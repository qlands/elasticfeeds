from elasticfeeds.exceptions import IDError, OrderError, SizeError, FromError

__all__ = ["BaseAggregator"]


class BaseAggregator(object):
    """
    Base aggregator. Performs the basic operations of an aggregator. Sub-classes must implement how the aggregation
    works (set_aggregation_section) and how the results are returned (get_feeds).
    """

    def __init__(self, actor_id):
        """
        Initialize the base aggregator
        :param actor_id: The actor ID that will be used to query for activity feeds
        """
        temp = actor_id.split(" ")
        if len(temp) == 1:
            self._actor_id = actor_id
        else:
            raise IDError()

        self._connection = None
        self._feed_index = None
        self._network_array = []
        self.query_dict = (
            None  #: The query dict that ES will execute to fetch activity feeds
        )
        self.es_feed_result = (
            None  #: The fetched activity feeds by ES. Used by subclasses in get_feeds()
        )
        self._order = "desc"  #: Order is descending at start
        self._result_size = 10000  #: Result size is 10000 records at start
        self._result_from = 0  #: From is 0 at start
        self._top_hits_size = 100  #: Top hits size is 100 at start

    @property
    def result_from(self):
        """
        Result_from allows you to configure the offset from with position in the total hits you want to fetch. You can
        use it in combination with result_size to enable result pagination (if no aggregation is performed)
        :return: Integer
        """
        return self._result_from

    @result_from.setter
    def result_from(self, value):
        if not isinstance(value, int):
            raise FromError
        self._result_from = value

    @property
    def result_size(self):
        """
        Result_size allows you to configure the maximum amount of hits to be returned.
        :return: Integer
        """
        return self._result_size

    @result_size.setter
    def result_size(self, value):
        if not isinstance(value, int):
            raise SizeError
        self._result_size = value

    @property
    def top_hits_size(self):
        """
        In an aggregation top_hits_size allows you to configure the amount of hits per bucket
        :return: Integer
        """
        return self._top_hits_size

    @top_hits_size.setter
    def top_hits_size(self, value):
        if not isinstance(value, int):
            raise SizeError
        self._top_hits_size = value

    @property
    def actor_id(self):
        """
        The actor ID that will be used to query for activity feeds
        :return: String
        """
        return self._actor_id

    @actor_id.setter
    def actor_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._actor_id = value
        else:
            raise IDError()

    @property
    def connection(self):
        """
        The connection to ElasticSearch
        :return: ES connection
        """
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    @property
    def feed_index(self):
        """
        The name of the feed index
        :return: String
        """
        return self._feed_index

    @feed_index.setter
    def feed_index(self, value):
        self._feed_index = value

    @property
    def order(self):
        """
        Order allows you to set the order of the query result. Descending by default
        :return: String
        """
        return self._order

    @order.setter
    def order(self, value):
        if value == "asc" or value == "desc":
            self._order = value
        else:
            raise OrderError()

    @property
    def network_array(self):
        """
        An array of the network links by Actor ID.
        :return: Array
        """
        return self._network_array

    @network_array.setter
    def network_array(self, value):
        self._network_array = value

    def get_sort_array(self):
        result = [{"published": {"order": self.order}}]
        return result

    def set_query_dict(self):
        """
        Setup the query section of the ES dict that will search for activities in the feed index
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
                should.append(should_item)
        if len(should) > 0:
            self.query_dict = {
                "query": {"bool": {"should": should}},
                "sort": self.get_sort_array(),
            }
        else:
            self.query_dict = None

    def query_feeds(self):
        if self.connection is not None:
            es_result = self.connection.search(
                index=self.feed_index, body=self.query_dict
            )
            if es_result["hits"]["total"] > 0:
                self.es_feed_result = es_result

    def set_aggregation_section(self):
        """
        Reimplemented by subclasses, this function should set the 'aggs' section in self.query_dict by doing
        self.query_dict['aggs'] = {aggregation_dict}
        """
        raise NotImplementedError(
            "set_aggregation_section must be implemented in subclasses"
        )

    def get_feeds(self):
        """
        Reimplemented by subclasses, this function must return self.es_feed_result in a friendly way to the user
        :return: An array of feeds
        """
        raise NotImplementedError("get_feeds must be implemented in subclasses")
