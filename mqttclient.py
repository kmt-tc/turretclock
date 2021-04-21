import config as cfg
import paho.mqtt.client as mqtt

import time
import json
import globs
from globs import dbq, uiq, mqq
from ui import debug
from defs import Watchdog, error_gen, round_to_100

import sqlite3
from sqlite3 import Error

def mqttTelemetry():
    '''publish telemetry data to MQTT broker every mqtt_telemetry_interval seconds'''
    global mqclient, watchdog
    # Reset the watchdog
    watchdog.reset()
#    watchdog = Watchdog(cfg.mqtt_telemetry_interval, mqttTelemetry)
    # Sort the telemetry data and clear the global
    stelemetry = sorted(globs.telemetry)
    globs.telemetry = []
    try:
        avgskew = sum(stelemetry)/len(stelemetry)
    except ZeroDivisionError:                               # This will happen when the clock isn't running
        return
    drift = -avgskew*86400/cfg.p_period
    avgs = sqlaverages(drift)
    percents = round_to_100([
        100*len([element for element in stelemetry if element < cfg.p_offset-cfg.p_tolerance2])/len(stelemetry),
        100*len([element for element in stelemetry if cfg.p_offset-cfg.p_tolerance2 <= element < cfg.p_offset-cfg.p_tolerance1])/len(stelemetry),
        100*len([element for element in stelemetry if abs(cfg.p_offset-element) <= cfg.p_tolerance1])/len(stelemetry),
        100*len([element for element in stelemetry if cfg.p_offset+cfg.p_tolerance1 < element <= cfg.p_offset+cfg.p_tolerance2])/len(stelemetry),
        100*len([element for element in stelemetry if element > cfg.p_offset+cfg.p_tolerance2])/len(stelemetry)
    ])
    payload = {
            'interval' : cfg.mqtt_telemetry_interval,
            'avgskew' : avgskew,
            'maxskew' : int(stelemetry[-1]),
            'minskew' : int(stelemetry[0]),
            'bad-' : percents[0],
            'warn-' : percents[1],
            'good' : percents[2],
            'warn+' : percents[3],
            'bad+' : percents[4],
            'drift' : round(drift,1),
            '1hdrift' : avgs[0],
            '1ddrift' : avgs[1],
            '1wdrift' : avgs[2],
            '95max' : int(stelemetry[int(len(stelemetry)*0.95)]),
            '95min' : int(stelemetry[int(len(stelemetry)*0.05)]),
            'temperature' : globs.temperature,
            'humidity' : globs.humidity,
    }
    debug('MQTT publish: {}/telemetry: {}'.format(cfg.mqtt_topicbase, payload), 3)
    payload = json.dumps(payload)
    mqclient.publish('{}/telemetry'.format(cfg.mqtt_topicbase), payload=payload, qos=0, retain=False)

def sqlaverages(drift):
    '''compute/maintain the hourly, daily, weekly rolling averages'''
    debug('sqlaverages called')
    db2x = dbopen()
    db2x.row_factory = lambda cursor, row: row[0]        # Produce a list, not a list of tuples
    cur = db2x.cursor()
    # Look to see if the current pool has gotten two hours old
    sql = "SELECT COUNT(avg) FROM avg WHERE timestamp < Datetime('now', '-2 hours', 'localtime');"
    cur.execute(sql)
    count = cur.fetchone()
    if count > 0:       # The oldest entries are more than two hours old, so consolidate everything >1 hour old
        sql = "SELECT AVG(avg) FROM avg WHERE timestamp < Datetime('now', '-1 hour', 'localtime') AND timestamp >= Datetime('now', '-121 minutes', 'localtime');"
        cur.execute(sql)
        row = cur.fetchone()
        sql = "INSERT INTO avg1H(avg) VALUES ({})".format(row)
        cur.execute(sql)
        sql = "DELETE FROM avg WHERE timestamp < Datetime('now', '-1 hour', 'localtime');"
        cur.execute(sql)
    # Store the current drift
    sql = "INSERT INTO avg(avg) VALUES ({})".format(drift)
    cur.execute(sql)
    db2x.commit()
    # Move hourly averages into daily if they are more than 48 hours old (sql query is for -47 hours
    # because the above consolidation results in timestamps one hour later than the data)
    sql = "SELECT COUNT(avg) FROM avg1H WHERE timestamp < Datetime('now', '-47 hours', 'localtime');"
    cur.execute(sql)
    count = cur.fetchone()
    if count > 0:       # The oldest entries are more than two days old, so consolidate into avg1D
        sql = "SELECT AVG(avg) FROM avg1H WHERE timestamp < Datetime('now', '-23 hours', 'localtime') AND timestamp >= Datetime('now', '-48 hours', 'localtime');"
        cur.execute(sql)
        row = cur.fetchone()
        sql = "INSERT INTO avg1D(avg) VALUES ({})".format(row)
        cur.execute(sql)
        sql = "DELETE FROM avg1H WHERE timestamp < Datetime('now', '-23 hours', 'localtime');"
        cur.execute(sql)
    # Drop data from daily if it's more than one week old
    sql = "DELETE FROM avg1D WHERE timestamp < Datetime('now', '-6 days', 'localtime');"
    cur.execute(sql)
    db2x.commit()
    # Compute the 1 hour average
    sql = "SELECT AVG(avg) FROM avg WHERE timestamp >= Datetime('now', '-1 hours', 'localtime');"
    cur.execute(sql)
    avg1h = cur.fetchone()
    # Compute the 1 day average
    sql = "SELECT AVG(avg) FROM avg1H WHERE timestamp >= Datetime('now', '-23 hours', 'localtime');"
    cur.execute(sql)
    avg1d = cur.fetchone()
    # Need to know how old the oldest entry in avg is, to weight properly
    sql = "SELECT (strftime('%s', 'now', 'localtime') - strftime('%s', timestamp)) FROM avg ORDER BY timestamp LIMIT 1;"
    cur.execute(sql)
    oldest = cur.fetchone()
    sql = "SELECT AVG(avg) FROM avg;"
    cur.execute(sql)
    avg1d2 = cur.fetchone()
    avg1d = (23*avg1d + (oldest/3600)*avg1d2)/(23+(oldest/3600))
#    if len(rows2) > 0:
#        rows.append(sum(rows2)/len(rows2))
#    avg1d = (sum(rows)+avg1h)/(len(rows)+1)
    # Compute the 1 week average
    # FIXME apply the same logic to weekly if this works
    sql = "SELECT avg FROM avg1D"
    cur.execute(sql)
    rows = cur.fetchall()
    sql = "SELECT avg FROM avg1H WHERE timestamp < Datetime('now', '-1 day', 'localtime');"
    cur.execute(sql)
    rows2 = cur.fetchall()
    if len(rows2) > 0:
        rows.append(sum(rows2)/len(rows2))
    avg1w = (sum(rows)+avg1d)/(len(rows)+1)
    debug('Computed averages {} {} {}'.format(avg1h, avg1d, avg1w),2)
    db2x.close()
    return (avg1h, avg1d, avg1w)

def dbopen():
    '''open the database
    '''
    debug('Opening moving averages database')
    try:
        db2x = sqlite3.connect(cfg.db_file)
    except Error as dberr:
        uiq.put(('Database open error: {}'.format(dberr), 'ERR'))
    return db2x

def dbinit():
    '''initialise the database
    '''
    global db2x
    db2x = None
    debug('Initialising moving averages database')
    try:
        db2x = sqlite3.connect(cfg.db_file)
        sql = "CREATE TABLE IF NOT EXISTS avg1H ({});".format(globs.avg1Hsqltable)
        cur = db2x.cursor()
        try:
            cur.execute(sql)
            db2x.commit()
        except Error as dberr:
            uiq.put(('Database table create error: {}'.format(dberr), 'ERR'))
        sql = "CREATE TABLE IF NOT EXISTS avg1D ({});".format(globs.avg1Dsqltable)
        cur = db2x.cursor()
        try:
            cur.execute(sql)
            db2x.commit()
        except Error as dberr:
            uiq.put(('Database table create error: {}'.format(dberr), 'ERR'))
        sql = "CREATE TABLE IF NOT EXISTS avg ({});".format(globs.avgsqltable)
        cur = db2x.cursor()
        try:
            cur.execute(sql)
            db2x.commit()
        except Error as dberr:
            uiq.put(('Database table create error: {}'.format(dberr), 'ERR'))
    except Error as dberr:
        uiq.put(('Database open error: {}'.format(dberr), 'ERR'))
    db2x.close()

def mqttD():
    '''MQTT broker thread'''
    debug('MQTT thread initialising')
    global mqclient, watchdog, db2x
    mqclient = mqtt.Client()
    mqclient.connect(cfg.mqtt_broker, cfg.mqtt_port, cfg.mqtt_keepalive)
    mqclient.loop_start()
    if cfg.mqtt_telemetry:
        # Initialise the database
        dbinit()
        # Set a watchdog for publishing telemetry data
        watchdog = Watchdog(cfg.mqtt_telemetry_interval, mqttTelemetry)
    while True:
        item = mqq.get()
        payload = json.dumps(item[1])
        mqclient.publish('{}/{}'.format(cfg.mqtt_topicbase, item[0]), payload=payload, qos=0, retain=False)
        debug('MQTT publish: {}/{}: {}'.format(cfg.mqtt_topicbase, item[0], item[1]), 3)

