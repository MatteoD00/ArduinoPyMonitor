#from connectArduino import *
#from DB import *
import sys
import os
import threading
from datetime import datetime, timezone
import requests
import serial
import time
import random
import math
import configparser

# Evaluate dew point
def dewPoint(temp, hum):
    if temp > 0:
        a = 17.62
        b = 243.12
    else:
        a = 22.46
        b = 272.62

    # Magnus-Tetens calculation
    gamma = (a * temp) / (b + temp) + math.log(hum / 100.0)
    dew_point = (b * gamma) / (a - gamma)
    
    return round(dew_point, 2)

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
                if temp_abs == 0. and abs(temp_last) != 0.:
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
    return sensname, valsens, temp_sign

def mainLoop(arduino, temp_sign, temp_last, testmode, outpath, config_influx):
    shutdown = False 
    stringOut = arduino.readline().decode()
    if "Sending data to PC" in stringOut:
        sensname, valOut, sign_out = readData(arduino, temp_sign, temp_last, testmode)
        temp_last = valOut[1]
        dew_point = dewPoint(valOut[1],valOut[0])
        ts = datetime.now()
        #ts = ts.strftime("%H:%M:%S")
        if config_influx is not None:
            token = config_influx['INFLUXDB']['token']
            org = config_influx['INFLUXDB']['org']
            url = config_influx['INFLUXDB']['url']
            bucket = config_influx['INFLUXDB']['bucket']
            write_client = InfluxDBClient(url=url, token=token, org=org)
            write_api = write_client.write_api(write_options=SYNCHRONOUS)
            point = Point("climate_chamber").field("HUM", valOut[0]).field("TEMP", valOut[1]).field("DEW", dew_point).tag("location", "climate_chamber").time(datetime.now(timezone.utc))
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
    # may add a condition/signal to stop the script (not sure if needed)
    return shutdown, temp_last, sign_out

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    port = config['ARDUINO']['port']
    baud = config.getint('ARDUINO', 'baudrate')
    timeout = config.getfloat('ARDUINO','timeout')
    writeDB = config.getboolean('MONITOR','writeDB')
    testmode = config.getboolean('MONITOR','testmode')     #Flag for output of the functions
    # testCO2 = False     #Flag to randomize CO2 status
    newfile = config.getboolean('MONITOR','newfile')
    temp_sign = config.getfloat('MONITOR','temp_sign')
    
    outdir = config["MONITOR"]['outdir']
    if outdir is None:
       outdir = os.path.join(os.getcwd(),"MonitorTXT")
    os.makedirs(outdir,exist_ok=True)
    outfile_name = config["MONITOR"]['outfile_name']
    if outfile_name is None:
        outfile_name = datetime.date(datetime.now())
    outpath = f"{os.getcwd()}/MonitorTXT/{outfile_name}.txt" #Define path and name of the txt file for output (e.g. f"/path/{datetime.date()}.txt")
    if newfile:
        with open(outpath,'w') as fileout:
            fileout.write("Time\tHumidity (%)\tTemperature (C)\n")
        fileout.close()
    arduino = serial.Serial(port, baud, timeout)
    
    config_influx = None
    if writeDB:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        config_influx = configparser.ConfigParser()
        config_influx.read('config_influx.ini')

    shutdown = False
    temp_last = 0.
    while not shutdown:
        try:
            shutdown, temp_last, temp_sign = mainLoop(arduino, temp_sign, temp_last, testmode, outpath, config_influx)
            #time.sleep(1.) #added to match arduino delay
        except KeyboardInterrupt:
            print("Received shutdown signal from user, disabling serial monitor")
            arduino.close()
            shutdown = True
        except Exception as e:
            print("!! Something went wrong, establishing new connection !!")
            try:
                arduino = serial.Serial(port, baud, timeout)
                print("Serial connection available --> Check Python script for instabilities")
            except:
                print("Reconnection failed, start shutdown procedure")
                arduino.close()
                shutdown = True
    print("Shutdown completed: end of serial communication")