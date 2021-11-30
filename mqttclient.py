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
    # Sort the telemetry data and clear the global
    stelemetry = sorted(globs.telemetry)
    globs.telemetry = []
    try:
        avgskew = sum(stelemetry)/len(stelemetry)
    except ZeroDivisionError:                               # This will happen when the clock isn't running
        return
    drift = -avgskew*86400/cfg.p_period
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
            '1mdrift' : globs.driftavgs[0],
            '1hdrift' : globs.driftavgs[1],
            '1ddrift' : globs.driftavgs[2],
            '95max' : int(stelemetry[int(len(stelemetry)*0.95)]),
            '95min' : int(stelemetry[int(len(stelemetry)*0.05)]),
            'temperature' : globs.temperature,
            'humidity' : globs.humidity,
    }
    debug('MQTT publish: {}/telemetry: {}'.format(cfg.mqtt_topicbase, payload), 3)
    payload = json.dumps(payload)
    mqclient.publish('{}/telemetry'.format(cfg.mqtt_topicbase), payload=payload, qos=0, retain=False)

def mqttD():
    '''MQTT broker thread'''
    debug('MQTT thread initialising')
    global mqclient, watchdog, db2x
    mqclient = mqtt.Client()
    mqclient.connect(cfg.mqtt_broker, cfg.mqtt_port, cfg.mqtt_keepalive)
    mqclient.loop_start()
    if cfg.mqtt_telemetry:
        # Set a watchdog for publishing telemetry data
        watchdog = Watchdog(cfg.mqtt_telemetry_interval, mqttTelemetry)
    while True:
        item = mqq.get()
        payload = json.dumps(item[1])
        mqclient.publish('{}/{}'.format(cfg.mqtt_topicbase, item[0]), payload=payload, qos=0, retain=False)
        debug('MQTT publish: {}/{}: {}'.format(cfg.mqtt_topicbase, item[0], item[1]), 3)

