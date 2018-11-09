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
(ts, tm_1, tm_2) = (0, 0.0, 0.0)
(j0_d, j0_m, jo_y, j0_l_h, j0_vol_j) = (0, 0, 0, [0xffffffff] * 24, 0xffffffff)


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
    global ts, tm_1, tm_2
    global j0_d, j0_m, jo_y, j0_l_h, j0_vol_j
    c = FloatModbusClient(host=SERVER_HOST, port=SERVER_PORT, unit_id=0xFF, auto_open=True)
    # polling loop
    while True:
        try:
            # read ts
            l_ts = c.read_holding_registers(28)
            # read tm
            l_tm = c.read_float(512, 2)
            # read j0 volumes
            l_vol = c.read_holding_registers(2048, 51)
            # update global vars
            with th_lock:
                if l_ts:
                    ts = l_ts[0]
                if l_tm:
                    tm_1 = l_tm[0]
                    tm_2 = l_tm[1]
                if l_vol:
                    # j date
                    reg_date =  l_vol[0]
                    j0_y = (reg_date & 0b1111111000000000) >> 9
                    j0_m = (reg_date & 0b0000000111100000) >> 5
                    j0_d = (reg_date & 0b0000000000011111)
                    # J0: vol_j0 and vol_j0_hx
                    l_vol32 = utils.word_list_to_long(l_vol[1:])
                    j0_l_h = l_vol32[0:24]
                    j0_vol_j = l_vol32[24]
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # 1s before next polling
        time.sleep(1.0)

# some class
class MySerial(serial.Serial):
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

    s = MySerial("/dev/ttyATH0", baudrate=9600, timeout=5.0)

    while True:
        try:
            # read system uptime in second
            with open('/proc/uptime', 'r') as f:
                uptime_s = int(float(f.readline().split()[0]))
            # format payload as hex str
            with th_lock:
                payload = binascii.hexlify(struct.pack(">IHf", j0_vol_j, ts, tm_1))
            s.send_cmd("set_pld %s" % payload, echo=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
        # wait next loop
        time.sleep(5.0)

    s.close()
