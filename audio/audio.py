#!/usr/bin/python
# coding: utf-8

"""
Программа подключается к mqtt брокеру и подписывается на ветку .../set.
При получении соббщения, сверяет соотвествует ли структуре словаря в audio_commands.py 
и обрабатывает (проигрывает соответствующий файл при помощи плеера omxplayer).
При проигрывании, файлы берутся с папки audio/[ru или ua или en]/ в зависимости от языка,
который указан в файле index.js (см "pathToConfig")
После проигрывания - отмечает выполнение команды в ветку .../status.
"""

from audio_commands import *
from subprocess import call
import paho.mqtt.client as mqtt     # библиотека по работе с mqtt протоколом
import time
import json
import os

mqtt_server_host = "localhost"
mqtt_server_port = 1883
mqtt_keepalive = 60

pathToConfig = '/home/pi/MagicMirror/config/config.js'  # место нахождения файла config.js со значением языка
LanguageAll = ['uk', 'ru', 'en','ar']                   # возможніе языки

class Device:
    global lang_config, command
    def __init__(self, name):
        self.name = name
    
    # проигрывание файла - путь формируется из значения языка и имени файла. Имя файла - это название команды в нижнем индексе.
    def play_audio(self):
        print('/audio/' + lang_config + '/' + command.lower() + '.wav')
        call(['aplay', '/audio/' + lang_config + '/' + command.lower() + '.wav'])

    def motion_on(self):
        self.play_audio()

    def motion_off(self):
        self.play_audio()

    def reboot(self):
        self.pplay_audio()

    def shutdown(self):
        self.play_audio()

    def success(self):
        self.play_audio()

    def fail(self):
        self.play_audio()

    def factory_settings(self):
        self.play_audio()
		
class DeviceCommandProcessor:
    commands_topic = ""
    processed_commands_topic = ""
    active_instance = None

    def __init__(self, name, device):
        self.name = name
        self.device = device
        DeviceCommandProcessor.commands_topic = \
            "myhome/smartmirror/{}/set".format(self.name)
        DeviceCommandProcessor.processed_commands_topic = \
            "myhome/smartmirror/{}/status".format(self.name)
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)
        DeviceCommandProcessor.active_instance = self
        self.client.on_connect = DeviceCommandProcessor.on_connect
        self.client.on_message = DeviceCommandProcessor.on_message
        self.client.connect(host=mqtt_server_host,
                            port=mqtt_server_port,
                            keepalive=mqtt_keepalive)

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        print("Result from connect: {}".format(
            mqtt.connack_string(rc)))
        # Проверяем, получено ли при подключении от сервера CONNACK_ACCEPTED код (подтвреждающий успешное подключение)
        if rc == mqtt.CONNACK_ACCEPTED:
            # Подписываемся на соотвествующую тему mqtt
            client.subscribe(
                DeviceCommandProcessor.commands_topic, 
                qos=2)

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        print("I've subscribed with QoS: {}".format(
            granted_qos[0]))

    @staticmethod
    def on_message(client, userdata, msg):
        global command
        if msg.topic == DeviceCommandProcessor.commands_topic:
            print("Received message payload: {0}".format(str(msg.payload)))
            try:
                message_dictionary = json.loads(msg.payload)
                if COMMAND_KEY in message_dictionary:
                    command = message_dictionary[COMMAND_KEY]
                    device = DeviceCommandProcessor.active_instance.device
                    is_command_executed = False
                    command_methods_dictionary = {
                        CMD_MOTION_ON: lambda: device.motion_on(),
                        CMD_MOTION_OFF: lambda: device.motion_off(),
                        CMD_REBOOT: lambda: device.reboot(),
                        CMD_SHUTDOWN: lambda: device.shutdown(),
                        CMD_SUCCESS: lambda: device.success(),
                        CMD_FAIL: lambda: device.fail(),
                        CMD_FACTORY_SETTINGS: lambda: factory_settings(),
                    }
                    if command in command_methods_dictionary:
                        method = command_methods_dictionary[command]
                        # Вызов метода
                        method()
                        is_command_executed = True
                    if is_command_executed:
                        DeviceCommandProcessor.active_instance.publish_executed_command_message(
                            message_dictionary)
                    else:
                        print("I've received a message with an unsupported command.")
            except ValueError:
                # сообщение не в формате словаря
                # JSON объект не может быть декодирован из сообщения
                print("I've received an invalid message.")

    def publish_executed_command_message(self, message):
        response_message = json.dumps({
            SUCCESFULLY_PROCESSED_COMMAND_KEY:
                message[COMMAND_KEY]})
        result = self.client.publish(
            topic=self.__class__.processed_commands_topic,
            payload=response_message)
        return result

    def process_incoming_commands(self):
        self.client.loop()

# считываем один раз установленный язык из файла config.js
def readLang(): #
    f = open(pathToConfig)
    language = 'language'
    line = f.readline()
    global lang_config
    while line:
        if language in line:
            for i in LanguageAll:
                if i in line:
                    lang_config = i
                    break
            break
        line = f.readline()

if __name__ == "__main__":
    device = Device("audio")
    device_command_processor = DeviceCommandProcessor("audio", device)
    readLang()

    # Обрабатываем сообщения и команды раз в 1 секунду
    while True:
        device_command_processor.process_incoming_commands()
        time.sleep(1)
