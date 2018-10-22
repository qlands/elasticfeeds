__all__ = ['KeyWordError', 'ExtraTypeError', 'WeightTypeError', 'IDError', 'LinkedTypeError', 'LinkObjectError',
           'LinkExistError', 'ActorObjectError', 'ObjectObjectError', 'OriginObjectError', 'TargetObjectError',
           'PublishedTypeError', 'ActivityObjectError', 'LinkedActivityObjectError', 'MaxLinkError',
           'AggregatorObjectError', 'ActivityClassError', 'OrderError', 'SizeError', 'FromError']


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
        return 'Link must be of class Link'


class LinkExistError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether a link object already exists in network.
    """

    def __str__(self):
        return 'Link object already exists in network'


class ActorObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an actor object is class Actor.
    """

    def __str__(self):
        return 'Actor must be of class Actor'


class ObjectObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an object object is class Object.
    """

    def __str__(self):
        return 'Object must be of class Object'


class OriginObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an origin object is class Origin.
    """

    def __str__(self):
        return 'Origin must be of class Origin'


class TargetObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an origin object is class Target.
    """

    def __str__(self):
        return 'Target must be of class Target'


class PublishedTypeError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether published is datetime.
    """

    def __str__(self):
        return 'Published must be datetime'


class ActivityObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an activity object is class Activity.
    """

    def __str__(self):
        return 'Activity must be of class Activity'


class LinkedActivityObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an linked activity object is class LinkedActivity.
    """

    def __str__(self):
        return 'Linked activity must be of class LinkedActivity'


class MaxLinkError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether max_link_size is integer.
    """

    def __str__(self):
        return 'The maximum number of links must be integer'


class AggregatorObjectError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an aggregator object is class Aggregator.
    """

    def __str__(self):
        return 'Aggregator must be of class Aggregator'


class ActivityClassError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether an linked activity class is actor or object.
    """

    def __str__(self):
        return 'Linked activity must be either actor or object'


class OrderError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether the order is asc or desc.
    """

    def __str__(self):
        return 'Order must be asc or desc'


class SizeError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether the size is integer.
    """

    def __str__(self):
        return 'Size and Top Hits Size must be integer'


class FromError(ElasticFeedException):
    """
        Exception raised when ElasticFeeds checks whether the from is integer.
    """

    def __str__(self):
        return 'From must be integer'
