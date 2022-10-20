from typing import List
from itertools import count
from dataclasses import dataclass, field
from dataclass_wizard import JSONWizard, json_field
from PySide6.QtCore import QObject
import datetime


@dataclass
class Split(QObject):
    title: str
    split_time: str
    best_time: str
    best_segment: str

    identifier: int = json_field("identifier", default_factory=count().__next__, dump=False)
    delta: float = json_field("delta", default=0, dump=False)
    time_this_run: datetime.timedelta = json_field("time_this_run", default=datetime.timedelta(), dump=False)


@dataclass
class Splits(JSONWizard):
    title: str
    category: str
    attempt_count: int
    finished_count: int
    splits: List[Split] = field(default_factory=list)
