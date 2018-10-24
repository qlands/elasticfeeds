#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticfeeds.manager import Manager
from elasticfeeds.aggregators import UnAggregated, RecentTypeAggregator, RecentTypeObjectAggregator, \
    RecentObjectTypeAggregator, DateWeightAggregator, YearMonthTypeAggregator
import pprint


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
    tst_recent_type_object_aggregator = RecentTypeObjectAggregator('cquiros')
    tst_manager.get_feeds(tst_recent_type_object_aggregator)

    # Test recent object type aggregator
    tst_recent_object_type_aggregator = RecentObjectTypeAggregator('cquiros')
    tst_manager.get_feeds(tst_recent_object_type_aggregator)

    # Test recent object type aggregator
    tst_date_weight_aggregator = DateWeightAggregator('cquiros')
    tst_manager.get_feeds(tst_date_weight_aggregator)

    # Test year, month, type aggregator
    tst_year_month_type_aggregator = YearMonthTypeAggregator('cquiros')
    tst_manager.get_feeds(tst_year_month_type_aggregator)





