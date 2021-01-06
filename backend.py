import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly .graph_objs as go
import sqlite3
from collections import deque

#Init
time = 1 #Secs on PLOT
L0, L1, L2, R0, R1, R2 = [], [], [], [], [],[]
plot = np.arange(time)
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()

df = pd.read_csv('data/sensors.csv')
sensors = ["L0","L1","L2","R0","R1","R2",]
lastname_options = []
for lastname in df['lastname'].unique():
    lastname_options.append({'label': str(lastname), 'value': lastname})

app = dash.Dash(__name__,assets_url_path="assets") #Here we implement the app but for now smth really basic is included

app.layout = html.Div([
    html.H1("Real time plot"),
    dcc.Graph(
        id = "real-time-plot",
        animate = True,
    ),
    dcc.Interval(
        id = 'plot-update',
        interval = 1000
    ),
    dcc.Dropdown(id='patient-picker',options=lastname_options,value=lastname_options[0]['label'])

])

@app.callback(Output("real-time-plot","figure"),
            [Input("plot-update", "n_intervals"),
             Input('patient-picker', 'value')])
def update(data,selected_patient):
    print("update plot")
    c.execute("SELECT TRACETIME,L0,L1,L2,R0,R1,R2 FROM 'traces' WHERE SECONDNAME = '"+selected_patient+"' ORDER BY TRACETIME DESC LIMIT 30")
    rows = c.fetchall()
    dataSQL = [list(row) for row in rows]
    labels = ["T","L0",'L1','L2','R0','R1','R2']
    df = pd.DataFrame.from_records(dataSQL, columns=labels)
    print(df)
    data = []
    for s in sensors:
        X = df["T"]
        Y = df[s]

        data.append(go.Scatter(
            x = list(X),
            y = list(Y),
            name = s,
            mode='lines',
            opacity=0.7,
            marker={'size': 15},
        ))
    return{"data":data, "layout":go.Layout(
                    xaxis= dict(range = [min(X), max(X)]),
                    yaxis = dict(range = [min(Y), max(Y)]),
                    hovermode='closest' )}


app.run_server()