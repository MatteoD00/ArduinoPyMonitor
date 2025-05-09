#from connectArduino import *
#from DB import *
import sys
import threading
from datetime import datetime
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
def sendfile(sensname, valOut, ts, outpath):
    try:
        outtxt = f"Time: {ts}            {sensname[0]}: {valOut[0]}            {sensname[1]}: {valOut[1]}\n"
        with open(outpath,'a') as fileout:
            fileout.write(outtxt)
        fileout.close()
    except:
        return False
    return True    
    

# reading and formatting lists of data
def readData(arduino,testmode):
    valsens = ("").split()
    sensname = ("").split()
    stringout = arduino.readline().decode()
    if testmode:
        print(stringout)
    while "End communication" not in stringout:
        try:
            if "Temp" in stringout:
                temp = stringout.split()
                valsens.append(float(temp[2]))
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

def mainLoop(arduino, testmode, outpath):
    shutdown = False 
    stringOut = arduino.readline().decode()
    if "Sending data to PC" in stringOut:
        sensname, valOut = readData(arduino,testmode)
        ts = datetime.now()
        ts = ts.strftime("%H:%M:%S")
        #successDB = send2DB(valOut, ts)
        successWrite = sendfile(sensname,valOut,ts,outpath)
        if not successWrite:
            print("! Problem while writing txt file !")
        if testmode:
            print(ts,valOut,sep="  ;   ")
            sizeval = len(valOut)
            print(f'N of params: {sizeval}\n')
        #if successDB:
        #    print("Data correctly sent to Influx\n")
    # may add a condition/signal to stop the script (not sure if needed)
    return shutdown

if __name__ == "__main__":
    shutdown = False
    testmode = True     #Flag for output of the functions
    testCO2 = False     #Flag to randomize CO2 status
    outpath = "test.txt" #Define path and name of the txt file for output (e.g. f"/path/{datetime.date()}.txt")
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=3.)
    #time.sleep(5)
    while not shutdown:
        try:
            shutdown = mainLoop(arduino, testmode, outpath)
            #time.sleep(1.) #added to match arduino delay
        except:
            print("!! Something went wrong, quit python script !!")
            shutdown = True
    print("Shutdown completed: end of serial communication")