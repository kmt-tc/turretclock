# global variables

from datetime import datetime
from queue import Queue
import config as cfg

clocktime = datetime.now()
realtime = datetime.now()
newclocktime = None
version = '2020030301'

cfg.ui_banner = 'Clock Monitor v{}'.format(version)  # This variable needs to exist, others can be checked after UI start
beatbanner = "[ Waiting for first beat ]"
driftbanner = "[ Waiting for drift data ]"
sqltable = '''
        timestamp       TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW', 'localtime')),
        beattype        INTEGER,
        delta           INTEGER,
        hz              REAL,
        skew            INTEGER,
        temperature     REAL,
        humidity        REAL
'''

# Database queue
dbq = Queue()           # Database queue
uiq = Queue()           # UI queue

temperature = 0
humidity = 0

driftavg = []
