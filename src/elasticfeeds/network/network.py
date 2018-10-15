import datetime
from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, WeightTypeError, IDError, LinkedTypeError, \
    LinkedActivityObjectError
from .activity import LinkedActivity

__all__ = ['Link']


class Link(object):
    def __init__(self, actor_id, linked_activity, linked=datetime.datetime.now(), link_type='follow', link_weight=1,
                 extra=None):
        temp = actor_id.split(" ")
        if len(temp) == 1:
            self._actor_id = actor_id
        else:
            raise IDError()
        if not isinstance(linked, datetime.datetime):
            raise LinkedTypeError
        self._linked = linked
        if not link_type.isalpha():
            raise KeyWordError(link_type)
        self._link_type = link_type
        if not isinstance(linked_activity, LinkedActivity):
            raise LinkedActivityObjectError
        self._linked_activity = linked_activity
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
    def linked_activity(self):
        return self._linked_activity

    @linked_activity.setter
    def linked_activity(self, value):
        if not isinstance(value, LinkedActivity):
            raise LinkedActivityObjectError
        self._linked_activity = value

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

    def get_dict(self):
        _dict = {
            "linked": self._linked,
            "actor_id": self._actor_id,
            "link_type": self._link_type,
            "linked_activity": self.linked_activity.get_dict(),
            "link_weight": self._link_weight,
        }
        if self._extra is not None:
            _dict["extra"] = self._extra
        return _dict

    def get_search_dict(self):
        _dict = {
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
                                "linked_activity.class": self.linked_activity.activity_class
                            }
                        },
                        {
                            "term": {
                                "linked_activity.type": self.linked_activity.activity_type
                            }
                        },
                        {
                            "term": {
                                "linked_activity.id": self.linked_activity.activity_id
                            }
                        }
                    ]
                }
            }
        }
        return _dict
