from .base import BaseAggregator
import pprint


class DateWeightAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds based on the same date and ordered by the weight of the connection. The
    aggregator only return feeds with activity_class = 'actor'
    """

    def set_query_dict(self):
        """
        We overwrite this method so only feeds with activity_class = 'actor' are retrieved
        """
        should = []
        for link in self.network_array:
            since = link["linked"]
            linked_activity = link["linked_activity"]
            if linked_activity["activity_class"] == "actor":
                should_item = {
                    "bool": {
                        "must": [
                            {"term": {"actor.id": linked_activity["id"]}},
                            {"term": {"actor.type": linked_activity["type"]}},
                            {"range": {"published": {"gte": since}}},
                        ]
                    }
                }
                should.append(should_item)
        if len(should) > 0:
            self.query_dict = {
                "query": {"bool": {"should": should}},
                "sort": self.get_sort_array(),
            }
        else:
            self.query_dict = None

    def set_aggregation_section(self):
        # Get the weights from the network
        weights = []
        for link in self.network_array:
            if link["linked_activity"]["activity_class"] == "actor":
                weights.append(
                    {"id": link["linked_activity"]["id"], "weight": link["link_weight"]}
                )
        self.query_dict["size"] = 0
        self.query_dict["aggs"] = {
            "dates": {
                "terms": {"field": "published_date"},
                "aggs": {
                    "top_date_hits": {
                        "top_hits": {
                            "sort": {
                                "_script": {
                                    "type": "number",
                                    "script": {
                                        "lang": "painless",
                                        "source": "def weight = 1; for (int i = 0; i < params.weights.length; ++i) { if (params.weights[i].id == doc['actor.id'].value) return params.weights[i].weight; } return weight;",
                                        "params": {"weights": weights},
                                    },
                                    "order": "desc",
                                }
                            },
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
                    }
                },
            }
        }

    def get_feeds(self):
        """
        Construct an array of activity feeds grouped by date. Each date has the following keys
            date: The date of feed
            activities: An array of the activity feeds ordered by weight. Each activity has the
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
        if self.es_feed_result["hits"]["total"] > 0:
            for a_date in self.es_feed_result["aggregations"]["dates"]["buckets"]:
                _dict = {"date": a_date["key_as_string"]}
                hit_array = []
                for hit in a_date["top_date_hits"]["hits"]["hits"]:
                    hit_array.append(hit["_source"])
                _dict["activities"] = hit_array
                result.append(_dict)
        return result
