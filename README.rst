.. image:: https://travis-ci.org/qlands/elasticfeeds.svg?branch=master
.. image:: https://codecov.io/gh/qlands/elasticfeeds/branch/master/graph/badge.svg

============
ElasticFeeds
============


A python library to manage notification and activity feeds using ElasticSearch as backend.


Description
===========

A few months ago, I started to work on a social media platform in Python with Pyramid and I had to get my hands into handling activity feeds. After searching the internet for possible Python frameworks, I realized that those well maintained (`Django Activity Stream <https://django-activity-stream.readthedocs.io/en/latest/index.html>`_ and `Stream Framework <https://github.com/tschellenbach/Stream-Framework>`_) were very oriented to Django (which I hate). Furthermore, both frameworks use asynchronous tasks to perform “fan-out on write” operations which I think is an overkill if you consider a user like @katyperry with 107,805,373 followers.

Later, I encounter a post in StackOverflow on "`Creating a SOLR index for activity stream or newsfeed <https://stackoverflow.com/questions/44468264/creating-a-solr-index-for-activity-stream-or-newsfeed#comment91900926_44468264>`_" which attached a presentation on "`A news feed with ElasticSearch <http://www.quentinsuire.com/presentations/a-news-feed-with-elasticsearch/#/>`_". The authors explain how to use `ElasticSearch <https://www.elastic.co/products/elasticsearch>`_ to create “fan-out on read” by “Storing atomic news and compose a news feed at the query time”.

After some trial and error, I managed to have feeds in ElasticSearch and perform fan-out on reads. ElasticSearch is incredible fast even with aggregation operations. The presentation on ElasticSearch talks about 40 milliseconds with 140 million of feeds with a 3 nodes. ElasticSearch is scalable which helps if you want to start small e.g., 1 node and progressively add more on demand.

Handling feeds in ElasticSearch and write aggregation queries is something that could discourage some Python programmers and that’s the reason for ElasticFeeds. ElasticFeeds encapsulates all these complexities allowing you to handle activity feeds with few lines of code while delegating all aggregation operations to ElasticSearch. The user only gets simple arrays of feeds as Python dictionaries.



Usage
=====

* Clone this repository and install ElasticFeeds


.. code-block:: bash

    $ git clone https://github.com/qlands/elasticfeeds.git
    $ cd elasticfeeds
    $ pip install -e .

* Install ElasticSearch. The easiest way here, if you want to test ElasticFeeds, is by using the provided docker compose file in the elasticsearch_docker directory

.. code-block:: bash

    $ sudo apt-get install docker docker-compose
    $ cd elasticsearch_docker
    $ sudo docker-compose up

    This will start a 3 node ElasticSearch (6.3.2) in port 9200 with Kibana in port 5601.
    If ElasticSearch fails to start due to "max virtual memory error" shutdown the docker (Ctrl+c) and do:

    $ sudo sysctl -w vm.max_map_count=262144
    $ sudo sudo docker-compose up


* Create a ElasticFeeds Manager

.. code-block:: python

    from elasticfeeds.manager import Manager
    my_manager = Manager('testfeeds', 'testnetwork')

* Follow some people

.. code-block:: python

    # Carlos follows himself (notification feed)
    my_manager.follow('carlos', 'carlos')
    # Carlos follows mark (Activity feed)
    my_manager.follow('carlos', 'mark')

* Create some activities

.. code-block:: python

    from elasticfeeds.activity import Actor, Object, Activity
    # Create an actor for Carlos of type person
    my_actor = Actor('carlos', 'person')
    # Create an Object for Project A of type project
    my_project = Object('project_a', 'project')
    # Create an activity representing that Carlos added project A
    my_activity = Activity('add', my_actor, my_project)
    # Store the activity
    my_manager.add_activity_feed(my_activity)

    # Create an actor for Mark of type person
    my_actor = Actor('mark', 'person')
    # Create an Object for Project A of type project
    my_project = Object('project_a', 'project')
    # Create an activity representing that Mark created a blog about project A
    my_activity = Activity('blog', my_actor, my_project)
    # Store the activity
    my_manager.add_activity_feed(my_activity)

* Query the activity feeds

.. code-block:: python

    from elasticfeeds.aggregators import UnAggregated, YearMonthTypeAggregator
    # Get feeds just ordered by date
    my_basic_aggregator = UnAggregated('carlos')
    my_feeds = my_manager.get_feeds(my_basic_aggregator)
    print(my_feeds)
    # Get feeds aggregated by year, month and type (verb)
    my_aggregate_feed = YearMonthTypeAggregator('carlos')
    my_feeds = my_manager.get_feeds(my_aggregate_feed)
    print(my_feeds)

Collaborate
===========
The way you manage feeds will depend on the kind of social platform you are implementing. While ElasticFeeds can store any kind of feeds and have some aggregator classes, the way you aggregate them would depend on how you want to present them to the end user.

The best way to collaborate with ElasticFeeds is by sharing aggregator classes with others. So if you have an aggregator, fork the project, create a pull request and I will be happy to add it to the base code :-)