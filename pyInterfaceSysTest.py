#from connectArduino import *
#from DB import *
import sys
import os
import threading
from datetime import datetime
import requests
import serial
import time
import random

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Evaluate dew point


# Write info on TXT file
def sendfile(sensname, valOut, ts, outpath):
    try:
        outtxt = f"{ts}\t{valOut[0]}\t{valOut[1]}\n"
        with open(outpath,'a') as fileout:
            fileout.write(outtxt)
        fileout.close()
    except:
        return False
    return True    
    

# reading and formatting lists of data
def readData(arduino, temp_sign, temp_last,testmode):
    valsens = ("").split()
    sensname = ("").split()
    stringout = arduino.readline().decode()
    if testmode:
        print(stringout)
    while "End communication" not in stringout:
        try:
            if "Temp" in stringout:
                temp = stringout.split()
                temp_abs = float(temp[2])
                if temp_abs == 0. and not abs(temp_last) == 0.:
                    temp_sign = -1.*temp_sign
                valsens.append(temp_abs*temp_sign)
                sensname.append("Temperature (C)")
            elif "Hum" in stringout:
                hum = stringout.split()
                valsens.append(float(hum[2]))
                sensname.append("Humidity (%)")
        except:
            print("Something went wrong while reading data from Arduino")
        stringout = arduino.readline().decode()
        if testmode:
            print(stringout)
    return sensname, valsens

def mainLoop(arduino, temp_sign, temp_last, testmode, outpath, writeDB):
    shutdown = False 
    stringOut = arduino.readline().decode()
    if "Sending data to PC" in stringOut:
        sensname, valOut = readData(arduino, temp_sign, temp_last, testmode)
        temp_last = valOut[1]
        ts = datetime.now()
        ts = ts.strftime("%H:%M:%S")
        if writeDB:
            token = "T1QLIsmyh4f8wTTyaJL85hVC07DOScCxu5BKFRh2DgEwojo6p29-msuCbUZbP7Qi6cLU4e1D7hLZ0gyfA7GuiQ=="
            org = "FAST_Group"
            url = "http://localhost:8086"
            bucket = "ArduinoClimateChamber"
            write_client = InfluxDBClient(url=url, token=token, org=org)
            write_api = write_client.write_api(write_options=SYNCHRONOUS)
            point = Point("climate_chamber").field("HUM", valOut[0]).field("TEMP", valOut[1]).tag("location", "climate_chamber").time(datetime.utcnow())
            try:
                write_api.write(bucket=bucket, org=org, record=point)
            except Exception as e:
                print(f"Problems uploading to InfluxDB:\n{e}")
            write_client.close()
        successWrite = sendfile(sensname,valOut,ts,outpath)
        if not successWrite:
            print("! Problem while writing txt file !")
        if testmode:
            sizeval = len(valOut)
            print(f'N of params: {sizeval}\n')
        print(ts,valOut,sep="\t")
        #if successDB:
        #    print("Data correctly sent to Influx\n")
    # may add a condition/signal to stop the script (not sure if needed)
    return shutdown, temp_last

if __name__ == "__main__":
    writeDB = True
    shutdown = False
    testmode = False     #Flag for output of the functions
    testCO2 = False     #Flag to randomize CO2 status
    newfile = False
    temp_sign = 1.
    temp_last = 0.
    
    outpath = f"{os.getcwd()}/{datetime.date(datetime.now())}.txt" #Define path and name of the txt file for output (e.g. f"/path/{datetime.date()}.txt")
    if newfile:
        with open(outpath,'w') as fileout:
            fileout.write("Time\tHumidity (%)\tTemperature (C)\n")
        fileout.close()
    arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=10.)
    #time.sleep(5)
    while not shutdown:
        try:
            shutdown, temp_last = mainLoop(arduino, temp_sign, temp_last, testmode, outpath, writeDB)
            #time.sleep(1.) #added to match arduino delay
        except:
            print("!! Something went wrong, try restablishing connection !!")
            try:
                arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=10.)
            except:
                print("Reconnection failed, start shutdown procedure")
                shutdown = True
    print("Shutdown completed: end of serial communication")