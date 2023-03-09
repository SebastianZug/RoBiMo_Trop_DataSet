#!/usr/bin/env python
# coding: utf-8

import sys
from pathlib import Path, PurePath
import pandas as pd
from datetime import datetime, timedelta

module_path = str(Path.cwd().parents[0])
# module_path = str(Path.cwd(__file__).parents[0] / "src")

if module_path not in sys.path:
     sys.path.append(module_path)

from parser.DataflashParser import read_from_log, write_csv, interpolate_data

def run_aggregation(ardupilot_file):
    # ## Step 1: Extracting estimated positional information from AHR2

    print("    ... extracting estimated positional information from AHR2")
    #FMT, 66, 45, AHR2, QccCfLLffff, TimeUS,Roll,Pitch,Yaw,Alt,Lat,Lng,Q1,Q2,Q3,Q4
    df, stats, msg = read_from_log(str(ardupilot_file), ['AHR2'], time_precision=1,
                                    flatline_remove=False, apply_zeros=False,
                                    message_type = "66")

    df.columns

    # inverse operation of the multiplication implemented in parser
    df_pos_est = pd.DataFrame()
    df_pos_est['lat_est'] = df['AHR2_Lat'] * 1/1.0000000116861E-07
    df_pos_est['lon_est'] = df['AHR2_Lng'] * 1/1.0000000116861E-07
    df_pos_est['yaw_est'] = df['AHR2_Yaw'] * 1/0.00999999977648258

    df_pos_est.head(3)

    # ## Step 2: Extracting time stamps and positions from GPS

    print("    ... extracting time stamps and positions from GPS")
    # FMT, 84, 51, GPS, QBBIHBcLLeffffB, TimeUS,I,Status,GMS,GWk,NSats,HDop,Lat,Lng,Alt,Spd,GCrs,VZ,Yaw,U
    # group_mults = ['70', '66', '66', '66', '48', '71', '71', '63', '63', '63', '63']
    df, stats, msg = read_from_log(str(ardupilot_file), ['GPS'], time_precision=1,
                                    flatline_remove=False, apply_zeros=False,
                                    message_type = "84")
    df.columns

    def gps_to_datetime(gps_week, gps_seconds):
        # GPS time starts on Jan 6, 1980 !
        gps_epoch = datetime(1980, 1, 6)
        # Calculate the number of seconds elapsed since GPS epoch
        elapsed_seconds = gps_week * 604800 + gps_seconds / 1000
        # Calculate the datetime object
        return gps_epoch + timedelta(seconds=elapsed_seconds)

    df_pos_meas = pd.DataFrame()
    df_pos_meas['datetime_UTC'] = df.apply(lambda x: gps_to_datetime(x.GPS_GWk[0], x.GPS_GMS[0]),axis=1)
    df_pos_meas['datetime_AMT'] = df_pos_meas['datetime_UTC'] - timedelta(hours=4, minutes=00)

    df_pos_meas['hdop']=df['GPS_HDop'] * 1/0.00999999977648258
    df_pos_meas['nsats'] = df['GPS_NSats']
    df_pos_meas['lat_meas'] = df['GPS_Lat'] * 1/1.0000000116861E-07
    df_pos_meas['lon_meas'] = df['GPS_Lng'] * 1/1.0000000116861E-07

    #df_pos_meas['yaw_meas'] = df['GPS_GCrs'] #* 1/0.00999999977648258


    # ## Step 3: Aggregate depth information from RFND

    print("    ... aggregate depth information from RFND")
    # FMT, 106, 16, RFND, QBCBB, TimeUS,Instance,Dist,Stat,Orient
    df, stats, msg = read_from_log(str(ardupilot_file), ['RFND'], time_precision=1,
                                    flatline_remove=False, apply_zeros=False,
                                    message_type = "106")

    df_range = pd.DataFrame()
    df_range['depth'] = df['RFND_Dist'] * 101.03
 
    # ## Merging

    print("    ... merging individual data frames")
    df_result = pd.merge(df_pos_est, df_pos_meas, left_index=True, right_index=True)
    df_result = pd.merge(df_result, df_range, left_index=True, right_index=True)
 
     # ## Filtering
    print("    ... checking time stamps")
    critical_date = "2000-01-01"
    invalid_df = df_result[df_result['datetime_AMT'] < critical_date]
    if not invalid_df.empty:
        print (f"      ! {invalid_df.shape[0]} samples of timestamps before 1.01.2000!")
        print (f"      ! Will be excluded from data set.")
        df_result = df_result[df_result['datetime_AMT'] > critical_date]

    df_result.reset_index(inplace=True)
    df_result.set_index("datetime_AMT", inplace=True)

    print("    ... resample data frame")
    df_result = df_result.tail(1000).resample('1s').first()

    return df_result

def main():

    # Data set with invalid time stamps
    #data_folder = "../../data/raw_data/ardupilot/day_07/"
    #_file_name = "00000048.log"

    data_folder = "../../data/raw_data/ardupilot/day_01/"
    _file_name = "00000038.log"

    ardupilot_file = Path.cwd() / data_folder / _file_name

    df_result = run_aggregation(ardupilot_file)

    result_file = Path.cwd() / data_folder / Path(_file_name.split(".")[0]+".p")   
    df_result.to_pickle(result_file)

if __name__ == "__main__":
    main()

