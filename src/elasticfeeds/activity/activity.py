from .actor import Actor
from .object import Object
from .origin import Origin
from .target import Target
from elasticfeeds.exceptions import ActorObjectError, ObjectObjectError, OriginObjectError, TargetObjectError, \
    ExtraTypeError, PublishedTypeError, KeyWordError
import datetime

__all__ = ['Activity']


class Activity(object):
    def __init__(self, activity_type, activity_actor, activity_object, published=datetime.datetime.now(),
                 activity_origin=None, activity_target=None, extra=None):
        if not isinstance(activity_actor, Actor):
            raise ActorObjectError()
        self._activity_actor = activity_actor
        if not isinstance(activity_object, Object):
            raise ObjectObjectError()
        self._activity_object = activity_object
        if activity_origin is not None:
            if not isinstance(activity_origin, Origin):
                raise OriginObjectError()
        self._activity_origin = activity_origin
        if activity_target is not None:
            if not isinstance(activity_target, Target):
                raise TargetObjectError()
        self._activity_target = activity_target
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra
        if not isinstance(published, datetime.datetime):
            raise PublishedTypeError()
        self._published = published
        if not activity_type.isalpha():
            raise KeyWordError(activity_type)
        self._activity_type = activity_type

    @property
    def activity_type(self):
        return self._activity_type

    @activity_type.setter
    def activity_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._activity_type = value

    @property
    def activity_actor(self):
        return self._activity_actor

    @activity_actor.setter
    def activity_actor(self, value):
        if not isinstance(value, Actor):
            raise ActorObjectError()
        self._activity_actor = value

    @property
    def activity_object(self):
        return self._activity_object

    @activity_object.setter
    def activity_object(self, value):
        if not isinstance(value, Object):
            raise ObjectObjectError()
        self._activity_object = value

    @property
    def published(self):
        return self._published

    @published.setter
    def published(self, value):
        if not isinstance(value, datetime.datetime):
            raise PublishedTypeError()
        self._published = value

    @property
    def activity_origin(self):
        return self._activity_origin

    @activity_origin.setter
    def activity_origin(self, value):
        if not isinstance(value, Origin):
            raise OriginObjectError()
        self._activity_origin = value

    @property
    def activity_target(self):
        return self._activity_target

    @activity_target.setter
    def activity_target(self, value):
        if not isinstance(value, Target):
            raise TargetObjectError()
        self._activity_target = value

    @property
    def extra(self):
        return self._extra

    @extra.setter
    def extra(self, value):
        if value is not None:
            if not isinstance(value, dict):
                raise ExtraTypeError()
        self._extra = value

    def get_dict(self):
        """
        Creates a dict based on the activity definition
        :return: The activity as a dict
        """
        iso_date = self.published.isoformat()
        array = iso_date.split("T")
        date = array[0]
        array = array[1].split(".")
        time = array[0]
        _dict = {
            "published": iso_date,
            "published_date": date,
            "published_time": time,
            "actor": self.activity_actor.get_dict(),
            "type": self.activity_type,
            "object": self.activity_object.get_dict()
        }
        if self.activity_origin is not None:
            _dict["origin"] = self.activity_origin.get_dict()
        if self.activity_target is not None:
            _dict["target"] = self.activity_target.get_dict()
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
