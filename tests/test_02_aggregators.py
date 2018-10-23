#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticfeeds.manager import Manager
from elasticfeeds.aggregators import UnAggregated, RecentTypeAggregator, RecentTypeObjectAggregator


def test_aggregator():

    tst_manager = Manager('testfeeds', 'testnetwork')

    # Test Un-aggregated aggregator
    tst_base_aggregator = UnAggregated('cquiros')
    # This will bring 5 records
    tst_manager.get_feeds(tst_base_aggregator)

    # Test recent type aggregator
    tst_recent_type_aggregator = RecentTypeAggregator('cquiros')
    tst_manager.get_feeds(tst_recent_type_aggregator)

    # Test recent type object aggregator
    st_recent_type_object_aggregator = RecentTypeObjectAggregator('cquiros')
    tst_manager.get_feeds(st_recent_type_object_aggregator)




