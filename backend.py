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
time = 10 #Secs on PLOT
L0, L1, L2, R0, R1, R2 = [], [], [], [], [],[]
plot = np.arange(time)
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()

sensors = ["L0","L1","L2","R0","R1","R2",]
app = dash.Dash(__name__,assets_url_path="assets") #Here we implement the app but for now smth really basic is included

feet_graphs = []

for s in sensors:
    feet_graphs.append(
        dcc.Graph(
        id = "real-time-plot-"+s,
        animate = True,
        )
    );
app.layout = html.Div([
    html.H1("Real time plot"),
    # dcc.Graph(
    #     id = "real-time-plot",
    #     animate = True,
    # ),
    feet_graphs[0],
    dcc.Interval(
        id = 'plot-update',
        interval = 1000
    )
])

@app.callback(Output("real-time-plot-L0","figure"),
            [Input("plot-update", "n_intervals")])

def update(input_data):
    print("update plot")
    dataSQL = []
    c.execute("SELECT ID,T,L0 FROM 'traces' ORDER BY T DESC LIMIT 30")

    rows = c.fetchall()
    dataSQL = [list(row) for row in rows]
    labels = ["ID","T","L0"]
    df = pd.DataFrame.from_records(dataSQL, columns=labels)
    print(df)
    X = df["T"]
    Y = df["L0"]

    data_plot = go.Scatter(
        x = list(X),
        y = list(Y),
        name = "Scatter",
        mode = "lines",
    )
    return{"data":[data_plot], "layout":go.Layout(xaxis= dict(range = [min(X), max(X)]),
                                                        yaxis = dict(range = [min(Y), max(Y)]))}


app.run_server()