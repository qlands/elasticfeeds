#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from elasticfeeds.skeleton import fib

__author__ = "Carlos Quiros"
__copyright__ = "Carlos Quiros"
__license__ = "new-bsd"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
