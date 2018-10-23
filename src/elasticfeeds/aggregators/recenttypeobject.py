from .base import BaseAggregator
from dotmap import DotMap
import pprint


class RecentTypeObjectAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same activity type (verb) and same object ID
    """

    def set_aggregation_section(self):
        self.query_dict['size'] = 0
        self.query_dict['aggs'] = {
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
                            "top_obj_hits": {
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
        Construct an array of the activity feeds grouped by activity type, object ID and ordered by published datetime.
        Each group is accessible with dot:
            .type: Activity type of the group
            .ids: An array of each object ID. Each object ID is also accessible with dot
                .id: The ID of the object group
                .activities: An array of the activity feeds ordered by published datetime in the ID object group. Each
                             activity feed is also accessible with dot:
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
                id_array = []
                for an_object in activity_type['objects']['buckets']:
                    _dict2 = {'id': an_object['key']}
                    hit_array = []
                    for hit in an_object['top_obj_hits']['hits']['hits']:
                        hit_array.append(hit['_source'])
                    _dict2['activities'] = hit_array
                    id_array.append(_dict2)
                _dict['ids'] = id_array
                result.append(DotMap(_dict))
        return result
