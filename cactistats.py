#!/usr/bin/env python3

# Thos script returns the average skew from the last five minutes as well as the max and min

import sqlite3
from dbstore import dbopen, dbclose

import config as cfg

dbx = dbopen()      # Open the database
dbx.row_factory = lambda cursor, row: row[0]        # Produce a list, not a list of tuples
cur = dbx.cursor()
sql = "SELECT skew FROM beats WHERE beattype=1 AND timestamp >= Datetime('now', '-5 minutes', 'localtime');"
cur.execute(sql)
rows = cur.fetchall()

avgskew = int(sum(rows)/len(rows))
print(avgskew)                                      # Average skew
print(max(rows))                                    # Maximum skew
print(min(rows))                                    # Minimum skew
print(round(100*len([element for element in rows if element < cfg.p_offset-cfg.p_tolerance2])/len(rows),1))       # Red- percent
print(round(100*len([element for element in rows if cfg.p_offset-cfg.p_tolerance2 <= element < cfg.p_offset-cfg.p_tolerance1])/len(rows),1))           # Yellow- percent
print(round(100*len([element for element in rows if abs(cfg.p_offset-element) <= cfg.p_tolerance1])/len(rows),1))        # Green percent
print(round(100*len([element for element in rows if cfg.p_offset+cfg.p_tolerance1 < element <= cfg.p_offset+cfg.p_tolerance2])/len(rows),1))            # Yellow+ percent
print(round(100*len([element for element in rows if element > cfg.p_offset+cfg.p_tolerance2])/len(rows),1))       # Red+ percent
print(round(-avgskew*86400/cfg.p_period,1))                 # Average daily skew over the past 5 minutes

dbclose()

