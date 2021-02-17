from kafka import KafkaConsumer, KafkaProducer
from threading import Thread, Event
from six.moves.queue import LifoQueue
#from queue import LifoQueue
import json
import requests
import time
import numpy as np
import os
import subprocess
from qtpy.QtCore import Slot, Qt
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

import logging

# Silence extremely noisy kafka logs
logger = logging.getLogger("kafka")
logger.setLevel("WARNING")

# TODO: Implement new signals...
# Configuration change
# Status change
# Send actions acknowledge
# Send actions disable

ALARMS = {
    "OK": 0,
    "MINOR": 1,
    "MAJOR": 2,
    "INVALID": 3,
    "DISCONNECTED": 4,
    "MINOR_ACK": 5,
    "MAJOR_ACK": 6,
    "UNDEFINED": 7,
    "UNDEFINED_ACK": 8
}


class Connection(PyDMConnection):
    """
    Connection plugin for the kafka alarm datasource. 

    """

    def __init__(self, channel, address, protocol=None, parent=None):
        # type: (channel: _, address: str, protocal: str, parent: _)
        super(Connection, self).__init__(channel, address, protocol, parent)
        self.address = address
        self._update_queue = LifoQueue(maxsize=1)
        self._exit_event = Event()
        self._configuration = channel.alarm_configuration

        kafka_url = os.getenv("KAFKA_URL")
        alarm_configuration = channel.alarm_configuration

        try:
            self.consumer = KafkaConsumer(
                alarm_configuration,
                bootstrap_servers=[kafka_url],
                enable_auto_commit=False,
                key_deserializer=lambda x: x.decode('utf-8')
            )


            self.producer = KafkaProducer(bootstrap_servers=[kafka_url], value_serializer=lambda v: json.dumps(v).encode('utf-8'), key_serializer=lambda v: v.encode('utf-8'))

            if self.consumer.bootstrap_connected():

                self.connection_state_signal.emit(True)

                # initialize so can seek to beginning
                while not self.consumer._client.poll(): continue

                self.consumer.seek_to_beginning()

                self._monitor_thread = Thread(
                    target=self._monitor,
                )
                self._monitor_thread.start()

        except Exception as e:
            print(e)

        self.connected = True
        self.add_listener(channel)


    def _monitor(self, delay=0.1):
        for message in self.consumer:
            if self._exit_event.is_set():
                break

            if message.key == "state:/{}".format(self.address):
                value = json.loads(message.value.decode("utf-8"))
                self.send_new_severity(value["severity"])

                if value.get("message"):
                    self.send_new_value(value["message"])

    def close(self):
        self._exit_event.set()
        self._monitor_thread.join()
        self.send_connection_state(False)

    def send_new_value(self, value):
        self.new_value_signal[str].emit(value)

    def send_new_severity(self, value):
        self.new_severity_signal.emit(ALARMS[value])

    def send_connection_state(self, conn): 
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self.send_connection_state(conn=True)
        channel.value_signal[bool].connect(self.put_value, Qt.QueuedConnection)

    def acknowledge(self):
        self.producer.send(self._configuration, key = "command:/{}".format(self.address), value={"user": "pydm", "host": "", "command": "acknowledge"})

    def unacknowledge(self):
        self.producer.send(self._configuration, key = "command:/{}".format(self.address), value={"user": "pydm", "host": "", "command": "unacknowledge"})

    def disable(self):
        pass

    def put_value(self, value):
        if value:
            self.acknowledge()
        else:
            self.unacknowledge()



class AlarmPlugin(PyDMPlugin):
    protocol = "alarm"
    connection_class = Connection