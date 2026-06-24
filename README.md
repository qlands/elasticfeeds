[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# ElasticFeeds

A Python library for **self-hosted activity & notification feeds** built on Elasticsearch, using
**fan-out-on-read** and **composable feed algorithms**.

ElasticFeeds stores activities once (no write amplification to followers) and *composes* each user's feed
at query time. You pick how a feed is shaped — chronologically, grouped, ranked, de-duplicated, or by
semantic similarity — by choosing an **aggregator**. All the Elasticsearch query and aggregation
complexity is hidden behind small Python classes that return plain dictionaries.

## Is this for you?

**Good fit:** you run (or are happy to run) Elasticsearch, and you want an embeddable activity log /
notification inbox / following feed inside your own app — without a third-party SaaS and without building a
full machine-learning ranking pipeline. This is the original use case it was designed for (a Pyramid/Flask
app such as [FormShare](https://github.com/qlands/FormShare)).

**Probably not a fit:** you need a fully managed consumer-scale social feed with learned "For You" ranking
and real-time delivery out of the box — look at hosted services (e.g. GetStream) or notification platforms
(e.g. Novu, Knock). ElasticFeeds gives you the storage, the fan-out-on-read model and pluggable
aggregators; ranking signals and delivery are yours to drive.

## Why fan-out-on-read?

Most feed frameworks fan out **on write**: when you post, a copy is pushed into every follower's feed.
That is expensive for high-fan-out accounts (imagine a celebrity with 100M+ followers). ElasticFeeds
instead stores each activity once and builds the feed **on read**, leaning on Elasticsearch's speed and
aggregations. Elasticsearch scales horizontally, so you can start with one node and add more on demand.

This approach shines when a user *follows* a bounded number of things (typical of B2B/SaaS and community
apps). For consumer-social-graph scale, a hybrid model is usually the right answer — see *Scaling notes*
below.

## Requirements

- Python 3.8+
- Elasticsearch 9.2.x (client `elasticsearch>=9.2,<10`)

## Installation

```sh
git clone https://github.com/qlands/elasticfeeds.git
cd elasticfeeds
pip install -e .
```

A single-node Elasticsearch 9.2.1 for local development / tests is provided:

```sh
export ES_PASS="my_es_password"        # the 'elastic' user password
cd elasticsearch_docker
docker compose up -d
```

To run the test suite (the live tests need a running cluster; there is also a server-free subset):

```sh
export ES_USER="elastic"
export ES_PASS="my_es_password"
pip install -e ".[testing]"
pytest                                  # all tests (needs Elasticsearch)
pytest -k no_es                         # server-free unit tests only
```

## Quickstart

```python
from elasticfeeds.manager import Manager

# Connect (creates the feeds + network indices if needed)
manager = Manager("feeds", "network", user_name="elastic", user_password="my_es_password")

# Build the network
manager.follow("carlos", "carlos")      # follow yourself -> notification feed
manager.follow("carlos", "mark")        # follow others   -> activity feed
manager.watch("carlos", "project_a", "project")   # watch an object

# Record activities
from elasticfeeds.activity import Actor, Object, Activity

actor = Actor("mark", "person")
obj = Object("project_a", "project")
manager.add_activity_feed(Activity("add", actor, obj))

# Read the feed by choosing an aggregator
from elasticfeeds.aggregators import UnAggregated, NotificationAggregator

print(manager.get_feeds(UnAggregated("carlos")))            # chronological
print(manager.get_feeds(NotificationAggregator("carlos")))  # collapsed notifications
```

## Aggregators

A feed is shaped by the aggregator you pass to `manager.get_feeds(...)`. All restrict results to the
actor's network and to activities published since each link was created.

| Aggregator | Shape of the feed |
|---|---|
| `UnAggregated` | Flat, reverse-chronological. `from`/`size` pagination. |
| `CursorAggregator` | Flat, reverse-chronological with `search_after` cursor pagination (no 10k limit). |
| `CollapseAggregator` | Reverse-chronological, **one most-recent activity per object** (or actor). |
| `NotificationAggregator` | Collapsed summaries: *"X, Y and N others &lt;verb&gt; &lt;object&gt;"*. |
| `DecayRankedAggregator` | Single **ranked** ("hot") feed: recency decay × connection weight. |
| `DateWeightAggregator` | Grouped by date, ordered within a day by connection weight. |
| `RecentTypeAggregator` | Grouped by activity type (verb). |
| `RecentTypeObjectAggregator` | Grouped by type, then object. |
| `RecentObjectTypeAggregator` | Grouped by object, then type. |
| `YearMonthAggregator` | Grouped by year → month. |
| `YearMonthTypeAggregator` | Grouped by year → month → type. |
| `SemanticAggregator` | Semantic / "more like this" via kNN vector search. |

Common knobs (on every aggregator): `order` (`"asc"`/`"desc"`), `result_size`, `result_from`,
`top_hits_size`.

### Notification feed

```python
from elasticfeeds.aggregators import NotificationAggregator

for n in manager.get_feeds(NotificationAggregator("carlos")):
    # {'object_id': 'project_a', 'type': 'add', 'actors': ['mark', 'jane'],
    #  'actor_count': 3, 'event_count': 5, 'latest': {...}}
    print(n["actors"][:2], f"and {n['actor_count'] - 2} others", n["type"], n["object_id"])
```

### Ranked ("hot") feed

```python
from elasticfeeds.aggregators import DecayRankedAggregator

# Score = Gaussian recency decay (half-weight after 7 days) × connection weight
feed = manager.get_feeds(DecayRankedAggregator("carlos", scale="7d", decay=0.5))
```

### Cursor (infinite scroll)

```python
from elasticfeeds.aggregators import CursorAggregator

page = manager.get_feeds(CursorAggregator("carlos"))          # first page
# page == {"activities": [...], "next_cursor": [...] or None}
if page["next_cursor"]:
    page2 = manager.get_feeds(CursorAggregator("carlos", search_after=page["next_cursor"]))
```

### Collapse (de-duplicate)

```python
from elasticfeeds.aggregators import CollapseAggregator

manager.get_feeds(CollapseAggregator("carlos"))                       # latest per object
manager.get_feeds(CollapseAggregator("carlos", collapse_field="actor.id"))  # latest per actor
```

### Semantic feed (kNN vector search)

ElasticFeeds is model-agnostic: **you** produce the vectors (with whatever embedding model you use) and
ElasticFeeds stores and searches them.

```python
# 1) Enable the vector field on the feed index (dimensionality of your model's output)
manager = Manager("feeds", "network", user_name="elastic", user_password="...",
                  embedding_dims=384)   # e.g. a 384-dim sentence-embedding model

# 2) Store activities with an embedding
activity = Activity("blog", Actor("mark", "person"), Object("post_1", "post"),
                    embedding=my_model.encode("a post about water systems"))
manager.add_activity_feed(activity)

# 3) Query by similarity to a vector (e.g. the user's interest profile or a seed item)
from elasticfeeds.aggregators import SemanticAggregator

query_vector = my_model.encode("water and sanitation")
feed = manager.get_feeds(SemanticAggregator("carlos", query_vector, k=10))
# restrict_to_network=False turns this into a global discovery feed
```

## Activities

Activities follow [activitystrea.ms](http://activitystrea.ms/) as closely as possible:

```python
Activity(
    activity_type,        # the verb, e.g. "add", "blog", "move" (alphabetic)
    activity_actor,       # Actor(id, type)
    activity_object,      # Object(id, type)
    published=None,       # datetime; defaults to now. Honoured (you can back-date)
    activity_origin=None, # Origin(id, type)  — optional
    activity_target=None, # Target(id, type)  — optional
    extra=None,           # dict; stored but non-analyzable
    embedding=None,       # list[float]; stored in the dense_vector field
)
```

`actor`, `object`, `origin` and `target` each carry an `extra` dict for non-indexed payload (titles,
URLs, etc.).

## Scaling notes

- **Read side:** the feed query contains one clause per followed entity (two per watched object). Very
  large *following* counts can approach Elasticsearch's `indices.query.bool.max_clause_count`; `max_link_size`
  (default 1000) caps how many network links are loaded. For consumer-scale graphs, consider a hybrid
  fan-out (write-fanout for normal accounts, read-fanout for high-fan-out ones).
- **Pagination:** `UnAggregated` uses `from`/`size` (bounded by `index.max_result_window`, 10000). Use
  `CursorAggregator` for unbounded infinite scroll.
- **Single node:** the default `number_of_replicas` is 1, which leaves a single-node cluster *yellow*
  (the replica can't be allocated). That's expected for local development.

## Collaborate

The way you aggregate feeds depends on how you want to present them to your users. The best way to
contribute is by sharing aggregator classes: fork the project, add an aggregator, and open a pull request.
Bug reports are very welcome too.
