# Built-ins
import time

# IPC-related # TODO: fix up imports here
import ipcqueue.posixmq
from ipcqueue.serializers import RawSerializer
from ipcqueue import posixmq

# Qt related #
from PySide6.QtCore import QObject, Signal, Slot, QRunnable

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
        Worker thread for the Message Queue
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
                    # bsp.parse_message(msg)
                    self.signals.result.emit(msg)
                except posixmq.QueueError as e:
                    self.signals.error.emit(e)  # TODO: as the docstring says
                    print("Exception")
            else:
                time.sleep(0.01)  # CPU usage, be gone
