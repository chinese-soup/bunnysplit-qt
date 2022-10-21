import datetime
import struct

class Utils:
    @staticmethod
    def parse_mapname(data):
        """
        Parses the mapname from the `data` of an event
        :param data: event's data
        :return:
        """
        length = struct.unpack('<I', data[11:15])[0]
        mapname = data[15:15 + length].decode("utf-8")
        return mapname

    @staticmethod
    def parse_time(data: bytes, offset: int): # TODO: should be static and return instead of setting self.curr_time?
        hours = struct.unpack('<I', data[offset:offset + 4])[0]
        minutes = data[offset + 4]
        seconds = data[offset + 5]
        milliseconds = struct.unpack('<H', data[offset + 6:offset + 8])[0]
        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)


    @staticmethod
    def timedelta_to_timestring(orig_timedelta) -> str:
        """
        Converts timedelta to string time for use in the JSON splits file
        TODO: make static and gtfo Bunnysplit class
        :return: String in the format of "MM:SS.f" f = milliseconds
        """
        time_obj = (datetime.datetime.min + orig_timedelta).time()
        timestring = datetime.time.strftime(time_obj, "%M:%S.%f")
        return timestring

    @staticmethod
    def timestring_to_timedelta(orig_time) -> datetime.timedelta:
        """
        Converts string time to timedelta
        TODO: make static and gtfo Bunnysplit class
        :return: datetime.timedelta object representing the original string time
        """
        # orig_time = "04:02.934"
        try:
            dt_parsed = datetime.datetime.strptime(orig_time, '%M:%S.%f').time()
            ms = dt_parsed.microsecond / 1000
            delta_obj = datetime.timedelta(hours=dt_parsed.hour,
                                           minutes=dt_parsed.minute,
                                           seconds=dt_parsed.second,
                                           milliseconds=ms)
        except ValueError:
            delta_obj = datetime.timedelta(0)

        if delta_obj == datetime.timedelta(0):
            print(delta_obj)
            print(delta_obj.total_seconds())

        return delta_obj