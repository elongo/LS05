from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient
from struct import *
import math
import time

con_cube_ip = '172.18.0.186'
now = datetime.utcnow()

def convert_bytes_to_float(iLSnt1, int2):
    hex1 = (int1).to_bytes(2,byteorder='little')
    hex2 = (int2).to_bytes(2,byteorder='little')
    return 0 if math.isnan(float(unpack("<f",hex2 + hex1)[0])) else unpack("<f",hex2 + hex1)[0]

for i in range(1,9):
    try:
        client = ModbusTcpClient(con_cube_ip)
        r = client.read_input_registers(0x0080, 116)
        line = 'data,geohash=' + ghash + ' ' + \
               'xP1Value=' + str(convert_bytes_to_float(r.registers[2], r.registers[3])) + \
               ',xP2Value=' + str(convert_bytes_to_float(r.registers[10], r.registers[11])) + \
               ',xP3Value=' + str(convert_bytes_to_float(r.registers[18], r.registers[19])) + \
               ',xP4Value=' + str(convert_bytes_to_float(r.registers[26], r.registers[27])) + \
               ',xP5Value=' + str(convert_bytes_to_float(r.registers[34], r.registers[35])) + \
               ',xP6Value=' + str(convert_bytes_to_float(r.registers[42], r.registers[43])) + \
               ',xP7Value=' + str(convert_bytes_to_float(r.registers[50], r.registers[51])) + \
               ',xP8Value=' + str(convert_bytes_to_float(r.registers[58], r.registers[59])) + \
               ',xP9Value=' + str(convert_bytes_to_float(r.registers[66], r.registers[67])) + \
               ',xP10Value=' + str(convert_bytes_to_float(r.registers[74], r.registers[75])) + \
               ',xP11Value=' + str(convert_bytes_to_float(r.registers[82], r.registers[83])) + \
               ',xP12Value=' + str(convert_bytes_to_float(r.registers[90], r.registers[91])) + \
               ',xP13Value=' + str(convert_bytes_to_float(r.registers[98], r.registers[99])) + \
               ',xP14Value=' + str(convert_bytes_to_float(r.registers[106], r.registers[107])) + \
               ',xP15Value=' + str(convert_bytes_to_float(r.registers[114], r.registers[115])) + \
               ' ' + str(now) + '\n'

        print "@ ", con_cube_ip, " we read"
        print "here we go = ", line
        print "clinet = ", client
        print "r = ", r
        break
    except:
        time.sleep(2)
        print "Couldn't get S::CAN values, at ", now
        continue

with open('/home/pi/LS05/examples/WasserData/' + str(now), 'a') as file:
    file.write(line)