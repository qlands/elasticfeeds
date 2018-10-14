#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from elasticfeeds.manager import Manager
from elasticfeeds.network import Link
import datetime


def test_manager():
    tst_manager = Manager('testfeeds', 'testnerwork', delete_network_if_exists=True, delete_feeds_if_exists=True)
    tst_link = Link('cquiros', 'edoquiros')
    tst_link.actor_id = 'cquiros'
    tst_link.feed_component_id = 'edoquiros'
    tst_link.linked = datetime.datetime.now()
    tst_link.feed_component_type = 'person'
    tst_link.feed_component_class = 'actor'
    tst_link.link_type = 'follow'
    tst_link.link_weight = 1
    tst_link.extra = {'some_extra_data': 'test'}
    tst_manager.add_network_link(tst_link)
    #tst_manager.get_links(tst_link)

