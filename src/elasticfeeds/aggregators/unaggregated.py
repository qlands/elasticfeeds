from .base import BaseAggregator


class UnAggregated(BaseAggregator):
    """
    This aggregator returns activity feeds ordered by published date. No aggregation is performed however pagination
    is performed by ES
    """
    def set_aggregation_section(self):
        self.query_dict['size'] = self.result_size
        self.query_dict['from'] = self.result_from

    def get_feeds(self):
        """
        Construct an array of the activity feeds ordered by published datetime with the following keys:
            published
            type
            extra (optional)
            actor
                id
                type
                extra (optional)
            object
                id
                type
                extra
            origin (optional)
                id
                type
                extra (optional)
            target (optional)
                id
                type
                extra (optional)

        :return: Dict array
        """
        result = []
        if self.es_feed_result['hits']['total'] > 0:
            for hit in self.es_feed_result['hits']['hits']:
                result.append(hit['_source'])
            return result
        else:
            return []
