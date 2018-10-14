__all__ = ['KeyWordError', 'ExtraTypeError', 'WeightTypeError', 'IDError', 'LinkedTypeError', 'LinkObjectError',
           'LinkExistError']


class ElasticFeedException(Exception):
    """
    Base class for all exceptions raised by this ElasticFeeds
    """


class KeyWordError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks keywords for special characters.
    """

    @property
    def keyword(self):
        """ A string error message. """
        return self.args[0]

    def __str__(self):
        return 'Keyword (%s) has invalid characters. Only alpha characters are allowed' % self.keyword


class ExtraTypeError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether extra is a dict.
    """

    def __str__(self):
        return 'Extra must be none or dictionary'


class WeightTypeError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether weight is integer or float.
    """

    def __str__(self):
        return 'Weight must be integer or float'


class LinkedTypeError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether linked is datetime.
    """

    def __str__(self):
        return 'Linked must be datetime'


class IDError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether IDs have space.
    """

    def __str__(self):
        return 'IDs cannot have spaces'


class LinkObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether a link object is class Link.
    """

    def __str__(self):
        return 'Link object must be of class Link'


class LinkExistError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether a link object already exists in network.
    """

    def __str__(self):
        return 'Link object already exists in network'
