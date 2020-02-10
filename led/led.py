#!/usr/bin/python
#coding: utf-8

import time
import json
import sys
import paho.mqtt.client as mqtt
from uuid import getnode as get_mac

from jsonschema import validate
from jsonschema import exceptions
from lib.neo_pixel_string import *
from random import *

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
QOS_STATE_PUBLISH = 1
RETAIN_STATE_PUBLISH = False

mac = get_mac() # определение мак-адреса устройства для формирования уникального ID каждого mqtt клиента

led_topic_set = "myhome/smartmirror/led/set"
led_topic_status = "myhome/smartmirror/led/status"

syscom_topic_set = "myhome/smartmirror/syscom/set"
syscom_topic_status = "myhome/smartmirror/syscom/status"

audio_topic_set = "myhome/smartmirror/audio/set"
audio_topic_status = "myhome/smartmirror/audio/status"

# LED strip configuration:
LED_COUNT      = 160      # Number of LED pixels.
LED_PIN        = 21      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)



loopflag = False
animation = 'none'

full_state_schema = {
    "type" : "object",
    "properties" : {
        "state" : {"enum" : ["ON", "OFF"]},
        "effect" : {"enum" : ["none", "rainbow", "rainbowcycle", "theaterchaserainbow", "colorwipe", "theaterchase"]},
        "brightness" : {"type": "number", "minimum": 0, "maximum": 255 },
        "color": {
            "type" : "object",
            "properties" : {
                "r" : {"type": "number", "minimum": 0, "maximum": 255 },
                "g" : {"type": "number", "minimum": 0, "maximum": 255 },
                "b" : {"type": "number", "minimum": 0, "maximum": 255 }
            },
            "required": ["r", "g", "b"]
        }
    }
}

neopixelstring = None
topic = "myhome/smartmirror/led"

def on_connect(client, userdata, flags, rc):
    m = "Connected flags" + str(flags) + "result code " \
        + str(rc) + "client1_id " + str(client)
    print(m)

# This is an interface that is compatible with Home Assistant MQTT JSON Light
def on_message_full_state(client, userdata, message):
    global json_message, loopflag, animation
    json_message = str(message.payload.decode("utf-8"))
    print("message received: ", json_message)

    try:
        data = json.loads(json_message)
        validate(data, full_state_schema)
        if (data.has_key('state')):
            print("got state " + data['state'])
            if (data['state'] == 'OFF'):
                neopixelstring.all_off()
                animation = 'none'
            else:
                neopixelstring.all_on()
                if (data.has_key('brightness')):
                    neopixelstring.set_brightness(data['brightness'])

                if (data.has_key('color')):
                    # For some reason we need to switch r and g. Don't get it
                    color = Color(data['color']['r'], data['color']['g'], data['color']['b'])
                    neopixelstring.set_color(color)
                    
                if (data.has_key('effect')):
                    loopflag = True
                    if (data['effect'] == 'none'):
                        animation = 'none'
                    elif (data['effect'] == 'rainbow'):
                        animation = 'rainbow'
                    elif (data['effect'] == 'rainbowcycle'):
                        animation = 'rainbowcycle'
                    elif (data['effect'] == 'theaterchaserainbow'):
                        animation = 'theaterchaserainbow'
                    elif (data['effect'] == 'colorwipe'):
                        animation = 'colorwipe'
                    elif (data['effect'] == 'theaterchase'):
                        animation = 'theaterchase'
                else:
                    animation = 'none'
                    loopflag = False

        publish_state(client)

    except exceptions.ValidationError:
        print "Message failed validation"
    except ValueError:
        print "Invalid json string"

def publish_state(client):
    json_state = {
        "brightness": neopixelstring.get_brightness(),
        "state": "OFF" if neopixelstring.is_off() else "ON",
        "effect": animation,
        "color": {
            "r": neopixelstring.get_color()['red'],
            "g": neopixelstring.get_color()['green'],
            "b": neopixelstring.get_color()['blue']
        }
    }

    (status, mid) = client.publish(topic_status, json.dumps(json_state), \
        QOS_STATE_PUBLISH, RETAIN_STATE_PUBLISH)

    if status != 0:
        print("Could not send state")

# Main program logic follows:
if __name__ == '__main__':
    neopixelstring = NeoPixelString(LED_COUNT, LED_PIN)
    mac = get_mac()

#    if (len(sys.argv) != 2):
#         print("usage: " + sys.argv[0] + " <topic>\n")
#         sys.exit(0)
#
#    topic = sys.argv[1]
    topic_set = topic + "/set"
    topic_status = topic + "/status"
    print("> using topic '"+topic+"'")
    print("> subscribing to '" + topic_set + "'")

    client1 = mqtt.Client(str(mac) + "-python_client")
    client1.on_connect = on_connect

    # Home Assistant compatible
    client1.message_callback_add(topic_set, on_message_full_state)
    time.sleep(1)

    client1.connect(BROKER_ADDRESS, BROKER_PORT)
    client1.loop_start()
    client1.subscribe(topic_set)

    justoutofloop = False
    print ('Press Ctrl-C to quit.')
    while True:
        if loopflag and animation != 'none':
            justoutofloop = True
            if animation == 'rainbow':
                neopixelstring.rainbow()
            elif (animation == 'rainbowcycle'):
               neopixelstring.rainbowCycle()
            elif (animation == 'theaterchaserainbow'):
               neopixelstring.theaterChaseRainbow()
            elif (animation == 'colorwipe'):
               neopixelstring.colorWipe(Color(randint(0,255), randint(0,255), randint(0,255)))
            elif (animation == 'theaterchase'):
               neopixelstring.theaterChase(Color(randint(0,127), randint(0,127), randint(0,127)))
        if not loopflag and justoutofloop:
            justoutofloop = False
            client1.publish(topic, json_message, 0, False)
        time.sleep(.1)

    # This should happen but it doesnt because CTRL-C kills process.
    # Fix later
    print "Disconnecting"
    publish_state(client1)
    client1.disconnect()
    client1.loop_stop()
