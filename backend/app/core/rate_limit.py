import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class InMemoryRateLimiter:
    """Simple fixed-window rate limiter for single-process deployments."""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            queue = self._requests[key]
            while queue and queue[0] < cutoff:
                queue.popleft()

            if len(queue) >= limit:
                return False

            queue.append(now)
            return True


rate_limiter = InMemoryRateLimiter()
