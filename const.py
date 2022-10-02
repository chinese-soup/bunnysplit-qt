from enum import Enum

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
