#!/usr/bin/env python3
# Built-ins
import sys
import datetime
import time

# IPC-related # TODO: fix up imports here
import ipcqueue.posixmq
from ipcqueue.serializers import RawSerializer
from ipcqueue import posixmq

# Parsing
import json
import struct

# Qt bullshit x
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Property
from PySide6.QtCore import QRunnable, Slot, QThreadPool
from PySide6.QtCore import QDir, QUrl

# Local
from const import EventType, MessageType
from splits import Splits


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    """
    finished = Signal()  # QtCore.Signal
    error = Signal(tuple)
    result = Signal(object)


# noinspection PyUnresolvedReferences
class Worker(QRunnable):
    """
    Worker thread for the BXT message queue
    """
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.should_stop = False

    def stop_queue(self, stop_or_not):
        self.should_stop = stop_or_not

    @Slot()  # QtCore.Slot
    def run(self):
        """
        Your code goes in this function
        """
        try:
            q1 = posixmq.Queue("/BunnymodXT-BunnySplit", serializer=RawSerializer, maxsize=8192, maxmsgsize=8192)
        except ipcqueue.posixmq.QueueError:
            print("Couldn't open the message queue. Is a BXT game running?")
            return

        while True:
            if self.should_stop:
                # TODO: Is this ↓ useful? Are we going to stop the MQ manually any other time than on quitting the app?
                self.should_stop = not self.should_stop
                break

            if q1.qsize() > 0:
                try:
                    msg = q1.get_nowait()
                    bsp.parse_message(msg)
                    self.signals.result.emit(msg)
                except posixmq.QueueError as e:
                    print("Exception")
            else:
                time.sleep(0.01) # CPU usage, be gone


# noinspection PyUnresolvedReferences
class Bunnysplit(QObject):
    updated = Signal(QObject)
    current_time_changed = Signal(name="currentTimeChanged") # TODO: unique the signals, dont always send everything, where it isnt necessary

    def emit_signal(self):
        # print("Emitting self.__dict__")
        # self.updated.emit(self)
        self.current_time_changed.emit()

    # TODO: https://doc.qt.io/qtforpython/PySide6/QtCore/Property.html
    @Property(str, notify=current_time_changed)
    # @Property(float, notify=current_time_changed)
    def curr_time_getter(self):
        # return self.curr_time.total_seconds()
        return self.timedelta_to_timestring(self.curr_time)

    @Property(int, notify=current_time_changed)  # TODO: THIS ISNT FLOAT WTF
    def curr_split_index_getter(self):
        if self.timer_started:
            return self.curr_split
        else:
            return -1

    @Property(float, notify=current_time_changed)
    def curr_split_delta_getter(self):
        """
        TODO: Should I use this? Or should I just set the .delta for the current split every frame,
        TODO: i mean that's what's happening here anyway, but might as well do it outside of the Property?
        :return:
        """
        if self.timer_started:
            current_time_td = self.curr_time
            current_split_obj = self.splits_data.splits[self.curr_split]

            current_split_delta = current_time_td - self.timestring_to_timedelta(current_split_obj.split_time)  # TODO: . BEST TIME ETC.???

            return current_split_delta.total_seconds()

    @Property(bool, notify=current_time_changed) # TODO: int (enum)
    def timer_state_getter(self):
        return self.timer_started

    @Property("QVariantMap", notify=current_time_changed)
    def split_data(self):
        # split_data = {"title": self.splits_data.title,
        #              "category": self.splits_data.category}
        return self.splits_data.__dict__ # TODO: ← & ↑ combine, this is here for a breakpoint lul

    # @Property(list)
    # @Slot(result="QVariantList")
    @Property("QVariantList", notify=current_time_changed)
    def get_splits(self):
        splits_as_list = [x.__dict__ for x in self.splits_data.splits]
        return splits_as_list  # TODO: ← & ↑ combine, this is here for a breakpoint lul

    @Property(str)
    def json_filename(self):
        return self.filename

    @json_filename.setter
    def json_filename(self, val):
        self.filename = QDir.toNativeSeparators(QUrl(val).path())
        self.filename_changed.emit()

    @Signal
    def filename_changed(self):
        print(f"Filename changed, now it is {self.filename}")

    name = Property(str, json_filename, notify=filename_changed)

    def check_empty_splits(self):
        for split in self.splits_data.splits:
            if self.timestring_to_timedelta(split.split_time) == datetime.timedelta(0):
                split.split_time = "99:99.0000000"  # Set the split_time to None
            else:
                pass

    def open_split_file(self):
        if self.timer_started:
            return

        with open(self.filename) as f:
            self.splits_data = Splits.from_json(f.read())
            self.check_empty_splits()

        self.emit_signal()

    def __init__(self):
        super().__init__()
        self.timer_started = False
        self.curr_time = datetime.timedelta()
        self.curr_split = 0
        self.already_visited_maps = []
        self.filename = "splits/splits.hl.json"
        self.splits_data = None

        self.open_split_file()

        self.emit_signal()

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

    def parse_message(self, data: bytes):
        """
        Parse the received message from MQ
        :param data: message's content (in bytes)
        :return:
        """

        # print(f"\033[%d;%dH Current time: {self.curr_time}" % (0, 0))
        # print(f"DEBUG: Current time: {self.curr_time}")
        # print(f"DEBUG: Current split: {self.splits_data.splits[self.curr_split]}")
        # print(f"DEBUG: Already visited maps: {self.already_visited_maps}")

        if data[1] == MessageType.TIME.value:
            self.parse_time(data, 2)

        elif data[1] == MessageType.EVENT.value:
            self.parse_time(data, 3)
            self.parse_event(data)

        else:
            print("Unknown data in message queue!", data)

        self.emit_signal()

    def reset_timer(self):
        self.curr_time = datetime.timedelta(seconds=0)
        self.curr_split = 0
        self.timer_started = False  # TODO: should be state enum or someshit, probably
        self.already_visited_maps = [] #.clear()
        self.run_finished = False # TODO: repalce with enum timer_state?

        self.splits_data.attempt_count += 1

        for split in self.splits_data.splits:
            split.delta = 0 # reset the delta for all of them.


    def split(self, finish=False):
        # Temporarily save off the current literal time.
        current_time_td = self.curr_time
        current_time_sec = current_time_td.total_seconds()
        current_split_obj = self.splits_data.splits[self.curr_split]

        current_split_delta = current_time_td - self.timestring_to_timedelta(current_split_obj.split_time) # TODO: . BEST TIME ETC.???

        self.already_visited_maps.append(self.splits_data.splits[self.curr_split].title)
        self.splits_data.splits[self.curr_split].time_this_run = current_time_td
        self.splits_data.splits[self.curr_split].delta = current_split_delta.total_seconds()

        if finish:
            self.run_finished = True
            self.timer_started = False
            self.curr_split = 0
            self.splits_data.finished_count += 1
            self.save_finished_run()
        else:
            self.curr_split += 1

    def is_this_pb_run(self):
        if self.splits_data.splits[-1].time_this_run < self.timestring_to_timedelta(self.splits_data.splits[-1].split_time):
            return True

        return False


    def save_finished_run(self):
        """
        Serialize the finished run split data and save it to a file
        TODO: best time / best segment stuff
        :param is_pb_run:
        :return:
        """

        # Save whether this ia PB run into a variable
        is_pb_run = self.is_this_pb_run()

        for split in self.splits_data.splits:
            best_time_td = self.timestring_to_timedelta(split.split_time)
            if is_pb_run:
                split.split_time = self.timedelta_to_timestring(split.time_this_run)


        splits_data_dict = self.splits_data.to_dict()
        splits_list = splits_data_dict["splits"]

        with open ("splits/splits.{}.json".format(time.time()), "w") as f:
            json.dump(splits_data_dict, f, indent=4)

        # Finally, set the new data that we've just saved as the current splits_data
        self.splits_data = Splits.from_dict(splits_data_dict)


    def finish_run(self):
        self.run_finished = True
        self.curr_split = 0
        self.timer_started = False


    def parse_event(self, data: bytes):
        event_type = data[2]

        if event_type == EventType.GAMEEND.value:
            if self.curr_split == len(self.splits_data.splits) - 1:
                self.split(finish=True)

        elif event_type == EventType.MAPCHANGE.value:
            mapname = self.parse_mapname(data)
            # print(f"DEBUG2: Mapname got = {mapname}")
            # print(f"{self.curr_split} | {len(self.splits_data.splits)} | {self.already_visited_maps}")

            if self.curr_split == len(self.splits_data.splits) - 1: # TODO: We are not ending right now on a Split(), we only end on GAMEEND
                # self.finish_run()
                pass

            elif mapname in self.already_visited_maps:
                pass

            elif self.splits_data.splits[self.curr_split].title == mapname and len(self.already_visited_maps) == 0:
                self.split()

            elif self.splits_data.splits[self.curr_split + 1].title == mapname:
                self.split()

            else:
                print("WTF")
            print(self.already_visited_maps)

        elif event_type == EventType.TIMER_RESET.value:
            self.reset_timer() # TOOD: Reload the JSON file?

        elif event_type == EventType.TIMER_START.value:
            print("Timer started")
            self.timer_started = True

        elif event_type == EventType.BS_ALEAPOFFAITH.value:
            # TODO: Implement
            if "ba_teleport2" in self.already_visited_maps:
                self.split()

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

    def parse_time(self, data: bytes, offset: int): # TODO: should be static and return instead of setting self.curr_time?
        hours = struct.unpack('<I', data[offset:offset + 4])[0]
        minutes = data[offset + 4]
        seconds = data[offset + 5]
        milliseconds = struct.unpack('<H', data[offset + 6:offset + 8])[0]
        self.curr_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

if __name__ == "__main__":
    bsp = Bunnysplit()
    bsp.save_finished_run()

    QQuickStyle.setStyle("Material")
    app = QApplication(sys.argv)
    # app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    qml_file = str(Path(__file__).resolve().parent / "main.qml")
    engine.load(qml_file)

    # Define our backend object, which we pass to QML.
    engine.rootObjects()[0].setProperty('backend', bsp)

    if not engine.rootObjects():
        sys.exit(-1)

    worker = Worker()
    worker.signals.result.connect(bsp.parse_message)

    threadpool = QThreadPool()
    threadpool.start(worker)

    app.aboutToQuit.connect(lambda: worker.stop_queue(True))

    sys.exit(app.exec_())
