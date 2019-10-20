from elasticfeeds.exceptions import KeyWordError, IDError, ActivityClassError

__all__ = ["LinkedActivity"]


class LinkedActivity(object):
    """
    This class represents a linked activity in the network of an actor
    """

    def __init__(self, activity_id, activity_class="actor", activity_type="person"):
        """
        Initializes the linked activity
        :param activity_id: String. The ID that is being followed or watched.
        :param activity_class: String. Single word. The type of activities that are being followed and watched.
                               This must be either "actor" or "object"
        :param activity_type: String. Single word. The type of feed component that is being followed or watched.
                              For example, if the class is "actor" then it's type could be "Person", "User" or "Member".
                              If the class is "object" then its type could be "Document", or "Project".
        """
        temp = activity_id.split(" ")
        if len(temp) == 1:
            self._activity_id = activity_id
        else:
            raise IDError()
        if not activity_class.isalpha():
            raise KeyWordError(activity_class)
        if activity_class == "actor" or activity_class == "object":
            self._activity_class = activity_class.lower()
        else:
            raise ActivityClassError
        if not activity_type.isalpha():
            raise KeyWordError(activity_type)
        self._activity_type = activity_type.lower()

    @property
    def activity_id(self):
        """
        The ID that is being followed or watched.
        :return: String
        """
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
        """
        Single word. The type of activities that are being followed and watched. This must be either "actor" or "object"
        :return:
        """
        return self._activity_class

    @activity_class.setter
    def activity_class(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        if value == "actor" or value == "object":
            self._activity_class = value.lower()
        else:
            raise ActivityClassError

    @property
    def activity_type(self):
        """
        The type of feed component that is being followed or watched.
        For example, if the class is "actor" then it's type could be "Person", "User" or "Member". If the class is
        "object" then its type could be "Document", or "Project".
        :return:
        """
        return self._activity_type

    @activity_type.setter
    def activity_type(self, value):
        if not value.isalpha():
            raise KeyWordError(value)
        self._activity_type = value.lower()

    def get_dict(self):
        """
        Creates a dict based on the Linked Activity definition
        :return: Dict
        """
        _dict = {
            "activity_class": self.activity_class,
            "id": self.activity_id,
            "type": self.activity_type,
        }
        return _dict
