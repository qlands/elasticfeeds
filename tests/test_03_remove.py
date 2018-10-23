#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticfeeds.manager import Manager


def test_remove():
    # Carlos un-watches Project A. Test of convenience function
    tst_manager = Manager('testfeeds', 'testnetwork')
    tst_manager.un_watch('cquiros', '50a808d3-1227-4149-80e9-20922bded1cf', 'project')

    # Carlos un-follow Eduardo. Test of convenience function
    tst_manager.un_follow('cquiros', 'edoquiros')
