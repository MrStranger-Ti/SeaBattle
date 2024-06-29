import threading
import time
from datetime import datetime, timedelta

import settings


class MessageScheduler(threading.Thread):
    def __init__(self, sleep_time: int):
        super().__init__()
        self.sleep_time: int = sleep_time
        self.lock = threading.Lock()

    def run(self) -> None:
        while True:
            time.sleep(self.sleep_time)

            with self.lock:
                for state in settings.STATES.values():
                    if state.buffer_messages and datetime.now() - state.last_buffer_update_time > timedelta(seconds=self.sleep_time):
                        state.clear_buffer()


def start_message_scheduler() -> None:
    thread = MessageScheduler(settings.CLEAR_BUFFER_TIME)
    thread.start()
