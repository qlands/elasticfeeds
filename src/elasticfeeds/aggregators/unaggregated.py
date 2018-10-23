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
        """
        Construct an array of the activity feeds ordered by published datetime. Each activity feed is accessible
        with dot:
            .published
            .published_date
            .published_time
            .type
            .extra

            .actor.id
            .actor.type
            .actor.extra

            .object.id
            .object.type
            .object.extra

            .origin.id
            .origin.type
            .origin.extra

            .target.id
            .target.type
            .target.extra

        :return: Array
        """
        result = []
        if self.es_feed_result['hits']['total'] > 0:
            for hit in self.es_feed_result['hits']['hits']:
                result.append(DotMap(hit['_source']))
            return result
        else:
            return []
