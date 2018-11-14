#!/usr/bin/python

import binascii
import struct
import sys
from threading import Thread, Lock
import time
import traceback
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import serial

# some const
SERVER_HOST = "192.168.1.99"
SERVER_PORT = 502

# set vars
th_lock = Lock()
ts = 0
tm_1 = 0.0
vol_c_1 = 0


# some class
class FloatModbusClient(ModbusClient):
    def read_float(self, address, number=1):
        reg_l = self.read_holding_registers(address, number * 2)
        if reg_l:
            return [utils.decode_ieee(f) for f in utils.word_list_to_long(reg_l)]
        else:
            return None

    def write_float(self, address, floats_list):
        b32_l = [utils.encode_ieee(f) for f in floats_list]
        b16_l = utils.long_list_to_word(b32_l)
        return self.write_multiple_registers(address, b16_l)


# some function
def polling_thread():
    global ts, tm_1, vol_c_1
    # init modbus client
    c = FloatModbusClient(host=SERVER_HOST, port=SERVER_PORT, unit_id=0xFF, auto_open=True)
    # polling loop
    while True:
        # read ts
        try:
            _ts =  c.read_holding_registers(28)[0]
            with th_lock:
                ts = _ts
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # read tm 1
        try:
            _tm_1 = c.read_float(512)[0]
            with th_lock:
                tm_1 = _tm_1
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # read gas corrected volume (gas volume converter 1)
        try:
            _vol_c_1 = utils.word_list_to_long(c.read_holding_registers(2634, 2))[0]
            with th_lock:
                vol_c_1 = _vol_c_1
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # 1s before next polling
        time.sleep(1.0)

# some class
class ArduinoCommandSerial(serial.Serial):
    def send_cmd(self, cmd, echo=False):
        # flush rx buffer
        self.read(self.inWaiting())
        # send command
        self.write(cmd + "\r\n")
        if echo:
            print("> " + cmd)
        # receive command return
        ret = self.readline().strip()
        if echo:
            print("< " + ret)

# main program
if __name__ == "__main__":
    # start polling thread
    tp = Thread(target=polling_thread)
    # set daemon: polling thread will exit if main thread exit
    tp.daemon = True
    tp.start()

    # allow time for thread start
    time.sleep(2.0)

    # init serial port
    s = ArduinoCommandSerial("/dev/ttyATH0", baudrate=9600, timeout=5.0)

    while True:
        try:
            # read linux system uptime in second
            with open('/proc/uptime', 'r') as f:
                uptime_s = int(float(f.readline().split()[0]))
            # format payload as hex str
            with th_lock:
                payload = binascii.hexlify(struct.pack(">IHf", vol_c_1, ts, tm_1))
            s.send_cmd("set_pld %s" % payload, echo=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # wait next loop
        time.sleep(5.0)

    s.close()
