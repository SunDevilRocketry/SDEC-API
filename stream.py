# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import threading
import time

from typing import Dict, Any
from util import make_safe_number

# CONSTANTS
ORIGIN_STRING = "SDEC-API"
STREAM_VERSION_STRING = "1.0"


class Stream:
    def __init__(self):
        self.signal_broadcast_event = threading.Event()
        self.stream_mutex = threading.Lock()
        self.sequence_number = 0
        self.terminate = False
        self.data = None

    def sse_put_callback(self, messageType: str, timestamp: float, msg: dict[str, Any]):
        """
        Set up a message for all clients to broadcast.
        """
        with self.stream_mutex:
            self.data = {
                "origin": ORIGIN_STRING,
                "version": STREAM_VERSION_STRING,
                "timestamp": timestamp,
                "messageType": messageType,
                "payload": msg
            }
            self.sequence_number += 1
        self.signal_broadcast_event() # Only signal the events after releasing the mutex


    def sse_broadcast_callback(self):
        """
        Yields messages for the client with this request open.
        """
        last_seq_num = 0 # scoped to this instance
        
        # Send a message immediately on connect if one exists
        with self.stream_mutex:
            if self.data is not None:
                last_seq_num = self.sequence_number
                yield self.data

        # Wait for new messages to be put
        while not self.terminate:
            self.signal_broadcast_event.wait()
            with self.stream_mutex:
                if self.data is not None and self.sequence_number != last_seq_num:
                    last_seq_num = self.sequence_number
                    yield self.data