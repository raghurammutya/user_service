import logging
from datetime import datetime
from zoneinfo import ZoneInfo

class CustomDate:
    def __init__(self, in_date):
        self.date, self.time, self.datetime, self.datetime_Z = (None,) * 4
        if not self.is_empty(in_date):
            self.datetime, self.datetime_Z = self.process_datetimes(in_date)
            if self.datetime:
                self.date = self.datetime.date()

    def add_timezone(self, dt_obj):
        if not isinstance(dt_obj, datetime) or dt_obj is None:
            return None

        ist_timezone = ZoneInfo("Asia/Kolkata")
        return dt_obj.astimezone(ist_timezone)

    def recognize_and_convert_dt(self, date_str):
        formats = ['%Y-%m-%dT%H:%M:%S.%f', '%d-%b-%Y', '%Y-%m-%d %H:%M:%S.%f', '%d-%m-%Y', '%Y-%m-%d']
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return self.add_timezone(date_obj)
            except ValueError:
                continue
        return None

    def convert_to_iso_z(self, dt_obj):
        return dt_obj.strftime('%Y-%m-%dT%H:%M:%S.000Z') if dt_obj else None

    @staticmethod
    def is_empty(date_obj):
        return not date_obj.strip() if isinstance(date_obj, str) else date_obj is None

    def process_datetimes(self, date_str):
        if isinstance(date_str, str):
            dt_obj = self.recognize_and_convert_dt(date_str)
        elif isinstance(date_str, datetime):
            dt_obj = self.add_timezone(date_str)
        else:
            return None, None

        return dt_obj, self.convert_to_iso_z(dt_obj)