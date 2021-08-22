from .base import BaseAggregator


class RecentTypeObjectAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same activity type (verb) and same object ID
    """

    def set_aggregation_section(self):
        self.query_dict["size"] = 0
        self.query_dict["aggs"] = {
            "types": {
                "terms": {"field": "type", "order": {"max_type_date": "desc"}},
                "aggs": {
                    "max_type_date": {"max": {"script": "doc.published"}},
                    "objects": {
                        "terms": {
                            "field": "object.id",
                            "order": {"max_obj_date": "desc"},
                        },
                        "aggs": {
                            "max_obj_date": {"max": {"script": "doc.published"}},
                            "top_obj_hits": {
                                "top_hits": {
                                    "sort": [{"published": {"order": "desc"}}],
                                    "_source": {
                                        "includes": [
                                            "published",
                                            "actor",
                                            "object",
                                            "origin",
                                            "target",
                                            "extra",
                                        ]
                                    },
                                    "size": self.top_hits_size,
                                }
                            },
                        },
                    },
                },
            }
        }

    def get_feeds(self):
        """
        Construct an array of feeds grouped by activity type and object ID, ordered by published datetime. Each
        activity type has the following keys:
            type: Activity type
            ids: An array of object IDs. Each ID has the following keys:
                id: The ID of the object
                activities: An array of the activity feeds ordered by published datetime. Each activity feed has the
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
        if self.es_feed_result["hits"]["total"]["value"] > 0:
            for activity_type in self.es_feed_result["aggregations"]["types"][
                "buckets"
            ]:
                _dict = {"type": activity_type["key"]}
                id_array = []
                for an_object in activity_type["objects"]["buckets"]:
                    _dict2 = {"id": an_object["key"]}
                    hit_array = []
                    for hit in an_object["top_obj_hits"]["hits"]["hits"]:
                        hit_array.append(hit["_source"])
                    _dict2["activities"] = hit_array
                    id_array.append(_dict2)
                _dict["ids"] = id_array
                result.append(_dict)
        return result
