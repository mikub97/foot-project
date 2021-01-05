import requests
import json
import time
import pandas as pd
import math
#import the date from API

# getting 5 min data (copy-pased from preparation)
#period -  time (in seconds) how long did the walking last
#gap - how often do you want to check the sensors
def get_data(period,gap):
    measurements = []
    for j in range(1, math.ceil(period/gap)):
        measure = []
        for i in range(1, 7):
            status_code = "success"
            try:
                response = requests.get(f'http://tesla.iem.pw.edu.pl:9080/v2/monitor/{i}')
                measure.append(response.json())
            except requests.exceptions.ConnectionError:
                status_code = "Connection refused"
        print(status_code)
        measurements.append(measure.copy())
        time.sleep(gap)

    df = pd.DataFrame()
    for m in measurements:
        df = pd.concat([df, pd.json_normalize(m)], axis=0)
    df.rename(columns={"id": "patientId"})

    df = pd.concat(
        [pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[0] if len(x) > 0 else {})).rename(
                columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                         'value': 'trace.value'})
                    ], axis=1),
         pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[1] if len(x) > 0 else {})).rename(
                 columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                          'value': 'trace.value'})
                    ], axis=1),
         pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[2] if len(x) > 0 else {})).rename(
                 columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                          'value': 'trace.value'})
                    ], axis=1),
         pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[3] if len(x) > 0 else {})).rename(
                 columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                          'value': 'trace.value'})
                    ], axis=1),
         pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[4] if len(x) > 0 else {})).rename(
                 columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                          'value': 'trace.value'})
                    ], axis=1),
         pd.concat([df.drop(['trace.sensors'], axis=1)
                       , df['trace.sensors'].apply(lambda x: pd.Series(x[5] if len(x) > 0 else {})).rename(
                 columns={'anomaly': 'trace.anomaly', 'id': 'trace.id', 'name': 'trace.footname',
                          'value': 'trace.value'})
                    ], axis=1)]
        , axis=0)
    df = df.reset_index().drop(columns=['index'])
    return df

# 5 min, every 5 s
def get_and_save_date():
    df = get_data(5*60,5);
    df.to_csv("data/sensors.csv")


def read_data():
    return pd.read_csv("data/sensors.csv")

