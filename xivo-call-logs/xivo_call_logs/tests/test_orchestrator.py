# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from hamcrest import assert_that, equal_to
from mock import Mock, sentinel, patch
from pika.channel import Channel
from pika.spec import Basic
from unittest import TestCase

from xivo_call_logs.manager import CallLogsManager
from xivo_call_logs.orchestrator import CallLogsOrchestrator
from xivo_bus.ctl.consumer import BusConsumer, BusConnectionError

EXCHANGE = 'xivo-ami'
KEY = 'cel'
RECONNECTION_DELAY = 5
QUEUE_NAME = 'xivo-call-logd-queue'


class TestCallLogsOrchestrator(TestCase):
    def setUp(self):
        self.channel_mock = Mock(Channel)
        self.method = Mock(Basic.Deliver)
        self.method.delivery_tag = sentinel.tag
        self.bus_consumer_mock = Mock(BusConsumer)
        self.bus_consumer_mock.run.side_effect = [Exception()]

        self.call_logs_manager_mock = Mock(CallLogsManager)
        self.orchestrator = CallLogsOrchestrator(self.bus_consumer_mock, self.call_logs_manager_mock)

    def tearDown(self):
        pass

    def test_when_run_then_initiate_bus_consumer(self):
        self.assertRaises(Exception, self.orchestrator.run)

        self.bus_consumer_mock.connect.assert_called_once_with()
        self.bus_consumer_mock.queue_declare.assert_called_once_with(callback=None,
                                                                     queue=QUEUE_NAME,
                                                                     exclusive=True)
        self.bus_consumer_mock.add_binding.assert_called_once_with(QUEUE_NAME,
                                                                   EXCHANGE,
                                                                   KEY,
                                                                   self.orchestrator.on_cel_event)
        self.bus_consumer_mock.run.assert_called_once_with()

    def test_given_linkedid_end_when_on_cel_event_then_generate(self):
        linkedid = '1391789340.26'
        body = """
            {
            "data": {
                "EventTime": "2014-02-07 11:09:03",
                "LinkedID": "%s",
                "UniqueID": "1391789340.26",
                "EventName": "LINKEDID_END"
            },
            "name": "CEL"
            }
        """ % linkedid

        self.orchestrator.on_cel_event(self.channel_mock, self.method, sentinel.header, body)

        self.call_logs_manager_mock.generate_from_linked_id.assert_called_once_with(linkedid)
        self.channel_mock.basic_ack.assert_called_once_with(delivery_tag=self.method.delivery_tag)

    def test_given_no_linkedid_end_when_on_cel_event_then_pass(self):
        linkedid = '1391789340.26'
        body = """
            {
            "data": {
                "EventTime": "2014-02-07 11:09:03",
                "LinkedID": "%s",
                "UniqueID": "1391789340.26",
                "EventName": "CHAN_START"
            },
            "name": "CEL"
            }
        """ % linkedid

        self.orchestrator.on_cel_event(self.channel_mock, self.method, sentinel.header, body)

        assert_that(self.call_logs_manager_mock.generate_from_linked_id.call_count, equal_to(0))
        self.channel_mock.basic_ack.assert_called_once_with(delivery_tag=self.method.delivery_tag)

    def test_given_exception_when_run_then_stop_and_raise(self):
        self.assertRaises(Exception, self.orchestrator.run)

        assert_that(self.bus_consumer_mock.stop.call_count, equal_to(1))

    @patch('time.sleep')
    def test_given_bus_connection_error_when_run_then_bus_reconnect(self, sleep_mock):
        self.bus_consumer_mock.run.side_effect = [BusConnectionError(), Exception()]

        self.assertRaises(Exception, self.orchestrator.run)

        assert_that(self.bus_consumer_mock.stop.call_count, equal_to(2))
        sleep_mock.assert_called_once_with(RECONNECTION_DELAY)
        assert_that(self.bus_consumer_mock.run.call_count, equal_to(2))
