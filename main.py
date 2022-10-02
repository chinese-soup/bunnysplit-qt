#!/usr/bin/env python3
# Built-ins
import sys
import datetime

# IPC-related
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

# Local
from const import EventType, MessageType


# Qt bullshit x

from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QTimer, QObject, Signal, Slot
from PySide6.QtCore import QRunnable, Slot, QThreadPool


@dataclass
class Split:
    title: str
    time: str
    best_time: str
    best_segment: str
    identifier: int = field(default_factory=count().__next__)


@dataclass
class Splits(JSONWizard):
    title: str
    category: str
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
    '''
    Worker thread
    '''
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Your code goes in this function
        '''

        q1 = posixmq.Queue("/bxt", serializer=RawSerializer, maxsize=5000, maxmsgsize=50000)
        while True:
            while q1.qsize() > 0:
                try:
                    msg = q1.get_nowait()
                    print(msg)
                    self.signals.result.emit(msg)
                except posixmq.QueueError as e:
                    pass




class BunnysplitShit(QObject):
    updated = Signal("QVariantMap")

    def emit_signal(self):
        # Pass the current time to QML.
        # curr_time = strftime("%H:%M:%S", localtime())
        print(f"Emitting {self.data}")
        self.data["current_time"] = self.curr_time
        if self.data:
            self.updated.emit(self.data)
        else:
            self.updated.emit(self.data)

    def __init__(self):
        super().__init__()
        self.timer_stared = False
        self.curr_time = 0
        self.curr_split = 0
        self.already_visited_maps = []
        self.data = {"current_time": 0.0}

        with open("splits.example.json") as f:
            self.splits = Splits.from_json(f.read())

    def timedelta_to_timestring(self) -> str:
        """
        Converts timedelta to string time for use in the JSON splits file
        :return:
        """
        pass

    def timestring_to_timedelta(self) -> datetime.timedelta:
        """
        Converts string time to timedelta
        :return:
        """
        pass

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
        print(f"DEBUG: Current time: {self.curr_time}")
        print(f"DEBUG: Current split: {self.splits.splits[self.curr_split]}")
        print(f"DEBUG: Already visited maps: {self.already_visited_maps}")

        if data[1] == MessageType.TIME.value:
            print("Time", data)
            self.parse_time(data, 2)

        elif data[1] == MessageType.EVENT.value:
            print("Event", data)
            self.parse_time(data, 3)
            self.parse_event(data)

        else:
            print("None", data)

        self.emit_signal()

    def reset_timer(self):
        self.curr_time = 0
        self.curr_split = 0
        self.timer_started = False  # TODO: should be state enum or someshit, probably
        self.already_visited_maps.clear()

    def parse_event(self, data: bytes):
        event_type = data[2]
        if event_type == EventType.GAMEEND.value:
            pass

        elif event_type == EventType.MAPCHANGE.value:
            length = struct.unpack('<I', data[11:15])[0]
            mapname = data[15:15 + length].decode("utf-8")
            print(f"DEBUG2: Mapname got = {mapname}")
            if mapname in self.already_visited_maps:
                pass

            elif self.splits.splits[self.curr_split + 1].title == mapname and len(self.already_visited_maps) == 0:
                self.already_visited_maps.append(self.splits.splits[self.curr_split].title)
                self.curr_split += 1

            elif self.splits.splits[self.curr_split + 1].title == mapname \
                    and self.splits.splits[self.curr_split].title not in self.already_visited_maps:
                self.already_visited_maps.append(self.splits.splits[self.curr_split].title)
                self.curr_split += 1

            print(self.curr_time)
            print(self.splits.splits[self.curr_split])
            print(self.curr_split)

        elif event_type == EventType.TIMER_RESET.value:
            self.reset_timer()

        elif event_type == EventType.TIMER_START.value:
            self.timer_started = True
            self.curr_split = 0

        elif event_type == EventType.BS_ALEAPOFFAITH.value:
            pass

    def parse_time(self, data: bytes, offset: int):
        # print(f"ParseTime({data}, {offset})")
        hours = struct.unpack('<I', data[offset:offset + 4])[0]
        minutes = data[offset + 4]
        seconds = data[offset + 5]
        milliseconds = struct.unpack('<H', data[offset + 6:offset + 8])[0]
        # print(f"{hours}, {minutes}, {seconds}, {milliseconds}")
        curr_time = hours, minutes, seconds, milliseconds  # TODO: ?
        self.curr_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds).total_seconds()

        # self.curr_time = hours * 3600 + minutes * 60 + seconds + milliseconds/1000

if __name__ == "__main__":
    bsp = BunnysplitShit()

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

    sys.exit(app.exec_())
