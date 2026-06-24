=========
Changelog
=========

Version 1.2.0
=============

OpenSearch support (issue #5)
-----------------------------

- Added an optional OpenSearch backend. ElasticSearch remains the default and its behaviour is unchanged.
  Select the backend with ``Manager(backend="opensearch")`` and install ``pip install elasticfeeds[opensearch]``.
- The two clients are isolated behind ``elasticfeeds/backends.py`` adapters: connection building,
  document/index writes, and vector search (``dense_vector`` + top-level ``knn`` on ES vs ``knn_vector`` +
  a ``knn`` query on OpenSearch). The shared aggregator query DSL needs no per-backend handling.
- ``Manager`` accepts a pre-built ``connection`` to inject your own client (AWS Lambda, IAM, custom TLS).

New features
------------

- ``Manager.get_activities(...)`` -- introspect the activity graph directly by actor / verb / object /
  target (independent of any follower network). Library-level building block for graph exploration and
  REST-style lookups (issue #8).
- ``examples/demo.py`` -- a runnable, self-cleaning, end-to-end demonstration including the
  GetStream -> ElasticFeeds mapping and pagination patterns (issue #9).

Notes
-----

- Verified against live clusters -- ElasticSearch 9.2.1 and OpenSearch 2.19 (including the kNN / semantic
  path) -- in addition to the server-free test suite.

Version 1.1.0
=============

Compatibility & fixes
---------------------

- Fixed compatibility with the ElasticSearch 8.x/9.x Python client:

  - ``delete_feeds_index`` / ``delete_network_index`` now pass ``index`` as a keyword argument
    (positional was rejected by the new client).
  - Connection failures now raise the new ``ElasticFeedConnectionError`` instead of building a
    ``RequestError`` with a single string (which raised ``TypeError`` on the new client).
  - The connection no longer passes the legacy ``use_ssl`` / ``url_prefix`` host-dict keys (which raised
    ``ValueError``); SSL is derived from the scheme and ``url_prefix`` maps to ``path_prefix``.
  - Index creation uses ``settings=`` / ``mappings=`` and a clean ``exists`` check; writes use ``document=``.

- The ``Manager`` now creates a single, long-lived ElasticSearch connection and reuses it for every
  operation instead of building a new client per call.
- ``Activity`` now honours the ``published`` date provided to it (it was previously overwritten with
  ``now`` at serialization time, making back-dating / importing impossible).
- Replaced ``datetime.datetime.now()`` default arguments (evaluated once at import time) with ``None``
  defaults resolved per call, in ``Activity``, ``Link``, ``Manager.follow`` and ``Manager.watch``.
- ``Manager.un_follow`` gained an ``activity_type`` parameter so links created with a non-default type
  can be removed.
- Packaging: development/test tools moved out of ``install_requires`` into extras.
- Updated the development docker-compose to a single-node ElasticSearch 9.2.1 (security on, http).
- Added a server-free test suite that does not require a running ElasticSearch cluster.

New aggregators
---------------

- ``NotificationAggregator`` - collapses activities into notification summaries
  ("X, Y and N others did Z").
- ``DecayRankedAggregator`` - a ranked ("hot"/"top") feed using Gaussian recency decay combined with the
  connection weight.
- ``CursorAggregator`` - chronological feed with ``search_after`` (cursor) pagination, unbounded by the
  10000 ``from``/``size`` window.
- ``CollapseAggregator`` - de-duplicates the feed to the most recent activity per object (or actor).
- ``SemanticAggregator`` - semantic / "more like this" feed using kNN vector search.

New features
------------

- Opt-in dense vector support: set ``embedding_dims`` on the ``Manager`` to add an ``embedding``
  ``dense_vector`` field to the feed index, and pass ``embedding=[...]`` to ``Activity`` to store vectors
  for the ``SemanticAggregator``. Fully backwards compatible (off by default).
- Each stored activity now carries a ``feed_id`` keyword (equal to its document id) used as a stable
  tie-breaker for ``CursorAggregator`` pagination. New indices get it automatically.

Version 0.1
===========

- Initial release.
