from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Object']


class Object(object):
    def __init__(self, object_id, object_type, extra=None):
        temp = object_id.split(" ")
        if len(temp) == 1:
            self._object_id = object_id
        else:
            raise IDError()
        if not object_type.isalpha():
            raise KeyWordError(object_type)
        self._object_type = object_type
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def object_id(self):
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
        return self._object_type

    @object_type.setter
    def object_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._object_type = value

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
        Creates a dict based on the object definition
        :return: The object as a dict
        """
        _dict = {"id": self.object_id, "type": self.object_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
