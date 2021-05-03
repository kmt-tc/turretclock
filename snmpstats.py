#!/usr/bin/env python3

# Statistics script for SNMP monitoring (e.g. Cacti)

# If the turretclock directory, configuration file, and database are all
# readable by the SNMP user or group, this script may be called directly.
# If not, sudo or something similar is required.

# This script produces the following statistics over the past db_stats_interval minutes:
#   - Average pendulum skew in uS
#   - Maximum pendulum skew in uS
#   - Minimum pendulum skew in uS
#   - Percentage of slow beats slower than "Poor" tolerance
#   - Percentage of slow beats faster than "Poor" tolerance but slower than "Fair" tolerance
#   - Percentage of beats within "Good" tolerance
#   - Percentage of fast beats faster than "Fair" tolerance but slower than "Poor" tolerance
#   - Percentage of fast beats faster than "Poor" tolerance 
#   - Average daily drift in s/day
#   - 95th percentile max
#   - 95th percentile min
#   - Average clock error in seconds

import sqlite3
from dbstore import dbopen, dbclose

import config as cfg

dbx = dbopen()      # Open the database
# Now I want tuples, because of adding in error data
# dbx.row_factory = lambda cursor, row: row[0]        # Produce a list, not a list of tuples
cur = dbx.cursor()
sql = "SELECT skew, error FROM beats WHERE beattype=1 AND timestamp >= Datetime('now', '-{} minutes', 'localtime') ORDER BY skew;".format(cfg.db_stats_interval)
cur.execute(sql)
rows = cur.fetchall()
skews = [x[0] for x in rows]
errs = [x[1] for x in rows]

avgskew = int(sum(skews)/len(skews))
print(avgskew)                                      # Average skew
print(max(skews))                                    # Maximum skew
print(min(skews))                                    # Minimum skew
print(round(100*len([element for element in skews if element < cfg.p_offset-cfg.p_tolerance2])/len(skews),1))       # Red- percent
print(round(100*len([element for element in skews if cfg.p_offset-cfg.p_tolerance2 <= element < cfg.p_offset-cfg.p_tolerance1])/len(skews),1))           # Yellow- percent
print(round(100*len([element for element in skews if abs(cfg.p_offset-element) <= cfg.p_tolerance1])/len(skews),1))        # Green percent
print(round(100*len([element for element in skews if cfg.p_offset+cfg.p_tolerance1 < element <= cfg.p_offset+cfg.p_tolerance2])/len(skews),1))            # Yellow+ percent
print(round(100*len([element for element in skews if element > cfg.p_offset+cfg.p_tolerance2])/len(skews),1))       # Red+ percent
print(round(-avgskew*86400/cfg.p_period,1))                 # Average daily skew over the past 5 minutes
print(skews[int(len(skews)*0.95)])                    # 95th percentile max
print(skews[int(len(skews)*0.05)])                    # 95th percentile min
print(sum(errs)/len(errs))                          # Average clock error

dbclose()

