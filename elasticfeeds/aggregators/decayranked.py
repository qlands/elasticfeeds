from .base import BaseAggregator

#: Painless script that returns the weight of the connection to the activity's actor (1 by default).
_WEIGHT_SOURCE = (
    "double weight = 1; "
    "for (int i = 0; i < params.weights.length; ++i) { "
    "if (params.weights[i].id == doc['actor.id'].value) { return params.weights[i].weight; } "
    "} return weight;"
)


class DecayRankedAggregator(BaseAggregator):
    """
    Returns a single, relevance-ranked ("hot"/"top") feed instead of a chronological one.

    The score of each activity is the product of two signals:

    * a Gaussian recency decay on the published date (newer activities score higher), and
    * the weight of the connection to the activity's actor (stronger connections score higher).

    This turns the static, date-bucketed DateWeightAggregator into a proper ranked feed, which is closer to how
    modern feeds order content.
    """

    def __init__(self, actor_id, scale="7d", offset=None, decay=0.5):
        """
        :param actor_id: The actor ID that will be used to query for activity feeds
        :param scale: Distance from ``now`` at which the recency score drops to ``decay``. ES date math, e.g. "7d".
        :param offset: Optional. Activities newer than this keep the maximum recency score. ES date math, e.g.
                       "1h". Omitted by default (decay starts from now).
        :param decay: The recency score at one ``scale`` away from now (0 < decay < 1).
        """
        BaseAggregator.__init__(self, actor_id)
        self.scale = scale
        self.offset = offset
        self.decay = decay

    def set_aggregation_section(self):
        weights = self._actor_weights()
        base_query = self.query_dict["query"]
        decay_params = {"scale": self.scale, "decay": self.decay}
        if self.offset is not None:
            decay_params["offset"] = self.offset
        self.query_dict["query"] = {
            "function_score": {
                "query": base_query,
                "functions": [
                    {"gauss": {"published": decay_params}},
                    {
                        "script_score": {
                            "script": {
                                "lang": "painless",
                                "source": _WEIGHT_SOURCE,
                                "params": {"weights": weights},
                            }
                        }
                    },
                ],
                "score_mode": "multiply",
                "boost_mode": "replace",
            }
        }
        self.query_dict["sort"] = [{"_score": {"order": "desc"}}]
        self.query_dict["size"] = self.result_size
        self.query_dict["from"] = self.result_from

    def get_feeds(self):
        """
        Construct a single array of activity feeds ordered by their computed relevance score (descending). Each
        element is an activity with the usual shape (published, type, actor, object, origin, target, extra).

        :return: Dict array
        """
        result = []
        if self.es_feed_result["hits"]["total"]["value"] > 0:
            for hit in self.es_feed_result["hits"]["hits"]:
                result.append(hit["_source"])
        return result
