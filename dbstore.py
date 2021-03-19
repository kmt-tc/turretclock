# Database stuff

import sqlite3
from sqlite3 import Error

import config as cfg
import globs
from globs import dbq, uiq
from ui import debug

def dbopen():
    '''open the database
    '''
    global dbx
    dbx = None
    debug('Opening database', 2)
#    if cfg.ui_debugmod['db']: uiq.put(('Opening database', 'DEBUG', 2))
    try:
        dbx = sqlite3.connect(cfg.db_file)
#        dbx.isolation_level = 'EXCLUSIVE'                   # FIXME - this seems not to lock against other processes
#        dbx.execute('BEGIN EXCLUSIVE')
        sql = "CREATE TABLE IF NOT EXISTS beats ({});".format(globs.sqltable)
        cur = dbx.cursor()
        try:
            cur.execute(sql)
            dbx.commit()
        except Error as dberr:
            uiq.put(('Database table create error: {}'.format(dberr), 'ERR'))
    except Error as dberr:
        uiq.put(('Database open error: {}'.format(dberr), 'ERR'))
    return dbx

def dbclose():
    '''close the database
    '''
    global dbx
    dbx.close()

def dbstorebeat(beattype, delta, hz, skew):
    '''database storage routine:
        beattype = 1/arrive, 0/depart
        delta = delta since last beat, in uS
        hz = calculated Hz
        skew = skew from desired beat frequency
    '''
    global dbx, temperature, humidity
    sql = "INSERT INTO beats(beattype, delta, hz, skew, temperature, humidity) VALUES ({}, {}, {}, {}, {}, {})".format(beattype, delta, hz, skew, globs.temperature, globs.humidity)
    try: dbx
    except NameError: dbopen
    else:
        cur = dbx.cursor()
        try:
            debug('Executing SQL command {}'.format(sql), 3)
#            if cfg.ui_debugmod['db']: uiq.put(('Executing SQL command {}'.format(sql), 'DEBUG', 3))
            cur.execute(sql)
            dbx.commit()
        except Error as dberr:
            uiq.put(('Database write error: {}'.format(dberr), 'ERR'))

def dbD():
    '''database access thread
    '''
    debug('Database thread initialising')
#    if cfg.ui_debugmod['db']: uiq.put(('Database thread initialising', 'DEBUG'))
    dbopen()
    while True:
        item = dbq.get()
        dbstorebeat(*item)

