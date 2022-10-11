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

# Data class related
from typing import List
from itertools import count
from dataclasses import dataclass, field
from dataclass_wizard import JSONWizard

# Qt bullshit x
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QTimer, QObject, Signal, Slot, Property
from PySide6.QtCore import QRunnable, Slot, QThreadPool

# Local
from const import EventType, MessageType


@dataclass
class Split(QObject):
    title: str
    time: str
    best_time: str
    best_segment: str

    identifier: int = field(default_factory=count().__next__)
    delta: float = field(default=0) # TODO: ←&↓ These in seperate subclass? dunno if possible tho because of QObject bs tho...
    time_this_run: datetime.timedelta = field(default=datetime.timedelta())

    # @Property(str, notify=mrdat)
    # def get_title(self):
    #     return self.title
    #

@dataclass
class Splits(JSONWizard):
    title: str
    category: str
    attempt_count: int
    finished_count: int
    splits: List[Split] = field(default_factory=list)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = Signal()  # QtCore.Signal
    error = Signal(tuple)
    result = Signal(object)


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
            q1 = posixmq.Queue("/bxt", serializer=RawSerializer, maxsize=8192, maxmsgsize=8192)
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


class BunnysplitShit(QObject):
    updated = Signal(QObject)
    #updated = Signal("QVariantMap")
    current_time_changed = Signal(name="currentTimeChanged") # TODO: unique the signals, dont always send everything, where it isnt necessary

    def emit_signal(self):
        # Pass the current time to QML.
        # curr_time = strftime("%H:%M:%S", localtime())
        # self.updated.emit(self)
        print("Emitting self.__dict__")
        self.updated.emit(self)
        self.current_time_changed.emit()

    # TODO: https://doc.qt.io/qtforpython/PySide6/QtCore/Property.html
    @Property(str, notify=current_time_changed)
    # @Property(float, notify=current_time_changed)
    def curr_time_getter(self):
        # return self.curr_time.total_seconds()
        return self.timedelta_to_timestring(self.curr_time)

    @Property(float, notify=current_time_changed)
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

            current_split_delta = current_time_td - self.timestring_to_timedelta(current_split_obj.time)  # TODO: . BEST TIME ETC.???

            return current_split_delta.total_seconds()

    @Property(bool, notify=current_time_changed) #TODO: int (enum)
    def timer_state_getter(self):
        return self.timer_started

    @Property("QVariantMap", notify=current_time_changed)
    def split_data(self):
        #split_data = {"title": self.splits_data.title,
        #              "category": self.splits_data.category}
        return self.splits_data.__dict__ # TODO: ← & ↑ combine, this is here for a breakpoint lul

    # @Property(list)
    #@Slot(result="QVariantList")
    @Property("QVariantList", notify=current_time_changed)
    def get_splits(self):
        splits_as_list = [x.__dict__ for x in self.splits_data.splits]
        return splits_as_list # TODO: ← & ↑ combine, this is here for a breakpoint lul

    def __init__(self):
        super().__init__()
        self.timer_started = False
        self.curr_time = datetime.timedelta()
        self.curr_split = 0
        self.already_visited_maps = []

        with open("splits/splits.1665497570.9953058.json") as f:
        #with open("splits.example.json") as f:
            self.splits_data = Splits.from_json(f.read())

        self.emit_signal()

    def timedelta_to_timestring(self, orig_timedelta) -> str:
        """
        Converts timedelta to string time for use in the JSON splits file
        :return: String in the format of "MM:SS.f" f = milliseconds
        """
        time_obj = (datetime.datetime.min + orig_timedelta).time()
        timestring = datetime.time.strftime(time_obj, "%M:%S.%f")
        return timestring

    def timestring_to_timedelta(self, orig_time) -> datetime.timedelta:
        """
        Converts string time to timedelta
        :return: datetime.timedelta object representing the original string time
        """
        # orig_time = "04:02.934"
        dt_parsed = datetime.datetime.strptime(orig_time, '%M:%S.%f').time()
        ms = dt_parsed.microsecond / 1000
        delta_obj = datetime.timedelta(hours=dt_parsed.hour,
                                       minutes=dt_parsed.minute,
                                       seconds=dt_parsed.second,
                                       milliseconds=ms)
        print(delta_obj)
        print(delta_obj.total_seconds())

        return delta_obj

    def reset(self):
        pass

    def parse_message(self, data: bytes):
        """
        Parse the received message from MQ
        :param data: message's content (in bytes)
        :return:
        """
        # print(data[1])
        # print(MessageType.TIME.value)

        # print(f"\033[%d;%dH Current time: {self.curr_time}" % (0, 0))
        #print(f"DEBUG: Current time: {self.curr_time}")
        #print(f"DEBUG: Current split: {self.splits_data.splits[self.curr_split]}")
        #print(f"DEBUG: Already visited maps: {self.already_visited_maps}")

        if data[1] == MessageType.TIME.value:
            # print("Time", data)
            self.parse_time(data, 2)

        elif data[1] == MessageType.EVENT.value:
            # print("Event", data)
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

        current_split_delta = current_time_td - self.timestring_to_timedelta(current_split_obj.time) # TODO: . BEST TIME ETC.???

        self.already_visited_maps.append(self.splits_data.splits[self.curr_split].title)
        self.splits_data.splits[self.curr_split].time_this_run = current_time_td
        self.splits_data.splits[self.curr_split].delta = current_split_delta.total_seconds()

        if finish:
            self.run_finished = True
            self.timer_started = False
            self.curr_split = 0
            self.splits_data.finished_count += 1
            self.save_finished_run(is_pb_run=True)
        else:
            self.curr_split += 1

    def save_finished_run(self, is_pb_run=True):
        """
        Blabla
        TODO: best time / best segment stuff
        :param is_pb_run:
        :return:
        """
        for split in self.splits_data.splits:
            best_time_td = self.timestring_to_timedelta(split.time)
            if is_pb_run:
                split.time = self.timedelta_to_timestring(split.time_this_run)

        splits_data_dict = self.splits_data.to_dict()
        splits_list = splits_data_dict["splits"]
        
        # Remove the key that are supposed to be runtime only
        del_keys = ["timeThisRun", "delta", "identifier"]
        cleaned_up_splits = [
            {k: v for k, v in sub.items() if k not in del_keys}
            for sub in splits_list
        ]

        # Replace the splits in the original dictionary
        # with a list of new "runtime data cleaned up" dictionaries
        splits_data_dict["splits"] = cleaned_up_splits

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

            # print(self.curr_time)
            # print(self.splits_data.splits[self.curr_split])
            # print(self.curr_split)

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
        # print(f"ParseTime({data}, {offset})")
        hours = struct.unpack('<I', data[offset:offset + 4])[0]
        minutes = data[offset + 4]
        seconds = data[offset + 5]
        milliseconds = struct.unpack('<H', data[offset + 6:offset + 8])[0]
        # curr_time = hours, minutes, seconds, milliseconds  # TODO: ?
        self.curr_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

        # self.curr_time = hours * 3600 + minutes * 60 + seconds + milliseconds/1000

if __name__ == "__main__":
    bsp = BunnysplitShit()

    """origgg = "04:20.300"
    print("ORIG = ", origgg)
    dt = bsp.timestring_to_timedelta(origgg)
    end = bsp.timedelta_to_timestring(dt)
    assert origgg == end"""

    #bsp.save_finished_run()
    #sys.exit(1)

    QQuickStyle.setStyle("Material")
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    qml_file = str(Path(__file__).resolve().parent / "main.qml")
    engine.load(qml_file)

    # Define our backend object, which we pass to QML.
    #backend = Backend()

    engine.rootObjects()[0].setProperty('backend', bsp)

    # Initial call to trigger first update. Must be after the setProperty to connect signals.
    # backend.emit_signal()"""

    if not engine.rootObjects():
        sys.exit(-1)

    worker = Worker()
    threadpool = QThreadPool()
    threadpool.start(worker)
    worker.signals.result.connect(bsp.parse_message)
    app.aboutToQuit.connect(lambda: worker.stop_queue(True))
    sys.exit(app.exec_())
