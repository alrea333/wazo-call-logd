# -*- coding: utf-8 -*-
# Copyright 2016-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from hamcrest import (
    assert_that,
    has_entries,
    only_contains,
)
from xivo_test_helpers import until
from xivo_test_helpers.wait_strategy import WaitStrategy


class ComponentsWaitStrategy(WaitStrategy):

    def __init__(self, components):
        self._components = components

    def wait(self, integration_test):

        def components_are_ok(components):
            status = integration_test.call_logd.status.get()
            assert_that(status, has_entries(dict.fromkeys(self._components, value='ok')))

        until.assert_(components_are_ok, self._components, timeout=10)


class CallLogdEverythingUpWaitStrategy(WaitStrategy):

    def wait(self, integration_test):

        def everything_is_up():
            status = integration_test.call_logd.status.get()
            assert_that(status.values(), only_contains('ok'))

        until.assert_(everything_is_up, timeout=10)
