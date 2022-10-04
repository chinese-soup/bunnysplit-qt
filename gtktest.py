import threading
import time

import gi
#from gi.overrides import GLib

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GObject
from gi.repository import Gdk

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



class BunnysplitShit:

    def __init__(self):
        super().__init__()
        self.timer_stared = False
        self.curr_time = 0.0
        self.curr_split = 0
        self.already_visited_maps = []
        self.data = {"current_time": 0.0} # TODO: This isn't supposed to be a dict

        with open("splits.example.json") as f:
            self.splits_data = Splits.from_json(f.read())

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
        print(f"DEBUG: Current split: {self.splits_data.splits[self.curr_split]}")
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

            elif self.splits_data.splits[self.curr_split + 1].title == mapname and len(self.already_visited_maps) == 0:
                self.already_visited_maps.append(self.splits_data.splits[self.curr_split].title)
                self.curr_split += 1

            elif self.splits_data.splits[self.curr_split + 1].title == mapname \
                    and self.splits_data.splits[self.curr_split].title not in self.already_visited_maps:
                self.already_visited_maps.append(self.splits_data.splits[self.curr_split].title)
                self.curr_split += 1

            print(self.curr_time)
            print(self.splits_data.splits[self.curr_split])
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


def set_current_split_cell(column, cell, model, itr, user_data):
    """

    :param column:
    :param cell:
    :param model:
    :param itr: Iterator
    :param col_num: Column number
    :return:
    """

    value = model.get(itr, user_data)[0]
    path = model.get_path(itr)
    row = path[0]
    if isinstance(value, float):
        if value < 0:
            cell.set_property("foreground", "red")

def app_main():
    #win = Gtk.Window(default_height=50, default_width=300)

    #progress = Gtk.ProgressBar(show_text=True)
    #win.add(progress)

    bsp = BunnysplitShit()
    q1 = posixmq.Queue("/bxt", serializer=RawSerializer, maxsize=5000, maxmsgsize=50000)

    from gi.repository.GdkX11 import X11Screen
    display = Gdk.Display.get_default()
    screen = display.get_default_screen()

    css_provider = Gtk.CssProvider()
    css_provider.load_from_path('themes/livesplitlike.css')

    context = Gtk.StyleContext()
    context.add_provider_for_screen(screen, css_provider,
                                    Gtk.STYLE_PROVIDER_PRIORITY_USER)

    builder = Gtk.Builder()
    builder.add_from_file("asdfasdf.glade")


    window = builder.get_object("window1")
    window.show_all()
    window.connect("destroy", Gtk.main_quit)

    store = Gtk.ListStore(str, float, float, str)
    store.append(["one", 1.0, 4.0, "#000000"])
    store.append(["two", 2.0, -5.0, "#000000"])
    store.append(["three", 3.0, 6.0, "#000000"])

    tree = builder.get_object("gtktreeview1")
    tree.set_model(store)

    #for i, column_title in enumerate(["Title", "Diff", "Time"]):
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Rofl", renderer, text=0, foreground=3)
    #column.set_cell_data_func(renderer, set_current_split_cell, 0)

    renderer2 = Gtk.CellRendererText()
    column2 = Gtk.TreeViewColumn("Rofl2", renderer2, text=1, foreground=3)
    #column2.set_cell_data_func(renderer2, set_current_split_cell, 1)


    renderer3 = Gtk.CellRendererText()
    column3 = Gtk.TreeViewColumn("Rofl3", renderer3, text=2, foreground=3)
    #column3.set_cell_data_func(renderer3, set_current_split_cell, 2)

    tree.append_column(column)
    tree.append_column(column2)
    tree.append_column(column3)

    label1 = builder.get_object("timer")
    label1.set_name("timer")
    label1.id = "timer"

    gamename_label = builder.get_object("gamename")
    gamename_label.set_markup(f"<b>{bsp.splits_data.title}</b> <small>({bsp.splits_data.category})</small>")

    def update_progess(i):
        print(f"Update progress = {i.curr_time}")
        label1.set_text(f"{i.curr_time}")
        return False

    def example_target(q1_inst, bsp_inst):
        while True:
            if q1_inst.qsize() > 0:
                try:
                    msg = q1_inst.get_nowait()
                    print(msg)
                    bsp_inst.parse_message(msg)
                    GLib.idle_add(update_progess, bsp)
                except posixmq.QueueError as e:
                    print("Exception")
            else:
                #print("Sleeping for 0.1 seconds")
                time.sleep(0.01)


    thread = threading.Thread(target=example_target, args=(q1, bsp))
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    app_main()
    Gtk.main()