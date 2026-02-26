import sys
import os
import threading
from datetime import datetime, timezone
import serial
import time
import math
import configparser

# InfluxDB module required only for uploading data
try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    pass

# Evaluate dew point
def dewPoint(temp, hum):
    if temp > 0:
        a = 17.62
        b = 243.12
    else:
        a = 22.46
        b = 272.62
    gamma = (a * temp) / (b + temp) + math.log(hum / 100.0)
    dew_point = (b * gamma) / (a - gamma)
    return round(dew_point, 2)

# Write info on TXT file
def sendfile(valOut, ts, outpath):
    try:
        # valOut[0] is Hum, valOut[1] is Temp
        outtxt = f"{ts}\t{valOut[0]}\t{valOut[1]}\n"
        with open(outpath, 'a') as fileout:
            fileout.write(outtxt)
    except Exception as e:
        print(f"File Write Error: {e}")
        return False
    return True

# reading and formatting lists of data
def readData(arduino, temp_sign, temp_last, debug):
    valsens = []
    sensname = []
    stringout = arduino.readline().decode().strip()
    
    if debug:
        print(f"DEBUG: {stringout}")
        
    while "End communication" not in stringout:
        try:
            if "Temp" in stringout:
                temp_parts = stringout.split()
                temp_abs = float(temp_parts[2])
                # Logic for handling the sign flip at 0 degrees
                if temp_abs == 0. and abs(temp_last) != 0.:
                    temp_sign = -1. * temp_sign
                valsens.append(temp_abs * temp_sign)
                sensname.append("Temperature (C)")
            elif "Hum" in stringout:
                hum_parts = stringout.split()
                valsens.append(float(hum_parts[2]))
                sensname.append("Humidity (%)")
        except Exception:
            print("Something went wrong while reading data from Arduino")
            
        stringout = arduino.readline().decode().strip()
        if debug:
            print(f"DEBUG: {stringout}")
            
    return sensname, valsens, temp_sign

def mainLoop(arduino, temp_sign, temp_last, debug, outpath, write_api, influx_info):
    shutdown = False 
    try:
        stringOut = arduino.readline().decode().strip()
    except Exception:
        return False, temp_last, temp_sign

    if "Sending data to PC" in stringOut:
        sensname, valOut, temp_sign = readData(arduino, temp_sign, temp_last, debug)
        
        # Safety check: ensure we actually got both Humidity and Temperature
        if len(valOut) < 2:
            print("Warning: Received incomplete data frame")
            return False, temp_last, temp_sign

        temp_last = valOut[1]
        dew_p = dewPoint(valOut[1], valOut[0])
        ts = datetime.now()

        # Write to InfluxDB using the persistent write_api
        if write_api is not None:
            point = Point("climate_chamber") \
                .field("HUM", valOut[0]) \
                .field("TEMP", valOut[1]) \
                .field("DEW", dew_p) \
                .tag("location", "climate_chamber") \
                .time(datetime.now(timezone.utc))
            try:
                write_api.write(bucket=influx_info['bucket'], org=influx_info['org'], record=point)
            except Exception as e:
                print(f"Problems uploading to InfluxDB: {e}")

        successWrite = sendfile(valOut, ts, outpath)
        if not successWrite:
            print("! Problem while writing txt file !")
            
        print(f"{ts}\tH:{valOut[0]}%\tT:{valOut[1]}C\tDP:{dew_p}C")
        
    return shutdown, temp_last, temp_sign

if __name__ == "__main__":
    # 1. Load Main Config
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    port = config['ARDUINO']['port']
    baud = config.getint('ARDUINO', 'baudrate')
    timeout = config.getfloat('ARDUINO', 'timeout')
    
    # Use getboolean to handle "True"/"False" strings correctly
    writeDB = config.getboolean('MONITOR', 'writeDB')
    debug = config.getboolean('MONITOR', 'debug')
    newfile = config.getboolean('MONITOR', 'newfile')
    temp_sign = config.getfloat('MONITOR', 'temp_sign')
    
    # 2. Setup File Output
    outdir = config["MONITOR"].get('outdir') or os.path.join(os.getcwd(), "MonitorTXT")
    os.makedirs(outdir, exist_ok=True)
    
    outfile_name = config["MONITOR"].get('outfile_name') or datetime.now().strftime("%Y-%m-%d")
    outpath = os.path.join(outdir, f"{outfile_name}.txt")
    
    if newfile:
        with open(outpath, 'w') as fileout:
            fileout.write("Time\tHumidity (%)\tTemperature (C)\n")

    # 3. Setup InfluxDB (persistent connection)
    write_api = None
    influx_info = {}
    influx_client = None
    
    if writeDB:
        inf_conf = configparser.ConfigParser()
        inf_conf.read('config_influx.ini')
        influx_info = inf_conf['INFLUXDB']
        
        influx_client = InfluxDBClient(
            url=influx_info['url'], 
            token=influx_info['token'], 
            org=influx_info['org']
        )
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    # 4. Main Serial Loop
    arduino = serial.Serial(port, baud, timeout=timeout)
    temp_last = 0.
    shutdown = False
    
    print(f"Monitoring started on {port}...")

    try:
        while not shutdown:
            shutdown, temp_last, temp_sign = mainLoop(
                arduino, temp_sign, temp_last, debug, outpath, write_api, influx_info
            )
    except KeyboardInterrupt:
        print("\nShutdown signal received.")
    finally:
        # Ensure everything closes properly
        if influx_client:
            influx_client.close()
        arduino.close()
        print("Connections closed. Goodbye.")