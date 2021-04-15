# Miscellaneous defs

from threading import Timer
from math import isclose, sqrt

# Watchdog timer from Sergiy Belozorov
# https://stackoverflow.com/questions/16148735/how-to-implement-a-watchdog-timer-in-python

class Watchdog(Exception):
   def __init__(self, timeout, userHandler=None):  # timeout in seconds
       self.timeout = timeout
       self.handler = userHandler if userHandler is not None else self.defaultHandler
       self.timer = Timer(self.timeout, self.handler)
       self.timer.start()

   def reset(self):
       self.timer.cancel()
       self.timer = Timer(self.timeout, self.handler)
       self.timer.start()

   def stop(self):
       self.timer.cancel()

   def defaultHandler(self):
       raise self


# Largest Remainder/Parliamentary rounding method, to ensure everything adds up to 100%
# Varun Vohra / Mark Ransom - https://stackoverflow.com/a/34959983

def error_gen(actual, rounded):
    divisor = sqrt(1.0 if actual < 1.0 else actual)
    return abs(rounded - actual) ** 2 / divisor

def round_to_100(percents):
    if not isclose(sum(percents), 100):
        raise ValueError
    n = len(percents)
    rounded = [int(x) for x in percents]
    up_count = 100 - sum(rounded)
    errors = [(error_gen(percents[i], rounded[i] + 1) - error_gen(percents[i], rounded[i]), i) for i in range(n)]
    rank = sorted(errors)
    for i in range(up_count):
        rounded[rank[i][1]] += 1
    return rounded

