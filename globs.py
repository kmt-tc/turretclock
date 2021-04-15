# global variables

from datetime import datetime
from queue import Queue
import config as cfg

clocktime = datetime.now()
realtime = datetime.now()
newclocktime = None
version = '2021033101'

try:
    cfg.ui_banner
except NameError:
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
avgsqltable = '''
        timestamp       TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW', 'localtime')),
        avg             REAL
'''

avg1Hsqltable = '''
        timestamp       TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW', 'localtime')),
        avg             REAL
'''

avg1Dsqltable = '''
        timestamp       TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW', 'localtime')),
        avg             REAL
'''

# Set up queues - FIXME make these set up only when modules are enabled
uiq = Queue()           # UI queue
dbq = Queue()     # Database queue
mqq = Queue()   # MQTT queue

temperature = 0
humidity = 0

driftavg = []
telemetry = []
