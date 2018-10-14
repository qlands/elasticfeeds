from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
from elasticfeeds.exceptions import LinkObjectError, LinkExistError
from elasticfeeds.network import Link
import uuid
import pprint

__all__ = ['Manager']


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

        actor: Describes the entity that performing the activity..
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

        target [optional]: The target property is applicable to any type of activity for which the English preposition
                           "to" can be considered applicable in the sense of identifying the indirect object or
                           destination of the activity's object.
                           See https://www.w3.org/TR/activitystreams-vocabulary/#origin-target for more information
        target.id: The unique ID the target. Only one ID is accepted.
        target.type: Single word. Provides some degree of specificity to the target. E.g., Collection
        target.extra: Use this field to store extra information at target level.
                      IMPORTANT NOTE: This field is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.

    :return: A JSON object with the definition of the Feeds index.
    """
    # noinspection SpellCheckingInspection
    _json = {
        "settings": {
            "index": {
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas
            }
        },
        "mappings": {
            "activity": {
                "properties": {
                    "published": {
                        "type": "date"
                    },
                    "published_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "published_time": {
                        "type": "date",
                        "format": "HH:mm:ss"
                    },
                    "type": {
                        "type": "keyword"
                    },
                    "actor": {
                        "properties": {
                            "id": {
                                "type": "keyword"
                            },
                            "type": {
                                "type": "keyword"
                            },
                            "extra": {
                                "type": "object",
                                "enabled": "false"
                            }
                        }
                    },
                    "object": {
                        "properties": {
                            "id": {
                                "type": "keyword"
                            },
                            "type": {
                                "type": "keyword"
                            },
                            "extra": {
                                "type": "object",
                                "enabled": "false"
                            }
                        }
                    },
                    "origin": {
                        "properties": {
                            "id": {
                                "type": "keyword",
                            },
                            "type": {
                                "type": "keyword"
                            },
                            "extra": {
                                "type": "object",
                                "enabled": "false"
                            }
                        }
                    },
                    "target": {
                        "properties": {
                            "id": {
                                "type": "keyword",
                            },
                            "type": {
                                "type": "keyword"
                            },
                            "extra": {
                                "type": "object",
                                "enabled": "false"
                            }
                        }
                    },
                    "extra": {
                        "type": "object",
                        "enabled": "false"
                    }
                }
            }
        }
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
            feed_component: Single word. The feed component that are being followed and watched. This must be either
                            "actor" or "object"
            feed_component_type: Single word. The type of feed component that is being followed or watched. For example
                                 if the feed component is "actor" then it's type could be "Person", "User" or "Member".
                                 If the feed component is "object" then its type could be "Document", or "Project".
            feed_component_id: Single ID. The ID that is being followed or watched.
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
                "number_of_replicas": number_of_replicas
            }
        },
        "mappings": {
            "link": {
                "properties": {
                    "linked": {
                        "type": "date"
                    },
                    "actor_id": {
                        "type": "keyword"
                    },
                    "link_type": {
                        "type": "keyword"
                    },
                    "feed_component_class": {
                        "type": "keyword"
                    },
                    "feed_component": {
                        "properties": {
                            "id": {
                                "type": "keyword"
                            },
                            "type": {
                                "type": "keyword"
                            }
                        }
                    },
                    "link_weight": {
                        "type": "float"
                    },
                    "extra": {
                        "type": "object",
                        "enabled": "false"
                    }
                }
            }
        }
    }
    return _json


class Manager(object):
    def create_connection(self):
        """
        Creates a connection to ElasticSearch and pings it.
        :return: A tested (pinged) connection to ElasticSearch
        """
        if not isinstance(self.port, int):
            raise ValueError('Port must be an integer')
        if not isinstance(self.host, str):
            raise ValueError('Host must be string')
        if self.url_prefix is not None:
            if not isinstance(self.url_prefix, str):
                raise ValueError('URL prefix must be string')
        if not isinstance(self.use_ssl, bool):
            raise ValueError('Use SSL must be boolean')
        cnt_params = {'host': self.host, 'port': self.port}
        if self.url_prefix is not None:
            cnt_params["url_prefix"] = self.url_prefix
        if self.use_ssl:
            cnt_params["use_ssl"] = self.use_ssl
        connection = Elasticsearch([cnt_params], max_retries=1)
        if connection.ping():
            return connection
        else:
            return None

    def __init__(self, feed_index='feeds', network_index='network', host='localhost', port=9200, url_prefix=None,
                 use_ssl=False, number_of_shards_in_feeds=5, number_of_replicas_in_feeds=1,
                 number_of_shards_in_network=5, number_of_replicas_in_network=1, delete_feeds_if_exists=False,
                 delete_network_if_exists=False):
        """
        The constructor of the Manager. It creates the feeds and network indices if they don't exist. See
        https://www.elastic.co/guide/en/elasticsearch/reference/current/_basic_concepts.html#getting-started-shards-and-replicas
        for more information about shards and replicas
        :param feed_index: The name if the feed index. "feeds" by default
        :param network_index: The name of the network index. "network" by default
        :param host: ElasticSearch host name. "localhost" by default
        :param port: ElasticSearch port. 9200 by default
        :param url_prefix: URL prefix. None by default
        :param use_ssl: Use SSL to connect to ElasticSearch. False by default
        :param number_of_shards_in_feeds: Number of shards for the feeds index. 5 by default
        :param number_of_replicas_in_feeds: Number of replicas for the feeds index. 1 by default
        :param number_of_shards_in_network: Number of shards for the network index. 5 by default
        :param number_of_replicas_in_network: Number of replicas for the network index. 1 by default
        :param delete_feeds_if_exists: Delete the feeds index if already exist. False by default
        :param delete_network_if_exists: Delete the network index if already exist. False by default
        """
        self.host = host
        self.port = port
        self.url_prefix = url_prefix
        self.use_ssl = use_ssl
        self.feed_index = feed_index
        self.network_index = network_index

        connection = self.create_connection()
        if connection is not None:
            try:
                connection.indices.create(feed_index, body=_get_feed_index_definition(number_of_shards_in_feeds,
                                                                                      number_of_replicas_in_feeds))
            except RequestError as e:
                if e.status_code == 400:
                    if e.error.find('already_exists') >= 0:
                        if delete_feeds_if_exists:
                            self.delete_feeds_index()
                            connection.indices.create(feed_index,
                                                      body=_get_feed_index_definition(number_of_shards_in_feeds,
                                                                                      number_of_replicas_in_feeds))
                        else:
                            pass
                    else:
                        raise e
                else:
                    raise e
            try:
                connection.indices.create(network_index, body=_get_network_index_definition(
                    number_of_shards_in_network, number_of_replicas_in_network))
            except RequestError as e:
                if e.status_code == 400:
                    if e.error.find('already_exists') >= 0:
                        if delete_network_if_exists:
                            self.delete_network_index()
                            connection.indices.create(network_index,
                                                      body=_get_network_index_definition(number_of_shards_in_network,
                                                                                         number_of_replicas_in_network))
                        else:
                            pass
                    else:
                        raise e
                else:
                    raise e
        else:
            raise RequestError("Cannot connect to ElasticSearch")

    def delete_feeds_index(self):
        """
        Deletes the feed index
        :return: True if the index was deleted successfully
        """
        connection = self.create_connection()
        if connection is not None:
            connection.indices.delete(self.feed_index)
            return True
        return False

    def delete_network_index(self,):
        """
        Deleted the network index
        :return: True if the index was deleted successfully
        """
        connection = self.create_connection()
        if connection is not None:
            connection.indices.delete(self.network_index)
            return True
        return False

    def link_network_exists(self, link_object):
        if not isinstance(link_object, Link):
            raise LinkObjectError()
        connection = self.create_connection()
        if connection is not None:
            res = connection.search(index=self.network_index, body=link_object.search_for_link())
            if res['hits']['total'] > 0:
                return True
        else:
            raise RequestError("Cannot connect to ElasticSearch")
        return False

    def add_network_link(self, link_object):
        if not isinstance(link_object, Link):
            raise LinkObjectError()
        if not self.link_network_exists(link_object):
            connection = self.create_connection()
            if connection is not None:
                connection.index(index=self.network_index, doc_type='link', id=str(uuid.uuid4()),
                                 body=link_object.network_link())
            else:
                raise RequestError("Cannot connect to ElasticSearch")
        else:
            raise LinkExistError()

