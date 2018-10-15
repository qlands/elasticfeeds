from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Origin']


class Origin(object):
    def __init__(self, origin_id, origin_type, extra=None):
        temp = origin_id.split(" ")
        if len(temp) == 1:
            self._origin_id = origin_id
        else:
            raise IDError()
        if not origin_type.isalpha():
            raise KeyWordError(origin_type)
        self._origin_type = origin_type
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def origin_id(self):
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
        return self._origin_type

    @origin_type.setter
    def origin_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._origin_type = value

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
        Creates a dict based on the origin definition
        :return: The origin as a dict
        """
        _dict = {"id": self.origin_id, "type": self.origin_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
