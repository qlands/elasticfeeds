from .base import BaseAggregator
from dotmap import DotMap


class RecentTypeAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same activity type (verb)
    """

    def set_aggregation_section(self):
        self.query_dict['size'] = 0
        self.query_dict['aggs'] = {
            "types": {
                "terms": {
                    "field": "type",
                    "order": {
                        "max_date": "desc"
                    }
                },
                "aggs": {
                    "max_date": {
                        "max": {
                            "script": "doc.published"
                        }
                    },
                    "top_type_hits": {
                        "top_hits": {
                            "sort": [
                                {
                                    "published": {
                                        "order": "desc"
                                    }
                                }
                            ],
                            "_source": {
                                "includes": ["published", "actor", "object", "origin", "target", "extra"]
                            },
                            "size": self.top_hits_size
                        }
                    }
                }
            }
        }

    def get_feeds(self):
        """
        Construct an array of the activity feeds grouped by activity type and ordered by published datetime. Each group
        is accessible with dot:
            .type: Activity type of the group
            .activities: An array of the activity feeds ordered by published datetime in the group. Each activity feed
                         is also accessible with dot:
                .published
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
            for activity_type in self.es_feed_result['aggregations']['types']['buckets']:
                _dict = {'type': activity_type['key']}
                hit_array = []
                for hit in activity_type['top_type_hits']['hits']['hits']:
                    hit_array.append(hit['_source'])
                _dict['activities'] = hit_array
                result.append(DotMap(_dict))
        return result
