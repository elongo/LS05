#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

""" *** LivingSense Libraries *** """
import os
import urllib, urllib2, time
import time
from datetime import datetime
import sys
import Adafruit_ADS1x15
import atexit
import RPi.GPIO as GPIO
import glob
from tentacle_pi.AM2315 import AM2315
import math
    #END of Libraries

""" *** POWER BI API's *** """
# REST API endpoint, given to you when you create an API streaming dataset
REST_API_URL = "https://api.powerbi.com/beta/d9dc4061-aba4-47ad-9604-c994ff5caff0/datasets/87e8c51e-778f-4c66-896f-8b7f4f2ebd01/rows?redirectedFromSignup=1&key=6tXs51dtkpOsrMSBg%2F79aqEGY7ZLDkVSgNwlRZD%2BvtbLiCwaA2Nt0Ad9OpSQy%2F4hmi%2BeGMXIOw4SRxyRh6ZzSw%3D%3D"

""" *** VARIABLES *** """
# FIXED PARAMETERS FOR GAUGES IN POWER BI
minVWC = 0 
maxVWC = 100 
wet = 40 
VWC = {}
GAIN = 1
maxT_Cpu = 80
minT_Cpu = 0
okT_Cpu = 45
tank_empty = 0
tank_full = (80*273*63)/1000 # Height = 80cm, Width = 633cm, Lenght = 273 (Converted to Liters)

#Rockwool temperature setup (SENSOR DS18B20)
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir 	= '/sys/bus/w1/devices/'
device_folders  = glob.glob(base_dir + '28*')

# AIR TEMPERATURE AND HUMIDITY 2X AM2315
am_in = AM2315(0x5c,"/dev/i2c-1") # default I2C bus
am_out = AM2315(0x5c,"/dev/i2c-3") # new I2C bus created on pins GPIO23 (SDA) and GPIO24 (SCL)

""" LIST THAT WILL STORE TEMPERATURES - DS18B20 """
temperatures = []

""" *** SAYS GOOD BYE WHEN PROGRAM STOPS *** """
def exit_handler():
    GPIO.cleanup()
    print 'LivingSense stopped TRANSMITTING #DATA. See you soon!. GPIO.cleanup() executed' 
    return
atexit.register(exit_handler)
    # END OF GOOD BYE

""" ***  CPU TEMPERATURE *** """
def get_cpu_temp():
  res = os.popen("vcgencmd measure_temp").readline()
  t = float(res.replace("temp=","").replace("'C\n",""))
  print "t_cpu =", t#
  return t

""" *** VWC *** """
def vwc():
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1

    # Read all the ADC channel values in a list.
    values = [0]*3

    for i in range(3):
          # Read the specified ADC channel using the previously set gain value.
          values[i] = adc.read_adc(i, gain=GAIN)
          #VWC[i+1] =  (-0.0083*values[i]) + 47.81 # Old valibration made by EL
          VWC[i+1] =  (-0.0083*values[i]) + 300 # made up calibration, for dashboard test only.
          #VWC[i+1] =  (-0.00908*values[i]) + 187 # Calibratio made by Théo
    print "VWC = ", VWC
    return VWC
    # END OF VWC

""" *** WATER LEVEL - ULTRASOUND SENSOR HC-SR04 *** """
def level_1():
    # Use BCM GPIO references
    # instead of physical pin numbers
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # Define GPIO to use on Pi
    GPIO_TRIGGER = 13
    GPIO_ECHO = 26
    #Ultrasound Sensor_2
    # Set pins as output and input
    GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  # Trigger
    GPIO.setup(GPIO_ECHO,GPIO.IN)      # Echo
    # Set trigger to False (Low)
    GPIO.output(GPIO_TRIGGER, False)
    # Allow module to settle
    time.sleep(1)
    # Send 10us pulse to trigger
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start = time.time()
    while GPIO.input(GPIO_ECHO)==0:
      start = time.time()

    while GPIO.input(GPIO_ECHO)==1:
      stop = time.time()
    # Calculate pulse length
    elapsed = stop-start
    # Distance pulse travelled in that time is time
    # multiplied by the speed of sound (cm/s)
    distance = elapsed * 34300
    # total distance travelled by sound, divided by 2 (due to sound return), minus 3 cm (gap betwen sensor and water)
    distance = (distance -3.0)/ 2.0
    v_empty = (distance*(273*63))/1000
    v_in_tank_1 = tank_full - v_empty
    # Reset GPIO settings
    print "v_in_tank_1 = ", v_in_tank_1
    return v_in_tank_1
    # END OF WATER LEVEL SENSOR

def level_2():
    # Use BCM GPIO references
    # instead of physical pin numbers
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # Define GPIO to use on Pi
    GPIO_TRIGGER = 20
    GPIO_ECHO = 21
    # Set pins as output and input
    GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  # Trigger
    GPIO.setup(GPIO_ECHO,GPIO.IN)      # Echo
    # Set trigger to False (Low)
    GPIO.output(GPIO_TRIGGER, False)
    # Allow module to settle
    time.sleep(1)
    # Send 10us pulse to trigger
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start = time.time()
    while GPIO.input(GPIO_ECHO)==0:
      start = time.time()
    while GPIO.input(GPIO_ECHO)==1:
      stop = time.time()
    # Calculate pulse length
    elapsed = stop-start
    # Distance pulse travelled in that time is time
    # multiplied by the speed of sound (cm/s)
    distance = elapsed * 34300
    # total distance travelled by sound, divided by 2 (due to sound return), minus 3 cm (gap betwen sensor and water)
    distance = (distance -3.0)/ 2.0
    v_empty = (distance*(273*63))/1000
    v_in_tank_2 = tank_full - v_empty
    # Reset GPIO settings
    print "v_in_tank_1 = ", v_in_tank_2
    return v_in_tank_2
    # END OF WATER LEVEL SENSOR

""" *** ROCKWOOLL TEMPERATURE AND HUMIDTY - SENSOR DS18B20 *** """

def read_temp_raw( filename ):
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    return lines

def ReadSingleSensor( i, sensor_file ):
    device_name = sensor_file.replace( base_dir, '' ).replace( '/w1_slave', '' )
    print("SENSOR = ", device_name )

    lines = read_temp_raw( sensor_file )
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw( sensor_file )

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        #print "SENSOR",i, " = ", temp_c
        temperatures.append(temp_c)
        print "temperatures LIST = ", temperatures

def ReadSensors():
    for (i, item) in enumerate(device_folders):
        sensor_file = item + '/w1_slave'
        # print( sensor_file )
        ReadSingleSensor( i, sensor_file)
        #print "hi, this was ReadSensors (DS18B20)"
        # END OF ROCKWOOLL TEMP AND HUMIDTY

""" *** AIR TEMPERATURE AND HUMIDTY - SENSOR AM2315*** """
def air_in(): #in default I2C bus 1
    temperature_in, humidity_in, crc_check_in = am_in.sense()
    print "crc_check_in = ", crc_check_in
    return temperature_in, humidity_in
    time.sleep(1)

def air_out(): #in I2C bus 3
    temperature_out, humidity_out, crc_check_out = am_out.sense()
    print "crc_check_out = ", crc_check_out
    return temperature_out, humidity_out
    time.sleep(1)

def data_to_power_bi(data):
    try:
        """ SENDING DATA TO POWER BI"""
        req = urllib2.Request(REST_API_URL, data)
        response = urllib2.urlopen(req)
        #print("POST request to Power BI with data:{0}".format(data))
        print("Response: HTTP {0} {1}\n".format(response.getcode(), response.read()))
        print "DATA SENT TO POWER BI\n"
    except:
        print "There seems to be an issue connecting to PowerBi. However data is always stored locally in sensor_data.txt"

try:
  while True:
    reading_interval = 300
    now = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%Z")
    t_cpu = get_cpu_temp() # returns t
    VWC = vwc() #returns Sensor 0, Sensor 1, Sensor 2, Sensor 3
    w_lev_1 = level_1() #returns distance
    w_lev_2 = level_2() #returns distance
    ait_t_h_in = air_in() # returns temperature, humidty
    time.sleep(3)
    ait_t_h_out = air_out() # returns temperature, humidty
    temps_DS18B20 = ReadSensors() #returns t_surf_a = temperatures[0], t_surf_b = temperatures[1], t_treat_w = temperatures[2], t_waste_w = temperatures[3]

    data = '[{{"timestamp": "{0}", "t_cpu": "{1:0.1f}", "vwc_1": "{2:0.1f}", "vwc_2": "{3:0.1f}","w_lev_1": "{4:0.1f}","w_lev_2": "{5:0.1f}","air_t_in": "{6:0.1f}","air_h_in": "{7:0.1f}","air_t_out": "{8:0.1f}","air_h_out": "{9:0.1f}","t_surf_a": "{10:0.1f}","t_surf_b": "{11:0.1f}","t_treat_w": "{12:0.1f}", "t_waste_w": "{13:0.1f}", "minVWC": "{14:0.1f}", "maxVWC": "{15:0.1f}", "wet": "{16:0.1f}", "tank_empty": "{17:0.1f}", "tank_full": "{18:0.1f}", "reading_interval":"{19:0.1f}"}}]'.format(now, t_cpu, VWC[2], VWC[3], w_lev_1, w_lev_2, ait_t_h_in[0], ait_t_h_in[1], ait_t_h_out[0], ait_t_h_out[1], temperatures[0], temperatures[1], temperatures[2], temperatures[3], minVWC, maxVWC, wet, tank_empty, tank_full, reading_interval)
    sensor_data = open("sensor_data.txt", "a")
    sensor_data.write(data)
    sensor_data.write("\n")
    print "data = ", data
    print "data was written to file sensor_data.txt"
    print "I'll send data to Power BI, and will  sleep for ", reading_interval, "seconds. See you then!"
    data_to_power_bi(data)

    del temperatures[:]
    time.sleep(reading_interval)

except:
    print ("ACHTUNG: ---> ISSUE WHILE STREAMIN TO Power BI")
    sensor_data.close()