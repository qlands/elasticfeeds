from elasticfeeds.backends import get_backend
from elasticfeeds.exceptions import (
    LinkObjectError,
    LinkExistError,
    ActivityObjectError,
    AggregatorObjectError,
    MaxLinkError,
    LinkNotExistError,
    ElasticFeedConnectionError,
)
from elasticfeeds.network import Link, LinkedActivity
from elasticfeeds.activity import Activity
from elasticfeeds.aggregators import BaseAggregator
import uuid
import datetime

__all__ = ["Manager"]


def _get_feed_index_definition(number_of_shards, number_of_replicas):
    """
    Constructs the Feed index with a given number of shards and replicas. Feeds are stored in an atomic form and
       are based as much as possible on http://activitystrea.ms/

    :param number_of_shards: Number of shards for the feeds index.
    :param number_of_replicas: Number of replicas for the feeds index.

    The index has the following parts:

        published: Date when the feed was published. Stored in ISO 8601 format.
                   See https://docs.python.org/3.6/library/datetime.html#datetime.date.isoformat for more info.
        published_date: Date section of the published date. YYY-MM-DD. E.g., 2002-12-04
        published_time: Time section of the published date. HH:MM:SS. E.g., 13:00:23

        type: Single word in infinitive. Also know as "verb", it describes some form of action that may happen,
              is currently happening, or has already happened.
              See https://www.w3.org/TR/activitystreams-vocabulary/#dfn-activity for more info.

        actor: Describes the entity that is performing the activity.
               See https://www.w3.org/TR/activitystreams-vocabulary/#dfn-actor for more info.
        actor.id: The unique id of the actor. Only one ID is accepted.
        actor.type: Single word. The type of actor performing the activity. E.g., Person, User, Member.
                    See https://www.w3.org/TR/activitystreams-vocabulary/#actor-types for more info.
        actor.extra: Use this field to store extra information at actor level.
                     IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                     operations on it thus it cannot be used to order, aggregate, or filter query results.

        object: Describes an object of any kind linked to the action itself.
                See https://www.w3.org/TR/activitystreams-vocabulary/#dfn-object for more info.
        object.id: Single ID. The unique id of the object
        object.type: Single word. Provides some degree of specificity to the object. E.g., Document, Project, Form.
                     See https://www.w3.org/TR/activitystreams-vocabulary/#object-types for more info
        object.extra: Use this field to store extra information at object level.
                     IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                     operations on it thus it cannot be used to order, aggregate, or filter query results.

        origin [optional]: The origin is applicable to any type of activity for which the English preposition "from"
                           can be considered applicable in the sense of identifying the origin, source or provenance of
                           the activity's object. See https://www.w3.org/TR/activitystreams-vocabulary/#origin-target
                           for more information
        origin.id: The unique ID the origin. Only one ID is accepted.
        origin.type: Single word. Provides some degree of specificity to the origin. E.g., Collection
        origin.extra: Use this field to store extra information at origin level.
                      IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.

        target [optional]: The target is applicable to any type of activity for which the English preposition
                           "to" can be considered applicable in the sense of identifying the indirect object or
                           destination of the activity's object.
                           See https://www.w3.org/TR/activitystreams-vocabulary/#origin-target for more information
        target.id: The unique ID the target. Only one ID is accepted.
        target.type: Single word. Provides some degree of specificity to the target. E.g., Collection
        target.extra: Use this field to store extra information at target level.
                      IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.
        extra: Use this field to store extra information at activity level.
               IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
               operations on it thus it cannot be used to order, aggregate, or filter query results.

    :return: Dict.
    """
    # noinspection SpellCheckingInspection
    _json = {
        "settings": {
            "index": {
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas,
            }
        },
        "mappings": {
            "properties": {
                "published": {"type": "date"},
                "published_date": {"type": "date", "format": "yyyy-MM-dd"},
                "published_time": {"type": "date", "format": "HH:mm:ss"},
                "published_year": {"type": "integer"},
                "published_month": {"type": "integer"},
                "feed_id": {"type": "keyword"},
                "type": {"type": "keyword"},
                "actor": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "extra": {"type": "object", "enabled": "false"},
                    }
                },
                "object": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "extra": {"type": "object", "enabled": "false"},
                    }
                },
                "origin": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "extra": {"type": "object", "enabled": "false"},
                    }
                },
                "target": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "extra": {"type": "object", "enabled": "false"},
                    }
                },
                "extra": {"type": "object", "enabled": "false"},
            }
        },
    }
    return _json


def _get_network_index_definition(number_of_shards, number_of_replicas):
    """
    Constructs the Network index with a given number of shards and replicas.
    Each connection is stored as individual ES documents
    :param number_of_shards: Number of shards for the network index.
    :param number_of_replicas: Number of replicas for the network index.

    The index has the following parts:
         linked: Date when the link was made. Stored in ISO 8601 format.
                See https://docs.python.org/3.6/library/datetime.html#datetime.date.isoformat for more info.
         actor_id: Single word. The actor who's connection is being declared. For example if the actor "mark" is
                                following two people then "mark" would appear twice, one per connection.
         link_type: Single word in infinitive. The kind of link being declared. For example: Follow, Watch

         linked_activity: Linked activity to this link in the network
         linked_activity.activity_class: Single word. The type of activities that are being followed and watched.
                                         This must be either "actor" or "object"
         linked_activity.type: Single word. The type of feed component that is being followed or watched. For example
                               if the class is "actor" then it's type could be "Person", "User" or "Member".
                               If the class is "object" then its type could be "Document", or "Project".
         linked_activity.id: Single ID. The ID that is being followed or watched.

         link_weight: Numeric. Accept decimals. The wight of the connection. For example, if Mark follows Jane and
                      Katie depending on their interaction in social platform the connection between Mark and Jane
                      could be twice as strong as Mark and Katie, thus Mark and Katie will have a weight of 1 while
                      Mark and Jane will have a weight of 2. By default each connection has a weight of 1.
         extra: Use this field to store extra information at link level.
                IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                operations on it thus it cannot be used to order, aggregate, or filter query results.

    :return: A JSON object with the definition of the Network index.
    """
    _json = {
        "settings": {
            "index": {
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas,
            }
        },
        "mappings": {
            "properties": {
                "linked": {"type": "date"},
                "actor_id": {"type": "keyword"},
                "link_type": {"type": "keyword"},
                "linked_activity": {
                    "properties": {
                        "activity_class": {"type": "keyword"},
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                    }
                },
                "link_weight": {"type": "float"},
                "extra": {"type": "object", "enabled": "false"},
            }
        },
    }
    return _json


class Manager(object):
    """
    The Manager class handles all activity feed operations.

    By default it talks to ElasticSearch. Pass ``backend="opensearch"`` to use OpenSearch instead (requires
    the ``opensearch-py`` package), or inject a pre-built client via ``connection`` (useful for AWS Lambda or
    custom TLS/auth). ElasticSearch behaviour is unchanged regardless of these additions.
    """

    def create_connection(self):
        """
        Creates a connection to the configured backend and pings it.
        :return: A tested (pinged) client, or None if the ping fails
        """
        if not isinstance(self.port, int):
            raise ValueError("Port must be an integer")
        if not isinstance(self.host, str):
            raise ValueError("Host must be string")
        if self.url_prefix is not None:
            if not isinstance(self.url_prefix, str):
                raise ValueError("URL prefix must be string")
        if not isinstance(self.use_ssl, bool):
            raise ValueError("Use SSL must be boolean")
        return self._backend.create_client(
            host=self.host,
            port=self.port,
            scheme=self.scheme,
            url_prefix=self.url_prefix,
            use_ssl=self.use_ssl,
            user_name=self.user_name,
            user_password=self.user_password,
            max_retries=100,
            request_timeout=800,
        )

    def __init__(
        self,
        feed_index="feeds",
        network_index="network",
        host="localhost",
        port=9200,
        user_name="elastic",
        user_password="",
        scheme="http",
        url_prefix=None,
        use_ssl=False,
        number_of_shards_in_feeds=5,
        number_of_replicas_in_feeds=1,
        number_of_shards_in_network=5,
        number_of_replicas_in_network=1,
        delete_feeds_if_exists=False,
        delete_network_if_exists=False,
        embedding_dims=None,
        embedding_similarity="cosine",
        max_link_size=1000,
        backend="elasticsearch",
        connection=None,
    ):
        """
        The constructor of the Manager. It creates the feeds and network indices if they don't exist. See
        https://www.elastic.co/guide/en/elasticsearch/reference/current/_basic_concepts.html#getting-started-shards-and-replicas
        for more information about shards and replicas
        :param feed_index: The name if the feed index. "feeds" by default
        :param network_index: The name of the network index. "network" by default
        :param host: Backend host name. "localhost" by default
        :param port: Backend port. 9200 by default
        :param url_prefix: URL prefix. None by default
        :param use_ssl: Use SSL to connect to the backend. False by default
        :param number_of_shards_in_feeds: Number of shards for the feeds index. 5 by default
        :param number_of_replicas_in_feeds: Number of replicas for the feeds index. 1 by default
        :param number_of_shards_in_network: Number of shards for the network index. 5 by default
        :param number_of_replicas_in_network: Number of replicas for the network index. 1 by default
        :param delete_feeds_if_exists: Delete the feeds index if already exist. False by default
        :param delete_network_if_exists: Delete the network index if already exist. False by default
        :param embedding_dims: Optional integer. When set, the feed index gets a vector "embedding" field of
                               this dimensionality, enabling the SemanticAggregator (kNN). None by default (no
                               vector field, fully backwards compatible).
        :param embedding_similarity: Similarity metric for the embedding field ("cosine", "dot_product",
                                     "l2_norm"). "cosine" by default. Only used when embedding_dims is set.
        :param max_link_size: Maximum number of links to fetch from an actor
        :param backend: Which backend to use: "elasticsearch" (default) or "opensearch".
        :param connection: Optional pre-built client to use instead of creating one (e.g. for AWS Lambda or
                           custom TLS/auth). When provided it must match ``backend``.
        """
        self.host = host
        self.port = port
        self.user_name = user_name
        self.user_password = user_password
        self.scheme = scheme
        self.url_prefix = url_prefix
        self.use_ssl = use_ssl
        self.feed_index = feed_index
        self.network_index = network_index
        self._max_link_size = max_link_size
        self.backend = backend
        self._backend = get_backend(backend)

        # A single, long-lived connection is created here and reused for every operation. The client maintains
        # its own connection pool and is safe to share, so re-creating it per call is wasteful. A pre-built
        # client can be injected via ``connection`` (e.g. for AWS Lambda or custom TLS/auth).
        if connection is not None:
            self._connection = connection
        else:
            self._connection = self.create_connection()
            if self._connection is None:
                raise ElasticFeedConnectionError()

        feed_definition = _get_feed_index_definition(
            number_of_shards_in_feeds, number_of_replicas_in_feeds
        )
        if embedding_dims is not None:
            self._backend.add_vector_field(
                feed_definition, "embedding", embedding_dims, embedding_similarity
            )
        self._ensure_index(feed_index, feed_definition, delete_feeds_if_exists)
        self._ensure_index(
            network_index,
            _get_network_index_definition(
                number_of_shards_in_network, number_of_replicas_in_network
            ),
            delete_network_if_exists,
        )

    def _ensure_index(self, index_name, definition, delete_if_exists):
        """
        Creates an index from its definition if it does not exist. If it exists and ``delete_if_exists`` is True
        the index is dropped and recreated.
        :param index_name: Name of the index
        :param definition: Dict with "settings" and "mappings" sections
        :param delete_if_exists: Whether to drop and recreate an existing index
        """
        if self._backend.index_exists(self._connection, index_name):
            if delete_if_exists:
                self._backend.delete_index(self._connection, index_name)
            else:
                return
        self._backend.create_index(self._connection, index_name, definition)

    @property
    def connection(self):
        """
        The shared backend connection (Elasticsearch or OpenSearch client) used by this manager.
        :return: The backend client
        """
        return self._connection

    @property
    def max_link_size(self):
        """
        Maximum number of links to return from an actor
        :return:
        """
        return self._max_link_size

    @max_link_size.setter
    def max_link_size(self, value):
        if not isinstance(value, int):
            raise MaxLinkError()
        self._max_link_size = value

    def delete_feeds_index(self):
        """
        Deletes the feed index
        :return: True if the index was deleted successfully
        """
        self._backend.delete_index(self._connection, self.feed_index)
        return True

    def delete_network_index(self):
        """
        Deleted the network index
        :return: True if the index was deleted successfully
        """
        self._backend.delete_index(self._connection, self.network_index)
        return True

    def link_network_exists(self, link_object):
        """
        Check whether a link object already exists in the network index
        :param link_object: The link object to check if exists
        :return: True if exists otherwise False
        """
        if not isinstance(link_object, Link):
            raise LinkObjectError()
        res = self._backend.search(
            self._connection, self.network_index, link_object.get_search_dict()
        )
        if res["hits"]["total"]["value"] > 0:
            return True
        return False

    def add_network_link(self, link_object):
        """
        Adds a link to the network index
        :param link_object: The Link object being added to the index
        :return: The unique ID give to the link
        """
        if not isinstance(link_object, Link):
            raise LinkObjectError()
        if not self.link_network_exists(link_object):
            unique_id = str(uuid.uuid4())
            self._backend.index_document(
                self._connection, self.network_index, unique_id, link_object.get_dict()
            )
            return unique_id
        else:
            raise LinkExistError()

    def remove_network_link(self, link_object):
        """
        Removes a link from the network
        :param link_object: The Link object being removed from the index.
        :return: Bool
        """
        if not isinstance(link_object, Link):
            raise LinkObjectError()
        if self.link_network_exists(link_object):
            self._backend.delete_by_query(
                self._connection, self.network_index, link_object.get_search_dict()
            )
            return True
        else:
            raise LinkNotExistError()

    def follow(
        self,
        actor_id,
        following,
        linked=None,
        activity_type="person",
    ):
        """
        A convenience function to declare a follow link
        :param actor_id:  Actor ID who's link is being declared in the network
        :param following: The person that is being followed
        :param linked: Datetime of the link. Defaults to the current date and time.
        :param activity_type: String. Single word. The type of feed component that is being followed or watched.
                              For example, if the class is "actor" then it's type could be "Person", "User" or "Member".
                              If the class is "object" then its type could be "Document", or "Project".
        :return: None
        """
        a_linked_activity = LinkedActivity(following, activity_type=activity_type)
        a_link = Link(actor_id, a_linked_activity, linked=linked)
        self.add_network_link(a_link)

    def un_follow(self, actor_id, following, activity_type="person"):
        """
        A convenience function to un-follow a person
        :param actor_id:  Actor ID who's link is being declared in the network
        :param following: The person that is being un-followed
        :param activity_type: String. Single word. Must match the ``activity_type`` used when following, otherwise
                              the link will not be found. "person" by default.
        :return: Bool
        """
        a_linked_activity = LinkedActivity(following, activity_type=activity_type)
        a_link = Link(actor_id, a_linked_activity)
        return self.remove_network_link(a_link)

    def watch(self, actor_id, watch_id, watch_type, linked=None):
        """
        A convenience function to declare a watch link
        :param actor_id: Actor ID who's link is being declared in the network
        :param watch_id: The object that is being watched
        :param watch_type: The object type that is being watched
        :param linked: Datetime of the link. Defaults to the current date and time.
        :return: None
        """
        a_linked_activity = LinkedActivity(watch_id, "object", watch_type)
        a_link = Link(actor_id, a_linked_activity, linked=linked, link_type="watch")
        self.add_network_link(a_link)

    def un_watch(self, actor_id, watch_id, watch_type):
        """
        A convenience function to un-watch an object
        :param actor_id: Actor ID who's link is being declared in the network
        :param watch_id: The object that is being un-watched
        :param watch_type: The object type that is being un-watched
        :return: Bool
        """
        a_linked_activity = LinkedActivity(watch_id, "object", watch_type)
        a_link = Link(actor_id, a_linked_activity, link_type="watch")
        return self.remove_network_link(a_link)

    def add_activity_feed(self, activity_object):
        """
        Adds an activity to the feed index
        :param activity_object: The activity object being added to the index
        :return: The unique ID given to the activity
        """
        if not isinstance(activity_object, Activity):
            raise ActivityObjectError()
        unique_id = str(uuid.uuid4())
        document = activity_object.get_dict()
        # Store the id inside the document too so it can be used as a stable tie-breaker for
        # cursor (search_after) pagination without relying on _id fielddata.
        document["feed_id"] = unique_id
        self._backend.index_document(
            self._connection, self.feed_index, unique_id, document
        )
        return unique_id

    def get_search_dict(self, actor_id):
        """
        Constructs a search that will be used to search for the network of actor_id
        :param actor_id: The actor to search for its network links
        :return: A dict that will be passed to the backend
        """
        _dict = {
            "size": self.max_link_size,
            "query": {"bool": {"must": {"term": {"actor_id": actor_id}}}},
            "sort": [{"linked": {"order": "desc"}}],
        }
        return _dict

    def get_network(self, actor_id):
        """
        Creates an array of the current network.
        :return: Dict array
        """
        result = []
        es_result = self._backend.search(
            self._connection, self.network_index, self.get_search_dict(actor_id)
        )
        if es_result["hits"]["total"]["value"] > 0:
            for hit in es_result["hits"]["hits"]:
                result.append(hit["_source"])
        return result

    def get_feeds(self, aggregator):
        """
        Return an array of feeds. The structure of the elements will depend of the aggregator
        :param aggregator: Aggregator class
        :return: Array of feeds or empty array of the actor_id does not have any network links
        """
        if not isinstance(aggregator, BaseAggregator):
            raise AggregatorObjectError()
        aggregator.connection = self._connection
        aggregator.feed_index = self.feed_index
        aggregator.backend = self._backend
        aggregator.network_array = self.get_network(aggregator.actor_id)
        aggregator.set_query_dict()
        if aggregator.query_dict is not None:
            aggregator.set_aggregation_section()
            aggregator.query_feeds()
            return aggregator.get_feeds()
        else:
            return []

    def get_activities(
        self,
        actor_id=None,
        actor_type=None,
        verb=None,
        object_id=None,
        object_type=None,
        target_id=None,
        target_type=None,
        since=None,
        size=100,
        result_from=0,
        order="desc",
    ):
        """
        Introspect the activity graph directly, independent of any actor's network. Returns the activities
        matching the given actor / verb / object / target constraints (all optional, combined with AND),
        ordered by published date. This is the building block for graph exploration / REST-style lookups such
        as "all activities by actor X" or "X did <verb> to <object>".

        Unlike get_feeds(), results are NOT restricted to a follower network.

        :param actor_id: Match activities whose actor has this id
        :param actor_type: Match activities whose actor has this type
        :param verb: Match activities of this type (verb)
        :param object_id: Match activities whose object has this id
        :param object_type: Match activities whose object has this type
        :param target_id: Match activities whose target has this id
        :param target_type: Match activities whose target has this type
        :param since: Only activities published on or after this datetime (or ISO string)
        :param size: Maximum number of activities to return. 100 by default
        :param result_from: Offset for pagination. 0 by default
        :param order: "desc" (default) or "asc" by published date
        :return: Dict array of matching activities
        """
        must = []
        for field, value in (
            ("actor.id", actor_id),
            ("actor.type", actor_type),
            ("type", verb),
            ("object.id", object_id),
            ("object.type", object_type),
            ("target.id", target_id),
            ("target.type", target_type),
        ):
            if value is not None:
                must.append({"term": {field: value}})
        if since is not None:
            if isinstance(since, datetime.datetime):
                since = since.isoformat()
            must.append({"range": {"published": {"gte": since}}})
        query = {"bool": {"must": must}} if must else {"match_all": {}}
        body = {
            "query": query,
            "sort": [{"published": {"order": order}}],
            "size": size,
            "from": result_from,
        }
        es_result = self._backend.search(self._connection, self.feed_index, body)
        return [hit["_source"] for hit in es_result["hits"]["hits"]]

    def execute_raw_network_query(self, query_dict):
        return self._backend.search(self._connection, self.network_index, query_dict)

    def execute_raw_feeds_query(self, query_dict):
        return self._backend.search(self._connection, self.feed_index, query_dict)
