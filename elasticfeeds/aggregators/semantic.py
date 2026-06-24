from .base import BaseAggregator
from ..exceptions import EmbeddingTypeError, SizeError


class SemanticAggregator(BaseAggregator):
    """
    Returns a semantic ("more like this" / "for you") feed using ElasticSearch kNN vector search over the
    ``embedding`` field of the feed index.

    You supply a ``query_vector`` (for example, an embedding of the user's interests or of a seed item, produced
    by your own model). The aggregator finds the activities whose stored embedding is nearest to it. By default the
    results are restricted to the actor's network (the same following rules as the other aggregators); set
    ``restrict_to_network=False`` for a global discovery feed.

    Requires the feed index to have been created with ``embedding_dims`` set on the Manager, and activities to have
    been stored with an ``embedding``.
    """

    def __init__(
        self,
        actor_id,
        query_vector,
        k=10,
        num_candidates=100,
        embedding_field="embedding",
        restrict_to_network=True,
    ):
        """
        :param actor_id: The actor ID whose network is used to restrict the search (when restrict_to_network=True)
        :param query_vector: List of numbers. The vector to find nearest activities to.
        :param k: Number of nearest neighbours to return.
        :param num_candidates: Number of candidates to consider per shard (higher = more accurate, slower).
        :param embedding_field: Name of the dense_vector field in the feed index. "embedding" by default.
        :param restrict_to_network: When True, only activities from the actor's network are eligible.
        """
        BaseAggregator.__init__(self, actor_id)
        if not isinstance(query_vector, (list, tuple)) or not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in query_vector
        ):
            raise EmbeddingTypeError()
        if not isinstance(k, int) or not isinstance(num_candidates, int):
            raise SizeError()
        self.query_vector = list(query_vector)
        self.k = k
        self.num_candidates = num_candidates
        self.embedding_field = embedding_field
        self.restrict_to_network = restrict_to_network

    #: Feed fields returned by a semantic search (never the large embedding vector itself).
    _SOURCE_INCLUDES = [
        "published",
        "type",
        "actor",
        "object",
        "origin",
        "target",
        "extra",
    ]

    def set_query_dict(self):
        """
        Builds a kNN search via the active backend. Elasticsearch and OpenSearch express kNN differently, so
        the backend produces the correct body. When restricting to the network, the network "should" clauses
        are used as a kNN filter so only eligible activities are considered.
        """
        filter_clause = None
        if self.restrict_to_network:
            should = self._network_should_clauses()
            if len(should) == 0:
                self.query_dict = None
                return
            filter_clause = {"bool": {"should": should, "minimum_should_match": 1}}
        self.query_dict = self.backend.knn_search_body(
            field=self.embedding_field,
            query_vector=self.query_vector,
            k=self.k,
            num_candidates=self.num_candidates,
            filter_clause=filter_clause,
            source_includes=self._SOURCE_INCLUDES,
        )

    def set_aggregation_section(self):
        # The backend already produced a complete search body (size + _source included).
        pass

    def get_feeds(self):
        """
        Construct a single array of activity feeds ordered by semantic similarity (nearest first). Each element is
        an activity with the usual shape (the embedding vector is omitted).

        :return: Dict array
        """
        result = []
        if self.es_feed_result["hits"]["total"]["value"] > 0:
            for hit in self.es_feed_result["hits"]["hits"]:
                result.append(hit["_source"])
        return result
