"""
Backend adapters that isolate the differences between the Elasticsearch and OpenSearch clients.

Elasticsearch is the default and its behaviour is intentionally left byte-for-byte identical to the
single-backend implementation; OpenSearch support is purely additive. The two clients only diverge in a
handful of places:

* Building the connection (``basic_auth`` / ``request_timeout`` vs ``http_auth`` / ``timeout``).
* Writing documents and creating indices (typed ``document=`` / ``settings=`` / ``mappings=`` vs ``body=``).
* Vector search (``dense_vector`` + a top-level ``knn`` clause vs ``knn_vector`` + a ``knn`` query).

Everything else -- the activity/network query DSL produced by the aggregators -- is shared, so only these
adapters (and SemanticAggregator, which calls ``knn_search_body``) need to know which backend is in use.
"""

__all__ = ["get_backend", "BaseBackend", "ElasticsearchBackend", "OpenSearchBackend"]

# Map ElasticSearch dense_vector similarity names to OpenSearch knn_vector space types.
_OS_SPACE_TYPE = {
    "cosine": "cosinesimil",
    "l2_norm": "l2",
    "dot_product": "innerproduct",
}


class BaseBackend:
    """
    Operations shared by both clients. Both accept ``index=`` (keyword) for index management and ``body=``
    for search / delete_by_query, so those live here. Subclasses implement the operations that diverge.
    """

    name = None

    # --- connection -------------------------------------------------------
    def create_client(
        self,
        *,
        host,
        port,
        scheme,
        url_prefix,
        use_ssl,
        user_name,
        user_password,
        max_retries,
        request_timeout,
    ):
        raise NotImplementedError

    # --- index management (shared) ---------------------------------------
    def index_exists(self, client, index):
        return bool(client.indices.exists(index=index))

    def delete_index(self, client, index):
        client.indices.delete(index=index)

    def refresh(self, client, index):
        client.indices.refresh(index=index)

    # --- index management (divergent) ------------------------------------
    def create_index(self, client, index, definition):
        raise NotImplementedError

    def index_document(self, client, index, doc_id, document):
        raise NotImplementedError

    # --- search (shared: both clients accept body=) ----------------------
    def search(self, client, index, body):
        return client.search(index=index, body=body)

    def delete_by_query(self, client, index, body):
        client.delete_by_query(index=index, body=body)

    # --- vectors (divergent) ---------------------------------------------
    def add_vector_field(self, definition, field_name, dims, similarity):
        raise NotImplementedError

    def knn_search_body(
        self, *, field, query_vector, k, num_candidates, filter_clause, source_includes
    ):
        raise NotImplementedError


class ElasticsearchBackend(BaseBackend):
    """The default backend. These calls mirror the single-backend (1.1.0) implementation exactly."""

    name = "elasticsearch"

    def create_client(
        self,
        *,
        host,
        port,
        scheme,
        url_prefix,
        use_ssl,
        user_name,
        user_password,
        max_retries,
        request_timeout,
    ):
        from elasticsearch import Elasticsearch

        # SSL is derived from the scheme in the 8.x/9.x client; use_ssl just forces https.
        scheme = "https" if use_ssl else scheme
        node = {"host": host, "port": port, "scheme": scheme}
        if url_prefix is not None:
            node["path_prefix"] = url_prefix
        client = Elasticsearch(
            hosts=[node],
            basic_auth=(user_name, user_password),
            max_retries=max_retries,
            retry_on_timeout=True,
            request_timeout=request_timeout,
        )
        return client if client.ping() else None

    def create_index(self, client, index, definition):
        client.indices.create(
            index=index,
            settings=definition["settings"],
            mappings=definition["mappings"],
        )

    def index_document(self, client, index, doc_id, document):
        client.index(index=index, id=doc_id, document=document)

    def add_vector_field(self, definition, field_name, dims, similarity):
        definition["mappings"]["properties"][field_name] = {
            "type": "dense_vector",
            "dims": dims,
            "index": True,
            "similarity": similarity,
        }

    def knn_search_body(
        self, *, field, query_vector, k, num_candidates, filter_clause, source_includes
    ):
        knn = {
            "field": field,
            "query_vector": query_vector,
            "k": k,
            "num_candidates": num_candidates,
        }
        if filter_clause is not None:
            knn["filter"] = filter_clause
        return {"knn": knn, "size": k, "_source": {"includes": source_includes}}


class OpenSearchBackend(BaseBackend):
    """OpenSearch backend (opensearch-py). Uses the 7.x-style ``body=`` API and the k-NN plugin."""

    name = "opensearch"

    def create_client(
        self,
        *,
        host,
        port,
        scheme,
        url_prefix,
        use_ssl,
        user_name,
        user_password,
        max_retries,
        request_timeout,
    ):
        try:
            from opensearchpy import OpenSearch
        except ImportError as e:  # pragma: no cover - import guard
            raise ImportError(
                "opensearch-py is required for the OpenSearch backend. "
                "Install it with: pip install elasticfeeds[opensearch]"
            ) from e

        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(user_name, user_password),
            use_ssl=use_ssl or scheme == "https",
            url_prefix=url_prefix or "",
            max_retries=max_retries,
            retry_on_timeout=True,
            timeout=request_timeout,
        )
        return client if client.ping() else None

    def create_index(self, client, index, definition):
        client.indices.create(index=index, body=definition)

    def index_document(self, client, index, doc_id, document):
        client.index(index=index, id=doc_id, body=document)

    def add_vector_field(self, definition, field_name, dims, similarity):
        # OpenSearch needs the index-level knn flag plus a knn_vector field.
        definition["settings"]["index"]["knn"] = True
        definition["mappings"]["properties"][field_name] = {
            "type": "knn_vector",
            "dimension": dims,
            "method": {
                "name": "hnsw",
                "engine": "lucene",  # lucene engine supports filtered kNN without extra plugins
                "space_type": _OS_SPACE_TYPE.get(similarity, "cosinesimil"),
            },
        }

    def knn_search_body(
        self, *, field, query_vector, k, num_candidates, filter_clause, source_includes
    ):
        # OpenSearch ignores num_candidates (controlled by ef_search); k drives the search.
        knn = {"vector": query_vector, "k": k}
        if filter_clause is not None:
            knn["filter"] = filter_clause
        return {
            "size": k,
            "query": {"knn": {field: knn}},
            "_source": {"includes": source_includes},
        }


_BACKENDS = {
    "elasticsearch": ElasticsearchBackend,
    "opensearch": OpenSearchBackend,
}


def get_backend(name):
    """
    Return a backend adapter instance by name.
    :param name: "elasticsearch" (default) or "opensearch"
    :return: A BaseBackend subclass instance
    """
    try:
        return _BACKENDS[name]()
    except KeyError:
        raise ValueError(
            "Unknown backend '%s'. Choose from: %s" % (name, sorted(_BACKENDS))
        )
