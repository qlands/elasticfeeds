from elasticfeeds.exceptions import KeyWordError, ExtraTypeError, IDError

__all__ = ['Target']


class Target(object):
    def __init__(self, target_id, target_type, extra=None):
        temp = target_id.split(" ")
        if len(temp) == 1:
            self._target_id = target_id
        else:
            raise IDError()
        if not target_type.isalpha():
            raise KeyWordError(target_type)
        self._target_type = target_type
        if extra is not None:
            if not isinstance(extra, dict):
                raise ExtraTypeError()
        self._extra = extra

    @property
    def target_id(self):
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
        return self._target_type

    @target_type.setter
    def target_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._target_type = value

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
        Creates a dict based on the target definition
        :return: The target as a dict
        """
        _dict = {"id": self.target_id, "type": self.target_type}
        if self.extra is not None:
            _dict["extra"] = self.extra
        return _dict
