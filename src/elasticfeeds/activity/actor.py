from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Actor']


class Actor(object):
    def __init__(self, actor_id, actor_type, extra=None):
        temp = actor_id.split(" ")
        if len(temp) == 1:
            self._actor_id = actor_id
        else:
            raise IDError()
        if not actor_type.isalpha():
            raise KeyWordError(actor_type)
        self._actor_type = actor_type
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

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
    def actor_type(self):
        return self._actor_type

    @actor_type.setter
    def actor_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._actor_type = value

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
        Creates a dict based on the actor definition
        :return: The actor as a dict
        """
        _dict = {"id": self.actor_id, "type": self.actor_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
