from typing import List
from itertools import count
from dataclasses import dataclass, field
from dataclass_wizard import JSONWizard
from PySide6.QtCore import QObject

import datetime

@dataclass
class Split(QObject):
    title: str
    split_time: str
    best_time: str
    best_segment: str

    identifier: int = field(default_factory=count().__next__)
    delta: float = field(default=0) # TODO: ←&↓ These in seperate subclass? dunno if possible tho because of QObject bs tho...
    time_this_run: datetime.timedelta = field(default=datetime.timedelta())

    # @Property(str, notify=mrdat)
    # def get_title(self):
    #     return self.title

@dataclass
class Splits(JSONWizard):
    title: str
    category: str
    attempt_count: int
    finished_count: int
    splits: List[Split] = field(default_factory=list)