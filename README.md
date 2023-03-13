# Data collection during RoBiMoTrop campaign  

The python scripts implement the data aggregation and processing pipeline of the RoBiMoTrop project aggregating water parameters by a robotic boat. It transforms data from different sources to Python pandas dataframes and ROS2 Bag files. TU Bergakademie Freiberg initiated the project.

The data can be explored on the corresponding [website](https://sebastianzug.github.io/RoBiMo_Trop_DataSet/) and are available in the `data` folder. 

## System structure and data sources

```
                                                     GUI (Website)
                                                          |
                                                          v
Measurement                                         +-----------+
Component        CO2 sensor    -------------------->| ESP32     |
                                  +----------+      |           |----> Download          
                Wind sensor    -->| Raspbery |      | Logging   |
                Humidity       -->| Pi       |<---->| Sensor    |
                Temperature    -->|          |      +-----------+
                                  |          |-----------------------> Logfiles (intended feature)
                                  +----------+     
                                                    
Autonomous                        +----------+    
Boat Control    Depth sensor   -->| ArduPilot|
Component                         | Pixhawk  |-----------------------> Download via ArduPilot
                                  |          |                         Mission planner
                                  +----------+
  
                                  +----------+ 
Obstacle        Laser scanner  -->| Raspberry|
Monitoring      Thermal camera -->| Pi       |-----------------------> ROS2bag File  
Component       Camera         -->|          |  
                                  +----------+
```

| Component                | Format                  | Contained Data                                                                                                                                                                       |
| ------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Measurement              | csv and Meta data files | Measurement data of aggregation phases with different durations (5 - 20min)                                                                                                           |
|                          | `proprocessed data`     | `CO2(ppm)`, `airtemp in(degreeC)`, `humidity in(rH)`, `pressure in(mbar)`, `airtemp out(degreeC)`, `humidity out(rH)`, `pressure out(mbar)`, `PAR(umol m-2s-1)`, `H2O temp(degreeC)` |
| Autonomous Boat Control | ArduPilot Log Files     | Positional information (raw, estimated), GNSS time stamps, robots modes, depth measurements                                                                                          |
|                          | `proprocessed data`     | `lat_est`, `lon_est`, `yaw_est`, `hdop`, `lat_meas`, `lon_meas`, `depth`, `location`                                                                                                                                                                                   |
| Obstacle Monitoring      | ROS2 bag Files          | Distances of obstacles in front of the robot                                                                                                                                         |


## Processing chain 

+ __Measurement Component__ - Read the non standard format with `11_Extract_Measurements.ipynb`. The underlying python script stores the corresponding pandas files in `preproc_data_` folder.


+ __ABC Component__ - The Log-Files of ArduPilot can be downloaded via Mission Planner as _bin_ or _log_ file. In case of reading the SD Card directly only binary files are available. Fortunately, ArduPilot offers an tool for offline translation too. After preprocessing all files by running the notebook `10_Extract_ArduPilotData.ipynb`. All dataframes are stored in `preproc_data_` folder.

+ __Obstacle Monitoring Component__ - _have to be done_

## ToDos

### Phase 1: Data aggregation

- [X] Evaluate GNSS information (unclear MULT values)
- [X] Extract time stamps for GPS weeks and ms per Weeks
- [X] Check depth information data 
- [X] Integrate sensor data (measurement, wind, humidity, light sensor)
- [X] Provide overview map of all measurement points (station perspective)
- [ ] Draw robot parameter
- [ ] Improve data description on README
- [ ] Check the content of GPA to evaluate the GNSS position measurement [Link](https://ardupilot.org/copter/docs/logmessages.html)
- [ ] Generate ROS2 Bag from data set

### Phase 2: ROS Data aggregation

- [ ] Adjusting time stamp on RP
- [ ] Activate Cameras on Raspberry Pi
- [ ] Add rosbag recording mechanism
- [ ] Upload all data to MARV

## Acknowledgments

Many thanks to all contributors of open source repositories from different python packages we used. You make a great job!
We want to emphasize one project especially - the implementation of a student team from Hamburg University for extracting data from  Ardupilot Log files was very helpful and saved us a lot of time [Link](https://gitlab.rrz.uni-hamburg.de/bay2789/bslogfiles/-/tree/master). 