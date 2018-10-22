from .base import BaseAggregator
from dotmap import DotMap


class UnAggregated(BaseAggregator):
    """
    This aggregator returns activity feeds ordered by published date. No aggregation is performed however pagination
    is performed by ES
    """
    def set_aggregation_section(self):
        self.query_dict['size'] = self.result_size
        self.query_dict['from'] = self.result_from

    def get_feeds(self):
        result = []
        if self.es_feed_result['hits']['total'] > 0:
            for hit in self.es_feed_result['hits']['hits']:
                result.append(DotMap(hit['_source']))
            return result
        else:
            return []
