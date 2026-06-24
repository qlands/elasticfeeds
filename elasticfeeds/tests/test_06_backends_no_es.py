#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Server-free tests for the backend adapters and the get_activities graph helper.

These verify, without any running cluster, that the Elasticsearch and OpenSearch adapters emit the right
client calls / request bodies (their only points of divergence), and that the Manager routes through the
selected backend. A MagicMock stands in for the client.
"""

from unittest.mock import MagicMock

import pytest

from elasticfeeds.backends import (
    get_backend,
    ElasticsearchBackend,
    OpenSearchBackend,
)
from elasticfeeds.manager import Manager

# --------------------------------------------------------------------------- backend factory


def test_get_backend():
    assert isinstance(get_backend("elasticsearch"), ElasticsearchBackend)
    assert isinstance(get_backend("opensearch"), OpenSearchBackend)
    with pytest.raises(ValueError):
        get_backend("nope")


# --------------------------------------------------------------------------- I/O call shapes


def test_elasticsearch_backend_calls():
    b = ElasticsearchBackend()
    c = MagicMock()
    b.create_index(c, "f", {"settings": {"s": 1}, "mappings": {"m": 2}})
    c.indices.create.assert_called_once_with(
        index="f", settings={"s": 1}, mappings={"m": 2}
    )
    b.index_document(c, "f", "id1", {"a": 1})
    c.index.assert_called_once_with(index="f", id="id1", document={"a": 1})
    b.search(c, "f", {"q": 1})
    c.search.assert_called_once_with(index="f", body={"q": 1})
    b.delete_index(c, "f")
    c.indices.delete.assert_called_once_with(index="f")


def test_opensearch_backend_calls():
    b = OpenSearchBackend()
    c = MagicMock()
    defn = {"settings": {"index": {}}, "mappings": {"properties": {}}}
    b.create_index(c, "f", defn)
    c.indices.create.assert_called_once_with(index="f", body=defn)
    b.index_document(c, "f", "id1", {"a": 1})
    c.index.assert_called_once_with(index="f", id="id1", body={"a": 1})
    b.search(c, "f", {"q": 1})
    c.search.assert_called_once_with(index="f", body={"q": 1})


# --------------------------------------------------------------------------- vector field mapping


def test_elasticsearch_vector_field():
    defn = {"settings": {"index": {}}, "mappings": {"properties": {}}}
    ElasticsearchBackend().add_vector_field(defn, "embedding", 16, "cosine")
    assert defn["mappings"]["properties"]["embedding"] == {
        "type": "dense_vector",
        "dims": 16,
        "index": True,
        "similarity": "cosine",
    }
    assert "knn" not in defn["settings"]["index"]


def test_opensearch_vector_field():
    defn = {"settings": {"index": {}}, "mappings": {"properties": {}}}
    OpenSearchBackend().add_vector_field(defn, "embedding", 16, "cosine")
    assert defn["settings"]["index"]["knn"] is True
    field = defn["mappings"]["properties"]["embedding"]
    assert field["type"] == "knn_vector"
    assert field["dimension"] == 16
    assert field["method"]["name"] == "hnsw"
    assert field["method"]["engine"] == "lucene"
    assert field["method"]["space_type"] == "cosinesimil"


# --------------------------------------------------------------------------- kNN search body


def test_elasticsearch_knn_body():
    body = ElasticsearchBackend().knn_search_body(
        field="embedding",
        query_vector=[1, 2],
        k=5,
        num_candidates=50,
        filter_clause={"bool": {"x": 1}},
        source_includes=["actor"],
    )
    assert body["knn"]["field"] == "embedding"
    assert body["knn"]["query_vector"] == [1, 2]
    assert body["knn"]["k"] == 5
    assert body["knn"]["num_candidates"] == 50
    assert body["knn"]["filter"] == {"bool": {"x": 1}}
    assert body["size"] == 5
    assert body["_source"]["includes"] == ["actor"]


def test_opensearch_knn_body():
    body = OpenSearchBackend().knn_search_body(
        field="embedding",
        query_vector=[1, 2],
        k=5,
        num_candidates=50,
        filter_clause={"bool": {"x": 1}},
        source_includes=["actor"],
    )
    knn = body["query"]["knn"]["embedding"]
    assert knn["vector"] == [1, 2]
    assert knn["k"] == 5
    assert knn["filter"] == {"bool": {"x": 1}}
    assert "num_candidates" not in knn  # OpenSearch does not use num_candidates
    assert body["size"] == 5
    assert body["_source"]["includes"] == ["actor"]


# --------------------------------------------------------------------------- Manager routing + get_activities


def test_manager_uses_injected_connection_and_backend():
    client = MagicMock()
    # index_exists returns truthy MagicMock -> __init__ skips index creation, no live server needed
    manager = Manager(feed_index="f", network_index="n", connection=client)
    assert manager.backend == "elasticsearch"
    assert manager.connection is client


def test_get_activities_builds_filtered_query():
    client = MagicMock()
    client.search.return_value = {"hits": {"hits": [{"_source": {"type": "add"}}]}}
    manager = Manager(feed_index="f", network_index="n", connection=client)
    out = manager.get_activities(
        actor_id="carlos", verb="add", object_type="project", size=20, order="asc"
    )
    assert out == [{"type": "add"}]
    body = client.search.call_args.kwargs["body"]
    must = body["query"]["bool"]["must"]
    assert {"term": {"actor.id": "carlos"}} in must
    assert {"term": {"type": "add"}} in must
    assert {"term": {"object.type": "project"}} in must
    assert body["size"] == 20
    assert body["sort"] == [{"published": {"order": "asc"}}]


def test_get_activities_no_filters_is_match_all():
    client = MagicMock()
    client.search.return_value = {"hits": {"hits": []}}
    manager = Manager(feed_index="f", network_index="n", connection=client)
    assert manager.get_activities() == []
    body = client.search.call_args.kwargs["body"]
    assert body["query"] == {"match_all": {}}
