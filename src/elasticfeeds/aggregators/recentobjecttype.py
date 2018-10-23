from .base import BaseAggregator


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
        Construct an array of the grouped object ID and activity types ordered by published datetime. Each object ID has
        the following keys
            id: The ID of the object
            types: An array of activity types. Each activity type has the following keys:
                type: Activity type
                activities: An array of the activity feeds ordered by published datetime. Each activity has the
                            following keys:
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
                        extra (optional)
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
                result.append(_dict)
        return result
