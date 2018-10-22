from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Target']


class Target(object):
    """
    This class represents a target. The target is applicable to any type of activity for which the English preposition
    "to" can be considered applicable in the sense of identifying the indirect object or destination of the activity's
    object. See https://www.w3.org/TR/activitystreams-vocabulary/#origin-target for more information
    """
    def __init__(self, target_id, target_type, extra=None):
        """
        Initializes the target
        :param target_id: String. The unique ID the target. Only one ID is accepted.
        :param target_type: String. Single word. Provides some degree of specificity to the target. E.g., Collection
        :param extra: Use this dict to store extra information at target level.
                      IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.
        """
        temp = target_id.split(" ")
        if len(temp) == 1:
            self._target_id = target_id
        else:
            raise IDError()
        if not target_type.isalpha():
            raise KeyWordError(target_type)
        self._target_type = target_type.lower()
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def target_id(self):
        """
        The unique ID the target. Only one ID is accepted.
        :return: String
        """
        return self._target_id

    @target_id.setter
    def target_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._target_id = value
        else:
            raise IDError()

    @property
    def target_type(self):
        """
        Single word. Provides some degree of specificity to the target. E.g., Collection
        :return: String
        """
        return self._target_type

    @target_type.setter
    def target_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._target_type = value.lower()

    @property
    def extra(self):
        """
        Use this dict to store extra information at target level.
        IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any operations on it thus
        it cannot be used to order, aggregate, or filter query results.
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
        Creates a dict based on the target definition
        :return: Dict
        """
        _dict = {"id": self.target_id, "type": self.target_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
