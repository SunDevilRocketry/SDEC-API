# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import threading
import time
import json

from typing import Dict, Any
from util import make_safe_number

# CONSTANTS
ORIGIN_STRING = "SDEC-API"
STREAM_VERSION_STRING = "1.0"
RATE_LIMITER_HZ = 30
RATE_LIMITER_PERIOD = 1.0 / RATE_LIMITER_HZ


class Stream:
    def __init__(self) -> None:
        self.stream_cond = threading.Condition()
        self.sequence_number = 0
        self.terminate = False
        self.data = None

    def sse_put_callback(self, messageType: str, timestamp: float, msg: dict[str, Any]):
        """
        Set up a message for all clients to broadcast.
        """

        with self.stream_cond:
            response = {
                "origin": ORIGIN_STRING,
                "version": STREAM_VERSION_STRING,
                "timestamp": timestamp,
                "messageType": messageType,
                "payload": msg
            }
            self.data = f"data: {json.dumps(response)}\n\n".encode("utf-8")
            self.sequence_number += 1
            self.stream_cond.notify_all()


    def sse_broadcast_callback(self):
        """
        Yields messages for the client with this request open.
        """
        last_seq_num = 0 # scoped to this instance
        last_time = 0
        
        # Send a message immediately on connect if one exists
        with self.stream_cond:
            if self.data is not None:
                last_seq_num = self.sequence_number
                data_to_yield = self.data
            else:
                data_to_yield = None
                
        if data_to_yield is not None:
            yield data_to_yield

        # Wait for new messages to be put
        while not self.terminate:
            with self.stream_cond:
                # Wait for sequence_number to change to avoid spurious wakeups
                while self.sequence_number == last_seq_num and not self.terminate:
                    self.stream_cond.wait()
                # delay the broadcast (yielding to other threads) if rate limiter
                # indicates that messages are coming in too fast
                curr_time = time.time()
                if RATE_LIMITER_PERIOD + last_time < curr_time:
                    # Release the lock if we have to wait for the timeout,
                    # then reacquire once we're back on the target rate.
                    self.stream_cond.release()
                    time.sleep( RATE_LIMITER_PERIOD + last_time - curr_time )
                    self.stream_cond.acquire()
                # end the broadcast entirely if the termination flag is
                if self.terminate:
                    break
                last_seq_num = self.sequence_number
                data_to_yield = self.data
            
            yield data_to_yield