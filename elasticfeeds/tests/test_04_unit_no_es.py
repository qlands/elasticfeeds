#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests that do NOT require a running ElasticSearch cluster.

These exercise the pure-Python parts of the library (activity / network / aggregator
construction and serialization) and guard against regressions of a few historical bugs:

* ``Activity`` used to overwrite the provided ``published`` date with ``now`` at
  serialization time, so activities could not be back-dated.
* ``datetime.datetime.now()`` was used as a default argument in several places, which
  is evaluated once at import time (every call shared the same frozen timestamp).
* ``Manager.un_follow`` could not un-follow links created with a non-default type.
"""

import inspect
import datetime

import pytest

from elasticfeeds.activity import Actor, Object, Activity
from elasticfeeds.network import Link, LinkedActivity
from elasticfeeds.aggregators import UnAggregated
from elasticfeeds.exceptions import IDError
from elasticfeeds.manager import Manager


def test_activity_honours_explicit_published():
    """A provided ``published`` date must be kept verbatim (allows back-dating/import)."""
    past = datetime.datetime(2020, 1, 2, 3, 4, 5)
    activity = Activity(
        "add", Actor("carlos", "person"), Object("p1", "project"), published=past
    )
    result = activity.get_dict()
    assert result["published"] == past.isoformat()
    assert result["published_date"] == "2020-01-02"
    assert result["published_time"] == "03:04:05"
    assert result["published_year"] == 2020
    assert result["published_month"] == 1


def test_activity_default_published_is_dynamic():
    """With no ``published`` the date defaults to *now at call time*, not import time."""
    before = datetime.datetime.now()
    activity = Activity("add", Actor("carlos", "person"), Object("p1", "project"))
    after = datetime.datetime.now()
    published = datetime.datetime.fromisoformat(activity.get_dict()["published"])
    assert before <= published <= after


def test_link_default_linked_is_dynamic():
    """``Link.linked`` defaults to *now at call time*, not import time."""
    before = datetime.datetime.now()
    link = Link("carlos", LinkedActivity("mark"))
    after = datetime.datetime.now()
    assert before <= link.linked <= after


def test_ids_with_spaces_are_rejected():
    with pytest.raises(IDError):
        Actor("two words", "person")
    with pytest.raises(IDError):
        Object("two words", "project")


def test_un_follow_accepts_activity_type():
    """un_follow must expose the same ``activity_type`` knob as follow so that links
    created with a non-default type can be removed."""
    assert "activity_type" in inspect.signature(Manager.un_follow).parameters


def test_aggregator_query_dict_for_actor_and_object_links():
    """set_query_dict turns the network into the expected bool/should query, server-free."""
    aggregator = UnAggregated("carlos")
    aggregator.network_array = [
        {
            "linked": "2020-01-01T00:00:00",
            "actor_id": "carlos",
            "link_type": "follow",
            "linked_activity": {
                "activity_class": "actor",
                "id": "mark",
                "type": "person",
            },
            "link_weight": 1,
        },
        {
            "linked": "2020-01-01T00:00:00",
            "actor_id": "carlos",
            "link_type": "watch",
            "linked_activity": {
                "activity_class": "object",
                "id": "proj_a",
                "type": "project",
            },
            "link_weight": 1,
        },
    ]
    aggregator.set_query_dict()
    should = aggregator.query_dict["query"]["bool"]["should"]
    # one clause for the actor link, two for the object link (object + target)
    assert len(should) == 3
    actor_terms = should[0]["bool"]["must"]
    assert {"term": {"actor.id": "mark"}} in actor_terms
    object_clause = should[1]["bool"]["must"]
    assert {"term": {"object.id": "proj_a"}} in object_clause
    target_clause = should[2]["bool"]["must"]
    assert {"term": {"target.id": "proj_a"}} in target_clause


def test_aggregator_empty_network_yields_no_query():
    aggregator = UnAggregated("carlos")
    aggregator.network_array = []
    aggregator.set_query_dict()
    assert aggregator.query_dict is None
