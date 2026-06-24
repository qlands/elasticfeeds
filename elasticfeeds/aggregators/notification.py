from .base import BaseAggregator


class NotificationAggregator(BaseAggregator):
    """
    Collapses many atomic activities into notification-style summaries, e.g.
    "carlos, mark and 3 others added project_a".

    Activities are grouped by object and then by type (verb). For each group the aggregator returns the distinct
    actors involved, how many of them there are, how many activities happened in total and the most recent
    activity. This is the typical shape needed to render a notifications inbox.
    """

    def set_aggregation_section(self):
        self.query_dict["size"] = 0
        self.query_dict["aggs"] = {
            "objects": {
                "terms": {
                    "field": "object.id",
                    "size": self.result_size,
                    "order": {"last_seen": "desc"},
                },
                "aggs": {
                    "last_seen": {"max": {"field": "published"}},
                    "types": {
                        "terms": {
                            "field": "type",
                            "order": {"type_last_seen": "desc"},
                        },
                        "aggs": {
                            "type_last_seen": {"max": {"field": "published"}},
                            "actors": {
                                "terms": {
                                    "field": "actor.id",
                                    "size": self.top_hits_size,
                                    "order": {"actor_last_seen": "desc"},
                                },
                                "aggs": {
                                    "actor_last_seen": {"max": {"field": "published"}}
                                },
                            },
                            "actor_count": {"cardinality": {"field": "actor.id"}},
                            "event_count": {"value_count": {"field": "actor.id"}},
                            "latest": {
                                "top_hits": {
                                    "size": 1,
                                    "sort": [{"published": {"order": "desc"}}],
                                    "_source": {
                                        "includes": [
                                            "published",
                                            "type",
                                            "actor",
                                            "object",
                                            "origin",
                                            "target",
                                            "extra",
                                        ]
                                    },
                                }
                            },
                        },
                    },
                },
            }
        }

    def get_feeds(self):
        """
        Construct an array of notifications ordered by recency. Each notification has the following keys:
            object_id: The ID of the object the activities are about
            type: The activity type (verb)
            actors: An array of the distinct actor IDs involved, most recent first (capped at top_hits_size)
            actor_count: The total number of distinct actors involved
            event_count: The total number of activities in this group
            latest: The most recent activity (same shape returned by the other aggregators)

        :return: Dict array
        """
        result = []
        if self.es_feed_result["hits"]["total"]["value"] > 0:
            for an_object in self.es_feed_result["aggregations"]["objects"]["buckets"]:
                for a_type in an_object["types"]["buckets"]:
                    actors = [b["key"] for b in a_type["actors"]["buckets"]]
                    latest_hits = a_type["latest"]["hits"]["hits"]
                    result.append(
                        {
                            "object_id": an_object["key"],
                            "type": a_type["key"],
                            "actors": actors,
                            "actor_count": a_type["actor_count"]["value"],
                            "event_count": a_type["event_count"]["value"],
                            "latest": (
                                latest_hits[0]["_source"] if latest_hits else None
                            ),
                        }
                    )
        return result
