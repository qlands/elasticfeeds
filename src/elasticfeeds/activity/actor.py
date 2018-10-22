from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Actor']


class Actor(object):
    """
    This class represents the entity that is performing the activity.
    See https://www.w3.org/TR/activitystreams-vocabulary/#dfn-actor for more info.
    """
    def __init__(self, actor_id, actor_type, extra=None):
        """
        Initializes the Actor
        :param actor_id: String. The unique id of the actor. Only one ID is accepted.
        :param actor_type: String. Single word. The type of actor performing the activity. E.g., Person, User, Member.
                           See https://www.w3.org/TR/activitystreams-vocabulary/#actor-types for more info.
        :param extra: Use this dict to store extra information at actor level.
                      IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.
        """
        temp = actor_id.split(" ")
        if len(temp) == 1:
            self._actor_id = actor_id
        else:
            raise IDError()
        if not actor_type.isalpha():
            raise KeyWordError(actor_type)
        self._actor_type = actor_type.lower()
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def actor_id(self):
        """
        The unique id of the actor. Only one ID is accepted.
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
    def actor_type(self):
        """
        String. Single word. The type of actor performing the activity. E.g., Person, User, Member.
        See https://www.w3.org/TR/activitystreams-vocabulary/#actor-types for more info.
        :return: String
        """
        return self._actor_type

    @actor_type.setter
    def actor_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._actor_type = value.lower()

    @property
    def extra(self):
        """
        Use this dict to store extra information at actor level.
         IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any operations on it
         thus it cannot be used to order, aggregate, or filter query results.
        :return: Dict
        """
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
        :return: Dict
        """
        _dict = {"id": self.actor_id, "type": self.actor_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
