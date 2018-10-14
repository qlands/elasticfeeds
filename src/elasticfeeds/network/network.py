import datetime
from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, WeightTypeError, IDError, LinkedTypeError

__all__ = ['Link']


class Link(object):
    def __init__(self, actor_id, feed_component_id, linked=datetime.datetime.now(), link_type='follow',
                 feed_component_class='actor', feed_component_type='person', link_weight=1, extra=None):
        temp = actor_id.split(" ")
        if len(temp) == 1:
            self._actor_id = actor_id
        else:
            raise IDError()
        temp = feed_component_id.split(" ")
        if len(temp) == 1:
            self._feed_component_id = feed_component_id
        else:
            raise IDError()
        if not isinstance(linked, datetime.datetime):
            raise LinkedTypeError
        self._linked = linked
        if not link_type.isalpha():
            raise KeyWordError(link_type)
        self._link_type = link_type
        if not feed_component_class.isalpha():
            raise KeyWordError(feed_component_class)
        self._feed_component_class = feed_component_class
        if not feed_component_type.isalpha():
            raise KeyWordError(feed_component_type)
        self._feed_component_type = feed_component_type
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra
        if isinstance(link_weight, int) or isinstance(link_weight, float):
            self._link_weight = link_weight
        else:
            raise WeightTypeError()

    @property
    def actor_id(self):
        return self._actor_id

    @actor_id.setter
    def actor_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._actor_id = value
        else:
            raise IDError()

    @property
    def feed_component_id(self):
        return self._feed_component_id

    @feed_component_id.setter
    def feed_component_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._feed_component_id = value
        else:
            raise IDError()

    @property
    def linked(self):
        return self._linked

    @linked.setter
    def linked(self, value):
        if not isinstance(value, datetime.datetime):
            raise LinkedTypeError
        self._linked = value

    @property
    def link_type(self):
        return self._link_type

    @link_type.setter
    def link_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._link_type = value

    @property
    def feed_component_class(self):
        return self._feed_component_class

    @feed_component_class.setter
    def feed_component_class(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._feed_component_class = value

    @property
    def feed_component_type(self):
        return self._feed_component_type

    @feed_component_type.setter
    def feed_component_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._feed_component_type = value

    @property
    def extra(self):
        return self._extra

    @extra.setter
    def extra(self, value):
        if value is not None:
            if not isinstance(value, dict):
                raise ExtraTypeError()
        self._extra = value

    @property
    def link_weight(self):
        return self._link_weight

    @link_weight.setter
    def link_weight(self, value):
        if isinstance(value, int) or isinstance(value, float):
            self._link_weight = value
        else:
            raise WeightTypeError()

    def network_link(self):
        _json = {
            "linked": self._linked,
            "actor_id": self._actor_id,
            "link_type": self._link_type,
            "feed_component_class": self._feed_component_class,
            "feed_component": {
                'id': self._feed_component_id,
                'type': self._feed_component_type
            },
            "link_weight": self._link_weight,
        }
        if self._extra is not None:
            _json["extra"] = self._extra
        return _json

    def search_for_link(self):
        _json = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "actor_id": self.actor_id
                            }
                        },
                        {
                            "term": {
                                "link_type": self.link_type
                            }
                        },
                        {
                            "term": {
                                "feed_component_class": self.feed_component_class
                            }
                        },
                        {
                            "term": {
                                "feed_component.type": self.feed_component_type
                            }
                        },
                        {
                            "term": {
                                "feed_component.id": self.feed_component_id
                            }
                        }
                    ]
                }
            }
        }
        return _json
