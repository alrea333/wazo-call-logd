# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

import datetime
from xivo_dao.data_handler.call_log.model import CallLog


class RawCallLog(object):

    def to_call_log(self):
        result = CallLog(
            date=self.date,
            source_name=self.source_name,
            source_exten=self.source_exten,
            destination_name=self.destination_name,
            destination_exten=self.destination_exten,
            user_field=self.user_field,
            answered=self.answered,
            duration=self.duration
        )

        return result

    @property
    def duration(self):
        default_value = datetime.timedelta(0)
        if (hasattr(self, 'communication_start') and hasattr(self, 'communication_end')
                and self.communication_start and self.communication_end):
            duration = self.communication_end - self.communication_start
            return max(duration, default_value)
        else:
            return default_value