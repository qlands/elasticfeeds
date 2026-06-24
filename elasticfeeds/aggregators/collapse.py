from .base import BaseAggregator


class CollapseAggregator(BaseAggregator):
    """
    A chronological feed that collapses (de-duplicates) results so that only the most recent activity per group
    is returned. By default it collapses on ``object.id`` so a busy object does not flood the feed with repeated
    entries; set ``collapse_field`` to ``actor.id`` to instead show the latest activity per actor.

    Uses ElasticSearch field collapsing, so ``from``/``size`` pagination still works over the collapsed results.
    """

    def __init__(self, actor_id, collapse_field="object.id"):
        """
        :param actor_id: The actor ID that will be used to query for activity feeds
        :param collapse_field: The keyword field to collapse on. "object.id" by default; "actor.id" is also useful.
        """
        BaseAggregator.__init__(self, actor_id)
        self.collapse_field = collapse_field

    def set_aggregation_section(self):
        self.query_dict["size"] = self.result_size
        self.query_dict["from"] = self.result_from
        self.query_dict["collapse"] = {"field": self.collapse_field}

    def get_feeds(self):
        """
        Construct an array with a single (most recent) activity per collapsed group, ordered by published
        datetime. Each element is an activity with the usual shape.

        :return: Dict array
        """
        result = []
        if self.es_feed_result["hits"]["total"]["value"] > 0:
            for hit in self.es_feed_result["hits"]["hits"]:
                result.append(hit["_source"])
        return result
