#from connectArduino import *
#from DB import *
import sys
import threading
import datetime
import requests
import serial
import time
import random

"""
#Write to database via HTTP post
def send2DB(sensors, values, ts):
        try:
            #time.sleep(0.70)
            post_params = ( ('db', 'test_PetalColdbox'), )
            for i in range(len(sensors)):
                data_sent = sensors[i]+' value='+str(format(values[i], '.2f'))+' '+str(ts)
                print(data_sent)
                response_db = requests.post('http://atlasmonitoring.desy.de:8086'+'/write', params=post_params, data=data_sent)
                print(response_db)
            return True
        except:
            print("Error while connecting to Grafana")
            return False
"""

# Write info on TXT file
def sendfile(sensname, valOut, ts, fileout):
    outtxt = f"Time: {ts}            {sensname[0]}: {valOut[0]}            {sensname[1]}: {valOut[1]}"

# reading and formatting lists of data
def readData(arduino,testmode):
    valsens = ("").split()
    sensname = ("").split()
    stringout = arduino.readline().decode()
    if testmode:
        print(stringout)
    while "End communication" not in stringout:
        try:
            if "Temperature" in stringout:
                temp = stringout.split()
                valsens.append(float(temp[2]))
                sensname.append("Temperature (C)")
            elif "Humidity" in stringout:
                hum = stringout.split()
                valsens.append(float(hum[2]))
                sensname.append("Humidity (%)")
        except:
            print("Something went wrong while reading data from Arduino, impossible to upload to Influx")
        stringout = arduino.readline().decode()
        if testmode:
            print(stringout)
    return sensname, valsens

def mainLoop(arduino, testmode, fileout):
    shutdown = False 
    stringOut = arduino.readline().decode()
    if "Sending data to PC" in stringOut:
        sensname, valOut = readData(arduino,testmode)
        ts = time.time()
        #successDB = send2DB(valOut, ts)
        succesFile = sendfile(sensname,valOut,ts,fileout)
        if testmode:
            print(valOut,ts,sep="  ;   ")
            sizeval = len(valOut)
            print(f'N of values: {sizeval}\n')
        #if successDB:
        #    print("Data correctly sent to Influx\n")
    # may add a condition/signal to stop the script (not sure if needed)
    return shutdown

if __name__ == "__main__":
    shutdown = False
    testmode = True     #Flag for output of the functions
    testCO2 = False     #Flag to randomize CO2 status
    outpath = "/path/DD-MM-YY.txt" #Define path and name of the txt file for output 
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=3.)
    #time.sleep(5)
    fileout = open(outpath,"a")
    while not shutdown:
        try:
            shutdown = mainLoop(arduino, testmode, fileout)
            #time.sleep(1.) #added to match arduino delay
        except:
            print("!! Something went wrong, quit python script !!")
            shutdown = True