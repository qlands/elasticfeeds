from .base import BaseAggregator
from dotmap import DotMap


class RecentObjectTypeAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same object ID and activity type (verb)
    """

    def set_aggregation_section(self):
        self.query_dict['size'] = 0
        self.query_dict['aggs'] = {
            "objects": {
                "terms": {
                    "field": "object.id",
                    "order": {
                        "max_obj_date": "desc"
                    }
                },
                "aggs": {
                    "max_obj_date": {
                        "max": {
                            "script": "doc.published"
                        }
                    },
                    "types": {
                        "terms": {
                            "field": "type",
                            "order": {
                                "max_type_date": "desc"
                            }
                        },
                        "aggs": {
                            "max_type_date": {
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
            }
        }

    def get_feeds(self):
        """
        Construct an array of the activity feeds grouped by object ID, activity type and ordered by published datetime.
        Each group is accessible with dot:
            .id: The ID of the object group
            .types: An array of each activity type. Each type is also accessible with dot
                .type: Activity type of the group
                .activities: An array of the activity feeds ordered by published datetime in the activity type group.
                             Each activity feed is also accessible with dot:
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
        # pprint.pprint(self.es_feed_result)
        if self.es_feed_result['hits']['total'] > 0:
            for an_object in self.es_feed_result['aggregations']['objects']['buckets']:
                _dict = {'id': an_object['key']}
                types_array = []
                for a_type in an_object['types']['buckets']:
                    _dict2 = {'type': a_type['key']}
                    hit_array = []
                    for hit in a_type['top_type_hits']['hits']['hits']:
                        hit_array.append(hit['_source'])
                    _dict2['activities'] = hit_array
                    types_array.append(_dict2)
                _dict['types'] = types_array
                result.append(DotMap(_dict))
        return result
