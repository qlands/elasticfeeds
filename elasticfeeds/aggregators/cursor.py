from .base import BaseAggregator


class CursorAggregator(BaseAggregator):
    """
    A chronological feed that paginates with ``search_after`` (cursor pagination) instead of ``from``/``size``.

    This supports unbounded, stable infinite-scroll: it is not limited by the ``index.max_result_window`` (10000
    by default) ceiling that ``from``-based pagination hits, and it does not skip or duplicate items when new
    activities arrive between page loads.

    ``result_size`` controls the page size (25 by default). A stable tie-breaker (``feed_id``) is appended to the
    sort so the cursor is deterministic; for very high write volumes consider a point-in-time search on top of
    this.
    """

    def __init__(self, actor_id, search_after=None):
        """
        :param actor_id: The actor ID that will be used to query for activity feeds
        :param search_after: The ``next_cursor`` returned by a previous call, or None for the first page.
        """
        BaseAggregator.__init__(self, actor_id)
        self._result_size = 25  #: Page size. Override via the result_size property.
        self._search_after = search_after

    @property
    def search_after(self):
        """
        The cursor (sort values of the last seen hit) to resume pagination from.
        :return: List or None
        """
        return self._search_after

    @search_after.setter
    def search_after(self, value):
        self._search_after = value

    def get_sort_array(self):
        return [
            {"published": {"order": self.order}},
            {"feed_id": {"order": self.order}},
        ]

    def set_aggregation_section(self):
        self.query_dict["size"] = self.result_size
        if self._search_after is not None:
            self.query_dict["search_after"] = self._search_after

    def get_feeds(self):
        """
        Construct one page of the chronological feed. Returns a dict with:
            activities: An array of activities (usual shape) for this page, ordered by published datetime
            next_cursor: The cursor to pass as ``search_after`` for the next page, or None when the end is reached

        :return: Dict
        """
        hits = self.es_feed_result["hits"]["hits"]
        activities = [hit["_source"] for hit in hits]
        next_cursor = (
            hits[-1]["sort"] if hits and len(hits) == self.result_size else None
        )
        return {"activities": activities, "next_cursor": next_cursor}
