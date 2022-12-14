#!/usr/bin/env python3
# Built-ins
import sys
import datetime
import time

# Parsing
import json
from pathlib import Path

# Qt stuff
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
from utils import Utils
from mq_worker import Worker, WorkerSignals

# noinspection PyUnresolvedReferences
class Bunnysplit(QObject):
    updated = Signal(QObject)
    current_time_changed = Signal(name="currentTimeChanged")  # TODO: unique the signals, dont always send everything, where it isnt necessary

    def emit_signal(self):
        self.updated.emit(self)
        self.current_time_changed.emit()

    # TODO: https://doc.qt.io/qtforpython/PySide6/QtCore/Property.html
    @Property(str, notify=current_time_changed)
    def curr_time_getter(self):
        # return self.curr_time.total_seconds()
        return Utils.timedelta_to_timestring(self.curr_time)

    @Property(int, notify=current_time_changed)
    def curr_split_index_getter(self):
        if not self.timer_started:
            return -1
        return self.curr_split

    @Property(float, notify=current_time_changed)
    def curr_split_delta_getter(self) -> float:
        """
        TODO: Should I use this? Or should I just set the .delta for the current split every frame,
        TODO: i mean that's what's happening here anyway, but might as well do it outside of the Property?
        :return:
        """
        if self.timer_started:
            current_time_td = self.curr_time
            current_split_obj = self.splits_data.splits[self.curr_split]

            current_split_delta = current_time_td - Utils.timestring_to_timedelta(current_split_obj.split_time)  # TODO: . BEST TIME ETC.???

            return current_split_delta.total_seconds()

    @Property(bool, notify=current_time_changed)  # TODO: int (enum)
    def timer_state_getter(self) -> bool:
        return self.timer_started

    # noinspection PyTypeChecker
    @Property("QVariantMap", notify=current_time_changed)
    def split_data(self) -> dict:
        """
        This is here because QML can't into natively accessing Python class attributes...
        This is all awful, but whatever, life's too short.
        :return: Splits data as a dictionary
        """

        splits_data_dict = self.splits_data.__dict__
        for i in splits_data_dict["splits"]:
            if i.time_this_run != datetime.timedelta(0):
                i.time_this_run_str = Utils.timedelta_to_timestring(i.time_this_run)

        return splits_data_dict

    # @Property(list)
    # @Slot(result="QVariantList")
    # noinspection PyTypeChecker
    @Property("QVariantList", notify=current_time_changed)
    def get_splits(self) -> list:
        splits_as_list = [x.__dict__ for x in self.splits_data.splits]
        return splits_as_list  # TODO: ??? & ??? combine, this is here for a breakpoint lul

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

    def __init__(self):
        super().__init__()
        # Initialize variables
        self.timer_started = False
        self.curr_time = datetime.timedelta()
        self.curr_split = 0
        self.already_visited_maps = []
        self.filename = "splits/splits.example.json"
        self.splits_data = None
        self.run_finished = True

        self.open_split_file()  # Open the split file
        self.emit_signal()

    def parse_message(self, data: bytes) -> None:
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
            self.curr_time = Utils.parse_time(data, 2)

        elif data[1] == MessageType.EVENT.value:
            self.curr_time = Utils.parse_time(data, 3)
            self.parse_event(data)

        else:
            print("Unknown data in message queue!", data)

        self.emit_signal()

    def reset_timer(self):
        self.curr_time = datetime.timedelta(seconds=0)
        self.curr_split = 0
        self.timer_started = False  # TODO: should be state enum or someshit, probably
        self.already_visited_maps = []
        self.run_finished = False  # TODO: repalce with enum timer_state?

        self.splits_data.attempt_count += 1

        for split in self.splits_data.splits:
            split.delta = 0  # reset the delta for all of them.
            split.time_this_run = datetime.timedelta(0)  # reset time_this_run, since we've reset the run
            split.time_this_run_str = ""  # reset time_this_run_str, since we've reset the run

    def split(self, finish=False):
        # Temporarily save off the current literal time.
        current_time_td = self.curr_time
        current_time_sec = current_time_td.total_seconds()
        current_split_obj = self.splits_data.splits[self.curr_split]

        current_split_delta = current_time_td - Utils.timestring_to_timedelta(current_split_obj.split_time)  # TODO: . BEST TIME ETC.???

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

    def check_empty_splits(self):
        for split in self.splits_data.splits:
            if Utils.timestring_to_timedelta(split.split_time) == datetime.timedelta(0):
                split.split_time = "99:99:99.0000000"  # Set the split_time to None
            else:
                pass

    def open_split_file(self):
        if self.timer_started:
            return
        try:
            with open(self.filename) as f:
                self.splits_data = Splits.from_json(f.read())
                self.check_empty_splits()
        except FileNotFoundError as e:
            print(f"File does not exist. {e}")
            sys.exit(1)

        self.emit_signal()

    def is_this_pb_run(self):
        if self.splits_data.splits[-1].time_this_run < Utils.timestring_to_timedelta(self.splits_data.splits[-1].split_time):
            return True

        return False

    def save_finished_run(self):
        """
        Serialize the finished run split data and save it to a file
        TODO: best time / best segment stuff
        :return:
        """

        # Save whether this ia PB run into a variable
        is_pb_run = self.is_this_pb_run()

        for split in self.splits_data.splits:
            best_time_td = Utils.timestring_to_timedelta(split.split_time)
            if is_pb_run:
                split.split_time = Utils.timedelta_to_timestring(split.time_this_run)

        splits_data_dict = self.splits_data.to_dict()

        with open("splits/splits.{}.json".format(time.time()), "w") as f:
            json.dump(splits_data_dict, f, indent=4)

        # Finally, set the new data that we've just saved as the current splits_data
        # self.splits_data = Splits.from_dict(splits_data_dict)

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
            mapname = Utils.parse_mapname(data)
            # TODO: This is broken, splitting does not work correctly upon starting a run.
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
            self.reset_timer()  # TOOD: Reload the JSON file?

        elif event_type == EventType.TIMER_START.value:
            print("Timer started")
            self.timer_started = True

        elif event_type == EventType.BS_ALEAPOFFAITH.value:
            # TODO: Implement
            if "ba_teleport2" in self.already_visited_maps:
                self.split()


if __name__ == "__main__":
    bsp = Bunnysplit()

    QQuickStyle.setStyle("Material")
    app = QApplication(sys.argv)
    # app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    qml_file = str(Path(__file__).resolve().parent / "ui/main.qml")
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
