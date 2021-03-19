# Miscellaneous defs

from threading import Timer


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
