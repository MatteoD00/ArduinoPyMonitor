# Trivial system to monitor temperature and humidity using an Arduino board with a T/RH sensor connected inside any measuring environment.
## To run the monitoring system:
1. Open [Arduino IDE 2](https://docs.arduino.cc/software/ide-v2/tutorials/getting-started/ide-v2-downloading-and-installing/) (may not work with version 1) and select the connected board
2. Open "climatemonitor.ino" in the IDE and flash the firmware on the board (Arduino will automatically start running it until it is unplugged from the power source)
3. Run "pyInterfaceSysTest.py" in a terminal to read the output from Arduino and save it in a txt file  

## Notes:
<ol type="A">
  <li>Python script must be running the entire time to collect and store data</li>
  <li>Check that the sensor inside the Arduino firmware is the correct model</li>
  <li>To shutdown the Arduino board just unplug it from the power source</li>
</ol>
