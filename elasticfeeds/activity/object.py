from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ["Object"]


class Object(object):
    """
    This class represents the entity that is performing the activity.
    See https://www.w3.org/TR/activitystreams-vocabulary/#dfn-actor for more info.
    """

    def __init__(self, object_id, object_type, extra=None):
        """
        Initializes the Object
        :param object_id: String. Single ID. The unique id of the object.
        :param object_type: String. Single word. Provides some degree of specificity to the object. E.g., Document,
                            Project, Form.
                            See https://www.w3.org/TR/activitystreams-vocabulary/#object-types for more info
        :param extra: Use this dict to store extra information at object level.
                      IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any
                      operations on it thus it cannot be used to order, aggregate, or filter query results.
        """
        temp = object_id.split(" ")
        if len(temp) == 1:
            self._object_id = object_id
        else:
            raise IDError()
        if not object_type.isalpha():
            raise KeyWordError(object_type)
        self._object_type = object_type.lower()
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def object_id(self):
        """
        Single ID. The unique id of the object.
        :return: String
        """
        return self._object_id

    @object_id.setter
    def object_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._object_id = value
        else:
            raise IDError()

    @property
    def object_type(self):
        """
        Single word. Provides some degree of specificity to the object. E.g., Document, Project, Form.
        See https://www.w3.org/TR/activitystreams-vocabulary/#object-types for more info
        :return: String
        """
        return self._object_type

    @object_type.setter
    def object_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._object_type = value.lower()

    @property
    def extra(self):
        """
        Use this dict to store extra information at object level.
        IMPORTANT NOTE: This dict is "non-analyzable" which means that ES does not perform any
        operations on it thus it cannot be used to order, aggregate, or filter query results.
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
        Creates a dict based on the object definition
        :return: Dict
        """
        _dict = {"id": self.object_id, "type": self.object_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
