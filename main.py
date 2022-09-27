#!/usr/bin/env python3
from enum import Enum
import time
import sys
from ipcqueue.serializers import RawSerializer
from ipcqueue import posixmq
import ctypes
import struct
from posix_ipc import MessageQueue, O_NONBLOCK, O_RDONLY
import json
from typing import List
from dataclasses import dataclass, field
from dataclass_wizard import JSONWizard
import datetime
import curses
from itertools import count

class MessageType(Enum):
    TIME = 0x00
    CLIP = 0x01
    WATER = 0x02
    FRAMETIME_REMAINDER = 0x03
    EVENT = 0x04

class EventType(Enum):
    GAMEEND = 0x00
    MAPCHANGE = 0x01
    TIMER_RESET = 0x02
    TIMER_START = 0x03
    BS_ALEAPOFFAITH = 0x04

class BunnysplitShit:
    def __init__(self):
        self.timer_stared = False
        self.curr_time = 0
        self.curr_split = 0

        with open("splits.example.json") as f:
            self.splits = Splits.from_json(f.read())

    def ParseMessage(self, data: bytes):
        #print(data[1])
        #print(MessageType.TIME.value)

        """print(f"\033[%d;%dH Current time: {self.curr_time}" % (0, 0))
        print(f"Current split: {self.splits.splits[self.curr_split]}")"""

        if data[1] == MessageType.TIME.value:
            print("Time", data)
            self.ParseTime(data, 2)

        elif data[1] == MessageType.EVENT.value:
            print("Event", data)
            self.ParseTime(data, 3)
            self.ParseEvent(data)

        else:
            print("None", data)

    def ParseEvent(self, data: bytes):
        event_type = data[2]
        if event_type == EventType.GAMEEND.value:
            pass

        elif event_type == EventType.MAPCHANGE.value:
            print("MAPCHANGE")
            length = struct.unpack('<I', data[11:15])[0]
            mapname = data[15:15 + length].decode("utf-8")
            print(length, mapname)

            #if self.splits.splits[self.curr_split + 1].title ==
            self.curr_split += 1

        elif event_type == EventType.TIMER_RESET.value:
            self.timer_started = False # TODO: should be state enum or someshit, probably
            self.curr_split = 0

        elif event_type == EventType.TIMER_START.value:
            self.timer_started = True
            self.curr_split = 0

        elif event_type == EventType.BS_ALEAPOFFAITH.value:
            pass

    def ParseTime(self, data: bytes, offset: int):
        # print(f"ParseTime({data}, {offset})")
        hours = struct.unpack('<I', data[offset:offset + 4])[0]
        minutes = data[offset + 4]
        seconds = data[offset + 5]
        milliseconds = struct.unpack('<H', data[offset + 6:offset + 8])[0]
        # print(f"{hours}, {minutes}, {seconds}, {milliseconds}")
        curr_time = hours, minutes, seconds, milliseconds
        self.curr_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds, ).total_seconds()

        # self.curr_time = hours * 3600 + minutes * 60 + seconds + milliseconds/1000

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

if __name__ == "__main__":
    bsp = BunnysplitShit()
    bsp.ParseMessage(b'\x17\x04\x01\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00ba_tram3')
    sys.exit(1)

    q1 = posixmq.Queue("/bxt", serializer=RawSerializer)
    while True:
        while q1.qsize() > 0:
            try:
                msg = q1.get_nowait()
                print(msg)
                bsp.ParseMessage(msg)
            except:
                pass
