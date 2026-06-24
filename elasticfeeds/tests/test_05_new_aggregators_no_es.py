#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Server-free tests for the Path-2 aggregators and the opt-in embedding (vector) support.

These verify the ElasticSearch request bodies and the result-shaping logic without a live cluster, by feeding
the aggregators a fake ``network_array`` / ``es_feed_result``.
"""

import datetime

import pytest

from elasticfeeds.activity import Actor, Object, Activity
from elasticfeeds.exceptions import EmbeddingTypeError
from elasticfeeds.manager.manager import _get_feed_index_definition
from elasticfeeds.backends import ElasticsearchBackend
from elasticfeeds.aggregators import (
    NotificationAggregator,
    DecayRankedAggregator,
    CursorAggregator,
    CollapseAggregator,
    SemanticAggregator,
)


def _actor_network():
    return [
        {
            "linked": "2020-01-01T00:00:00",
            "actor_id": "carlos",
            "link_type": "follow",
            "linked_activity": {
                "activity_class": "actor",
                "id": "mark",
                "type": "person",
            },
            "link_weight": 2,
        }
    ]


# --------------------------------------------------------------------------- embedding / mapping


def test_feed_mapping_embedding_is_opt_in():
    plain = _get_feed_index_definition(5, 1)
    assert "embedding" not in plain["mappings"]["properties"]

    # The vector field is added by the backend adapter (ES dense_vector).
    ElasticsearchBackend().add_vector_field(plain, "embedding", 8, "cosine")
    field = plain["mappings"]["properties"]["embedding"]
    assert field["type"] == "dense_vector"
    assert field["dims"] == 8
    assert field["index"] is True
    assert field["similarity"] == "cosine"


def test_activity_embedding_serialized_and_validated():
    activity = Activity(
        "add",
        Actor("carlos", "person"),
        Object("p1", "project"),
        embedding=[0.1, 0.2, 0.3],
    )
    assert activity.get_dict()["embedding"] == [0.1, 0.2, 0.3]

    # no embedding -> key absent
    plain = Activity("add", Actor("carlos", "person"), Object("p1", "project"))
    assert "embedding" not in plain.get_dict()

    with pytest.raises(EmbeddingTypeError):
        Activity(
            "add", Actor("carlos", "person"), Object("p1", "project"), embedding="nope"
        )
    with pytest.raises(EmbeddingTypeError):
        Activity(
            "add",
            Actor("carlos", "person"),
            Object("p1", "project"),
            embedding=[1, "x"],
        )


# --------------------------------------------------------------------------- notification


def test_notification_aggregation_and_shaping():
    aggregator = NotificationAggregator("carlos")
    aggregator.network_array = _actor_network()
    aggregator.set_query_dict()
    aggregator.set_aggregation_section()
    assert aggregator.query_dict["size"] == 0
    assert "objects" in aggregator.query_dict["aggs"]

    aggregator.es_feed_result = {
        "hits": {"total": {"value": 3}},
        "aggregations": {
            "objects": {
                "buckets": [
                    {
                        "key": "proj_a",
                        "types": {
                            "buckets": [
                                {
                                    "key": "add",
                                    "actors": {
                                        "buckets": [{"key": "carlos"}, {"key": "mark"}]
                                    },
                                    "actor_count": {"value": 2},
                                    "event_count": {"value": 3},
                                    "latest": {
                                        "hits": {"hits": [{"_source": {"type": "add"}}]}
                                    },
                                }
                            ]
                        },
                    }
                ]
            }
        },
    }
    feeds = aggregator.get_feeds()
    assert feeds == [
        {
            "object_id": "proj_a",
            "type": "add",
            "actors": ["carlos", "mark"],
            "actor_count": 2,
            "event_count": 3,
            "latest": {"type": "add"},
        }
    ]


# --------------------------------------------------------------------------- decay-ranked


def test_decay_ranked_wraps_function_score():
    aggregator = DecayRankedAggregator("carlos", scale="3d", decay=0.4)
    aggregator.network_array = _actor_network()
    aggregator.set_query_dict()
    aggregator.set_aggregation_section()
    function_score = aggregator.query_dict["query"]["function_score"]
    # the network bool/should query is preserved inside the function_score
    assert "bool" in function_score["query"]
    kinds = [list(f.keys())[0] for f in function_score["functions"]]
    assert "gauss" in kinds and "script_score" in kinds
    # weight param carried the connection weight from the network
    script_fn = [f for f in function_score["functions"] if "script_score" in f][0]
    assert script_fn["script_score"]["script"]["params"]["weights"] == [
        {"id": "mark", "weight": 2}
    ]
    assert aggregator.query_dict["sort"] == [{"_score": {"order": "desc"}}]


# --------------------------------------------------------------------------- cursor


def test_cursor_sort_has_tiebreaker_and_search_after():
    aggregator = CursorAggregator("carlos", search_after=["2020-01-01T00:00:00", "id1"])
    aggregator.network_array = _actor_network()
    aggregator.set_query_dict()
    aggregator.set_aggregation_section()
    assert aggregator.query_dict["sort"] == [
        {"published": {"order": "desc"}},
        {"feed_id": {"order": "desc"}},
    ]
    assert aggregator.query_dict["search_after"] == ["2020-01-01T00:00:00", "id1"]
    assert aggregator.query_dict["size"] == 25  # default page size


def test_cursor_next_cursor_logic():
    aggregator = CursorAggregator("carlos")
    aggregator.result_size = 1
    aggregator.es_feed_result = {
        "hits": {"hits": [{"_source": {"a": 1}, "sort": [10, "id1"]}]}
    }
    page = aggregator.get_feeds()
    assert page["activities"] == [{"a": 1}]
    assert page["next_cursor"] == [10, "id1"]  # full page -> more may exist

    aggregator.result_size = 5  # partial page -> end reached
    page2 = aggregator.get_feeds()
    assert page2["next_cursor"] is None


# --------------------------------------------------------------------------- collapse


def test_collapse_adds_collapse_clause():
    aggregator = CollapseAggregator("carlos")
    aggregator.network_array = _actor_network()
    aggregator.set_query_dict()
    aggregator.set_aggregation_section()
    assert aggregator.query_dict["collapse"] == {"field": "object.id"}

    custom = CollapseAggregator("carlos", collapse_field="actor.id")
    custom.network_array = _actor_network()
    custom.set_query_dict()
    custom.set_aggregation_section()
    assert custom.query_dict["collapse"] == {"field": "actor.id"}


# --------------------------------------------------------------------------- semantic / kNN


def test_semantic_builds_knn_with_network_filter():
    aggregator = SemanticAggregator(
        "carlos", query_vector=[0.1, 0.2], k=5, num_candidates=50
    )
    aggregator.backend = ElasticsearchBackend()
    aggregator.network_array = _actor_network()
    aggregator.set_query_dict()
    aggregator.set_aggregation_section()
    knn = aggregator.query_dict["knn"]
    assert knn["field"] == "embedding"
    assert knn["query_vector"] == [0.1, 0.2]
    assert knn["k"] == 5 and knn["num_candidates"] == 50
    assert "bool" in knn["filter"]
    assert aggregator.query_dict["size"] == 5
    assert "embedding" not in aggregator.query_dict["_source"]["includes"]


def test_semantic_without_network_restriction_is_global():
    aggregator = SemanticAggregator(
        "carlos", query_vector=[0.1, 0.2], restrict_to_network=False
    )
    aggregator.backend = ElasticsearchBackend()
    aggregator.network_array = []
    aggregator.set_query_dict()
    assert aggregator.query_dict is not None
    assert "filter" not in aggregator.query_dict["knn"]


def test_semantic_restricted_empty_network_yields_no_query():
    aggregator = SemanticAggregator("carlos", query_vector=[0.1, 0.2])
    aggregator.network_array = []
    aggregator.set_query_dict()
    assert aggregator.query_dict is None


def test_semantic_rejects_bad_query_vector():
    with pytest.raises(EmbeddingTypeError):
        SemanticAggregator("carlos", query_vector="not-a-vector")
    with pytest.raises(EmbeddingTypeError):
        SemanticAggregator("carlos", query_vector=[1, "x"])
