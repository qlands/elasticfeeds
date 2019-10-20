from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ["Origin"]


class Origin(object):
    """
    This class represents an origin. The origin is applicable to any type of activity for which the English preposition
    "from" can be considered applicable in the sense of identifying the origin, source or provenance of the activity's
    object. See https://www.w3.org/TR/activitystreams-vocabulary/#origin-target for more information.
    """

    def __init__(self, origin_id, origin_type, extra=None):
        """
        Initializes the Origin
        :param origin_id: String. The unique ID the origin. Only one ID is accepted.
        :param origin_type: String. Single word. Provides some degree of specificity to the origin. E.g., Collection
        :param extra: Use this dict to store extra information at origin level.
                      IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.
        """
        temp = origin_id.split(" ")
        if len(temp) == 1:
            self._origin_id = origin_id
        else:
            raise IDError()
        if not origin_type.isalpha():
            raise KeyWordError(origin_type)
        self._origin_type = origin_type.lower()
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def origin_id(self):
        """
        The unique ID the origin. Only one ID is accepted.
        :return: String
        """
        return self._origin_id

    @origin_id.setter
    def origin_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._origin_id = value
        else:
            raise IDError()

    @property
    def origin_type(self):
        """
        Single word. Provides some degree of specificity to the origin. E.g., Collection
        :return: String
        """
        return self._origin_type

    @origin_type.setter
    def origin_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._origin_type = value.lower()

    @property
    def extra(self):
        """
        Use this dict to store extra information at origin level.
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
        Creates a dict based on the origin definition
        :return: Dict
        """
        _dict = {"id": self.origin_id, "type": self.origin_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
