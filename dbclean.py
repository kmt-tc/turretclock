#!/usr/bin/env python3

# Database cleanup script

# This is a very simple script that just drops everything from the database
# more than db_dumpinterval minutes old.

import sqlite3
from dbstore import dbopen, dbclose

import config as cfg

dbx = dbopen()      # Open the database
cur = dbx.cursor()
sql = "DELETE from beats WHERE timestamp < Datetime('now', '-{} minutes', 'localtime');".format(cfg.db_dump_interval)
cur.execute(sql)
dbx.commit()
cur.close()

dbclose()

