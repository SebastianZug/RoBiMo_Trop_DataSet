#!/usr/bin/env python
# coding: utf-8

import sys
from pathlib import Path, PurePath
import pandas as pd
from datetime import datetime, timedelta

def run_aggregation(measurement_file):

    print("    ... extract data from measurement file")
    df_raw=pd.read_csv(measurement_file, delimiter=";")
    df= df_raw[3:-1].copy()
    df['datetime_AMT']=pd.to_datetime(df.Timestamp, format="%d.%m.%y %H:%M:%S")

    slope = df_raw.iloc[1]
    offset = df_raw.iloc[2]

    print("    ... preprocess data")
    column_names = ['CO2(ppm)', 'airtemp in(degreeC)',
       'humidity in(rH)', 'pressure in(mbar)', 'airtemp out(degreeC)',
       'humidity out(rH)', 'pressure out(mbar)', 'PAR(umol m-2s-1)',
       'H2O temp(degreeC)',]

    for column_name in column_names:
        df[column_name]=df[column_name] * slope[column_name] + offset[column_name]

    #df.reset_index(inplace=True)
    df.set_index("datetime_AMT", inplace=True)
    df = df.resample('1s').first()
    #print(df.index)

    return df

def main():

    data_folder = "../../raw_data/measurements/Messpunkt 01/"

    _file_name = "010323-140717-ADC1.csv"
    measurement_file = Path.cwd() / data_folder / _file_name

    df = run_aggregation(measurement_file)

    result_file = Path.cwd() / data_folder / Path(_file_name.split(".")[0]+".p")   
    df.to_pickle(result_file)

if __name__ == "__main__":
    main()
