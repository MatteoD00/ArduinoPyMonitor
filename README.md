# 🌡️ Arduino Climate Monitor

A lightweight system for real-time monitoring of temperature and humidity. This project uses an Arduino with a T/RH sensor to stream data via Serial to a Python logger, which stores data locally and optionally uploads it to **InfluxDB**.


## 📂 Project Structure

* **`arduino_monitor/`**: Arduino firmware (`.ino`) and hardware library requirements.
* **`py_monitor/`**: Python interface, configuration files, and `requirements.txt`.
* **`MonitorTXT/`**: Default output directory for local data logs.
* **`plot_graph.ipynb`**: Jupyter Notebook for post-process visualization.


## 🚀 Getting Started

### 1. Hardware Preparation
1. Open [**Arduino IDE 2**](https://docs.arduino.cc/software/ide-v2/tutorials/getting-started/ide-v2-downloading-and-installing/) and load `arduino_monitor/climatemonitor.ino`.
2. Ensure the sensor model defined in the code matches your physical hardware (e.g., [DTH11](https://docs.arduino.cc/libraries/dht11/) or [DHT22](https://docs.arduino.cc/libraries/dht22/)).
3. Connect your board and **Upload** the firmware.

### 2. Python Environment
1. Navigate to the Python directory:
    ```bash
    cd py_monitor
    ```
2. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```
### 3. Configuration
  1. **General Settings:** Open **`config.ini`** and set your *port* (e.g., **`/dev/ttyACM0`** on Linux or **`COM3`** on Windows) and *baudrate*.
  2. **Database (Optional):** If you want to use InfluxDB:
      *  Copy **`config_influx_example.ini`** to **`config_influx.ini`**:
          ```bash
          cp config_influx_example.ini config_influx.ini
          ```
      *  Open the new **`config_influx.ini`** and enter your *Organization*, *Bucket*, and *Secret Token*.


## 💻 Usage
To start the monitoring session, run the logger:
  ```bash
  python pyInterfaceSysTest_new.py
  ```
- **Live View:** The terminal will display the *timestamp*, *Humidity*, *Temperature*, and calculated *Dew Point*.
- **Storage:** Data is automatically appended to a **`.txt`** file in the **`MonitorTXT`** folder.
- **Stop:** Press **`Ctrl+C`** in the terminal to safely close the serial connection and stop logging.


## 📝 Technical Notes
- **Dew Point:** The system calculates the dew point in real-time using the *Magnus-Tetens* approximation:

$$\gamma(T, RH) = \ln\left(\frac{RH}{100}\right) + \frac{17.62T}{243.12+T}$$

$$T_{dp} = \frac{243.12\gamma}{17.62-\gamma}$$

- **Data Persistence:** The Python script must remain running to collect and store data. The Arduino does not store history internally.
- **Shutdown:** To turn off the system, stop the Python script and unplug the Arduino from its power source.


## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
