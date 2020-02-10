#!/usr/bin/python
# coding: utf-8

# отслеживание состояние датчика движения и отправка сообщений о начале движения или его окончании.
import paho.mqtt.client as mqtt
from uuid import getnode as get_mac
import RPi.GPIO as GPIO         # стандартная библиотека по работе с GPIO (физические выводы) на Raspberry
import time
import json

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
QOS_STATE_PUBLISH = 1
RETAIN_STATE_PUBLISH = False

GPIO.setmode(GPIO.BCM)
PIR_PIN = 11 # номер GPIO, к которому подключен сенсор движения
SHUTOFF_DELAY = 45 # время в секундах, когда датчик не отключается при отсуствии движения (hold time) 
CLIENT_NAME = "pir_sensor_docker"

mac = get_mac()

client = mqtt.Client(str(mac) + CLIENT_NAME)

led_topic_set = "myhome/smartmirror/led/set"
led_topic_status = "myhome/smartmirror/led/status"

syscom_topic_set = "myhome/smartmirror/syscom/set"
syscom_topic_status = "myhome/smartmirror/syscom/status"

audio_topic_set = "myhome/smartmirror/audio/set"
audio_topic_status = "myhome/smartmirror/audio/status"

def main():
    GPIO.setup(PIR_PIN, GPIO.IN)
    turned_off = False
    last_motion_time = time.time()
    print ("Программа начала отслеживать состояние датчика \nСтарт. Движение _НЕ_ ОБНАРУЖЕНО")
    client.on_connect = on_connect

    while True:
        if GPIO.input(PIR_PIN):
            last_motion_time = time.time()
            if turned_off:
                turned_off = False
                motion_on()
        else:
            if not turned_off and time.time() > (last_motion_time + SHUTOFF_DELAY):
                turned_off = True
                motion_off()
        time.sleep(.1)
 
def motion_on():      # что делать, если движение ОБНАРУЖЕНО 
    print ("Движение ОБНАРУЖЕНО")
    client.connect(BROKER_ADDRESS, BROKER_PORT)
    client.publish(led_topic_set, json.dumps({"state":"ON"}), QOS_STATE_PUBLISH, RETAIN_STATE_PUBLISH)
    client.publish(audio_topic_set, json.dumps({"CMD":"MOTION_ON"}), QOS_STATE_PUBLISH, RETAIN_STATE_PUBLISH)
    client.disconnect()
 
def motion_off():     # что делать, если движение НЕ ОБНАРУЖЕНО 
    print ("Движение _НЕ_ ОБНАРУЖЕНО")
    client.connect(BROKER_ADDRESS, BROKER_PORT)
    client.publish(led_topic_set, json.dumps({"state":"OFF"}), QOS_STATE_PUBLISH, RETAIN_STATE_PUBLISH)
    client.publish(audio_topic_set, json.dumps({"CMD":"MOTION_OFF"}), QOS_STATE_PUBLISH, RETAIN_STATE_PUBLISH)
    client.disconnect()

# Отображаем подключились ли к серверу mqtt
def on_connect(client, userdata, flags, rc):            # функция on_connect не срабатывает (не выводит print). Тоесть, не получает от от mqtt сервера  А в led.py выводит.
    m = "Connected flags" + str(flags) + "result code " \
        + str(rc) + "client_id " + str(client)
    print(m)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        GPIO.cleanup()
