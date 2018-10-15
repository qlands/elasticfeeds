from elasticfeeds.exceptions import KeyWordError, IDError

__all__ = ['LinkedActivity']


class LinkedActivity(object):
    def __init__(self, activity_id, activity_class='actor', activity_type='person'):
        temp = activity_id.split(" ")
        if len(temp) == 1:
            self._activity_id = activity_id
        else:
            raise IDError()
        if not activity_class.isalpha():
            raise KeyWordError(activity_class)
        self._activity_class = activity_class
        if not activity_type.isalpha():
            raise KeyWordError(activity_type)
        self._activity_type = activity_type


    @property
    def activity_id(self):
        return self._activity_id

    @activity_id.setter
    def activity_id(self, value):
        temp = value.split(" ")
        if len(temp) == 1:
            self._activity_id = value
        else:
            raise IDError()

    @property
    def activity_class(self):
        return self._activity_class

    @activity_class.setter
    def activity_class(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._activity_class = value

    @property
    def activity_type(self):
        return self._activity_type

    @activity_type.setter
    def activity_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._activity_type = value

    def get_dict(self):
        """
        Creates a dict based on the Network Activity definition
        :return: The Network Activity as a dict
        """
        _dict = {"class": self.activity_class, "id": self.activity_id, "type": self.activity_type}
        return _dict
