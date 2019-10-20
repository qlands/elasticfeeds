from .base import BaseAggregator
from ..exceptions import ElasticFeedException


class YearMonthTypeAggregator(BaseAggregator):
    """
    This aggregator returns activity feeds grouped by the same year, month and type (verb).
    """

    def __init__(self, actor_id, year=None):
        """
        We overwrite the constructor to be able to set an specific year
        :param actor_id: The actor ID that will be used to query for activity feeds
        :param year: The year to filter the query. If None then all years will be retrieved
        """
        BaseAggregator.__init__(self, actor_id)  # Call the parent constructor
        if year is not None:
            if not isinstance(year, int):
                raise ElasticFeedException("Year must be integer")
        self._year = year

    @property
    def year(self):
        """
        The year to filter the query
        :return: Integer
        """
        return self._year

    @year.setter
    def year(self, value):
        if not isinstance(value, int):
            raise ElasticFeedException("Year must be integer")
        self._year = value

    def set_query_dict(self):
        """
        We overwrite the query section to include the year
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
                if self.year is not None:
                    should_item["bool"]["must"].append(
                        {"term": {"published_year": self.year}}
                    )
                should.append(should_item)
            else:
                should_item = {
                    "bool": {
                        "must": [
                            {"term": {"object.id": linked_activity["id"]}},
                            {"term": {"object.type": linked_activity["type"]}},
                            {"range": {"published": {"gte": since}}},
                        ]
                    }
                }
                if self.year is not None:
                    should_item["bool"]["must"].append(
                        {"term": {"published_year": self.year}}
                    )
                should.append(should_item)
                should_item = {
                    "bool": {
                        "must": [
                            {"term": {"target.id": linked_activity["id"]}},
                            {"term": {"target.type": linked_activity["type"]}},
                            {"range": {"published": {"gte": since}}},
                        ]
                    }
                }
                if self.year is not None:
                    should_item["bool"]["must"].append(
                        {"term": {"published_year": self.year}}
                    )
                should.append(should_item)
        if len(should) > 0:
            self.query_dict = {
                "query": {"bool": {"should": should}},
                "sort": self.get_sort_array(),
            }
        else:
            self.query_dict = None

    def set_aggregation_section(self):
        self.query_dict["size"] = 0
        self.query_dict["aggs"] = {
            "years": {
                "terms": {
                    "field": "published_year",
                    "order": {"max_year_date": "desc"},
                },
                "aggs": {
                    "max_year_date": {"max": {"script": "doc.published"}},
                    "months": {
                        "terms": {
                            "field": "published_month",
                            "order": {"max_month_date": "desc"},
                        },
                        "aggs": {
                            "max_month_date": {"max": {"script": "doc.published"}},
                            "types": {
                                "terms": {
                                    "field": "type",
                                    "order": {"max_type_date": "desc"},
                                },
                                "aggs": {
                                    "max_type_date": {
                                        "max": {"script": "doc.published"}
                                    },
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
                            },
                        },
                    },
                },
            }
        }

    def get_feeds(self):
        """
        Construct an array of feeds grouped by year, month and type (verb). Each year has the following keys
            year: The year
            months: An array of months. Each month has the following keys:
                month: The month
                types: Array of activity types (verbs)
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
        if self.es_feed_result["hits"]["total"] > 0:
            for a_year in self.es_feed_result["aggregations"]["years"]["buckets"]:
                _year = {"year": a_year["key"]}
                month_array = []
                for a_month in a_year["months"]["buckets"]:
                    _month = {"month": a_month["key"]}
                    type_array = []
                    for a_type in a_month["types"]["buckets"]:
                        _type = {"type": a_type["key"]}
                        hit_array = []
                        for hit in a_type["top_type_hits"]["hits"]["hits"]:
                            hit_array.append(hit["_source"])
                        _type["activities"] = hit_array
                        type_array.append(_type)
                    _month["types"] = type_array
                    month_array.append(_month)
                _year["months"] = month_array
                result.append(_year)
        return result
