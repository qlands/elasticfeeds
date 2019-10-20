#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticfeeds.manager import Manager
from elasticfeeds.activity import Actor, Object, Target, Activity
import datetime
import time


def test_different_dates():
    now = datetime.datetime.now()
    tst_manager = Manager("testfeeds", "testnetwork")

    # --------------------------- Adds some activity feeds ------------------------------

    # An actor called edoquiros adds project C a year ago

    # Creates an actor
    tst_actor = Actor("edoquiros", "person")
    # Creates an object
    tst_object = Object("0cf19f7f-30c4-4e12-9fe0-96bbdeeadbdd", "project")
    # Creates an Activity
    tst_activity = Activity(
        "add", tst_actor, tst_object, published=now - datetime.timedelta(days=365)
    )
    # Adds the activity
    tst_manager.add_activity_feed(tst_activity)

    # edoquiros adds Form 2 in project C 12 days from now

    # Creates an object
    tst_object = Object("1636e233-7acd-4596-aab1-9980b7de69ff", "form")
    # Creates a target
    tst_target = Target("0cf19f7f-30c4-4e12-9fe0-96bbdeeadbdd", "project")
    # Creates an Activity
    tst_activity = Activity(
        "add",
        tst_actor,
        tst_object,
        activity_target=tst_target,
        published=now + datetime.timedelta(days=12),
    )
    # Adds the activity
    tst_manager.add_activity_feed(tst_activity)
    # Wait 2 seconds for ES to store previous data. This is only for this testing script
    time.sleep(2)
