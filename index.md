## Overview

The following map shows the 4 locations of the campaign. Click on the red dots to zoom into the individual data sets.

<iframe src="html/index.html" height="500" width="500"></iframe>

## Measurements

In the course of the project, XXX measurements were taken with the multi-modal measurement system. Our focus was on the autonomous recording of variables both during the day and at night.

| Location                                                       | Daylight | Night |
| -------------------------------------------------------------- | -------- | ----- |
| [Balbina Reservoir](https://en.wikipedia.org/wiki/Balbina_Dam) | 16       | 9     |
| Caldeirao                                                      | 25       | nan   |
| Iranduba                                                       | 19       | 12    |
| Jandira                                                        | 25       | 8     |'

## Aggregated Data 

| Column                  | Data type | Comment                                |
| ----------------------- | --------- | -------------------------------------- |
| lat_est                 | float64   | estimated position                     |
| lon_est                 | float64   |                                        |
| yaw_est                 | float64   |                                        |
| lat_meas                | float64   | measured position                      |
| lon_meas                | float64   |                                        |
| hdop                    | float64   | horizontal dilution of precision       |
| nsats                   | float64   | number of satellites                   |
| depth                   | float64   | depth of water                         |
| experiment_location     | object    | lake                                   |
| meas_running            | bool      | actual state of the measurement system |
| corresponding_meas_file | object    | original measurement file              |
| CO2(ppm)                | float64   |                                        |
| airtemp in(degreeC)     | float64   |                                        |
| humidity in(rH)         | float64   |                                        |
| pressure in(mbar)       | float64   |                                        |
| airtemp out(degreeC)    | float64   |                                        |
| humidity out(rH)        | float64   |                                        |
| pressure out(mbar)      | float64   |                                        |
| PAR(umol m-2s-1)        | float64   |                                        |
| H2O temp(degreeC)       | float64   |                                        |
| position                | float64   |                                        |
| DayNight                | bool      | 'PAR==0'                               |

## Interactive data exploration 

A first version of the interactive data exploration tool is avialable [here](https://sebastianzug.github.io/RoBiMo_Trop_DataSet/html/interactive_table.html).