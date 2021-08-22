from .base import BaseAggregator


class RecentTypeAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same activity type (verb)
    """

    def set_aggregation_section(self):
        self.query_dict["size"] = 0
        self.query_dict["aggs"] = {
            "types": {
                "terms": {"field": "type", "order": {"max_date": "desc"}},
                "aggs": {
                    "max_date": {"max": {"script": "doc.published"}},
                    "top_type_hits": {
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
            }
        }

    def get_feeds(self):
        """
        Construct an array of activity feeds grouped by type and ordered by published datetime.
        Each activity type has the following keys
            type: Activity type
            activities: An array of the activity feeds ordered by published datetime. Each activity has the following
                        keys:
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
                hit_array = []
                for hit in activity_type["top_type_hits"]["hits"]["hits"]:
                    hit_array.append(hit["_source"])
                _dict["activities"] = hit_array
                result.append(_dict)
        return result
