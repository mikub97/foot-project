from datetime import date, datetime

import dash_table
import pandas as pd
import numpy as np
import plotly.express as px
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import plotly .graph_objs as go
import sqlite3
import threading
#Init
from listener import get_users, fetch_data, prepare, getUserInfo
from manufacture import createScatterPlot, createBoxPlot, getTracesBetweenTimes

visualize_clicks=0
historical_display = False
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()
prepare()
storageThread = threading.Thread(name="fetch",
                                 target=fetch_data,
                                 args=(conn, ))

storageThread.start()
users = get_users(c)
patients = pd.DataFrame(users)
sensors = ["L0","L1","L2","R0","R1","R2",]
patient_picker_options = []
for user in users:
    patient_picker_options.append({'label': str(user['firstname'] + " " + user['secondname']), 'value':user['secondname']})

app = dash.Dash(__name__,assets_url_path="assets",) 

#################################################### MENU ####################################################

menu_div = html.Div([
    html.Div([html.Span(html.H3("WALKING PROCESS ANALYSIS"),className="logo")],className="three columns"),
    html.Div([html.Span(html.H3("STATISTICAL DATA"))], className="seven columns"),
    html.Div([html.Span(html.H3("LEGEND"))],className="two columns")

],className="twelve columns")



#################################################### PATIENT INFO, STATISTICAL DATA, AND THE PICTURE OF FEET ####################################################

statistical_vs = ['L0_avg','L0_med','L0_min','L0_max','L0_q1','L0_q3',
                  'avg1','min1','max1','sth1',"some1",
                  'avg2','min2','max2','sth2',"some2",
                  'avg3','min3','max3','sth3',"some3",
                  'avg4','min4','max4','sth4',"some4"]

patient_info = ["firstname","secondname",'birthdate','is disabled?']
patient_div =html.Div([
        html.Div([
            dcc.Dropdown(id='patient-picker', options=patient_picker_options, value=users[0]['secondname'], placeholder="Select a user",),
            html.H3("PATIENT INFO"),
            html.Table(
                ([html.Tr([
                    html.Td(val), html.Td([],id=val + "_v")]) for val in patient_info])
            ),
            html.Div([],id="interal-switch-info"),
            daq.BooleanSwitch(id='interval-switch', on=False, color="#666666", ),

        ], className="three columns"),
        html.Div([
            html.Div(dcc.Graph(id="box-plot")),

        ], className="seven columns"),
    html.Div([html.Img(src=app.get_asset_url('table.png'), className="img"),
              html.Img(src=app.get_asset_url('feet.png'), className="img")], className="two columns")
],className="patient_details")


#################################################### CONTROL AREA - BUTTONS, SLIDERS AND SO ON ####################################################

dff = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
control_div = html.Div([
            # html.Div([
            #     html.Div([html.Span(html.H3("ANONAMALY"))], className="eight columns"),
            #     html.Div([html.Span(html.H3("CONTROLING DATA DISPLAY"))], className="four columns")],className="twelve columns"),
            html.Div([
                html.Div([
                    html.Label("From when?"),
                    dcc.Input(id='time1-input', placeholder="%Y-%m-%d %H:%M:%S"),
                    html.Label("Untill when?"),
                    dcc.Input(id='time2-input', placeholder="%Y-%m-%d %H:%M:%S"),
                    html.Div(html.Label('How many last values?')),
                    dcc.Slider(id='time-period', value=5, min=5, max=100, step=1),
                    html.Div(id='time-period-value')
                ],className="six columns"),
            ], className="twelve columns"),
],className="twelve columns")


#################################################### APPLICATION LAYOUT ####################################################



app.layout = html.Div([
    menu_div,
    patient_div,
    html.Div(dcc.Graph(id = "real-time-plot",animate = True),className="twelve columns"),
    dcc.Interval(
        id = 'plot-update',
        interval = 1000
    ),
    # table,
   control_div
])



@app.callback(
            [Output("real-time-plot","figure"),
            Output("box-plot","figure")],
            [Input("plot-update", "n_intervals"),
            Input('patient-picker', 'value'),
            Input("time-period",'value'),
            Input('time1-input','value'),
            Input('time2-input', 'value')]
    )
def update(data,selected_patient,time_period,time1,time2):
    df = getTracesBetweenTimes(conn,selected_patient, time1, time2,time_period)
    return (createScatterPlot(df),
            createBoxPlot(df))


# ['firstname_v', 'secondname_v', 'birthdate_v', 'is disabled?_v']
@app.callback(
            [Output("firstname_v","children"),
            Output("secondname_v","children"),
            Output("birthdate_v","children"),
            Output("is disabled?_v","children")],
            [Input('patient-picker', 'value')]
    )
def update_info(selected_patient):
    info = getUserInfo(conn,selected_patient)
    if info[2]==0:
        isdisabled="No"
    else:
        isdisabled="Yes"
    return (info[3],info[4],info[1],isdisabled);


@app.callback(
    [Output("plot-update", "disabled"),
    Output("interal-switch-info","children")],
    [Input("interval-switch","on")],
    [State("plot-update", "disabled")],
)
def toggle_interval(n, disabled):
    if n:
        state = "on"
    else:
        state="off"
    return (n,"Pause on plots' updating is "+state)


@app.callback(
    dash.dependencies.Output('time-period-value', 'children'),
    [dash.dependencies.Input('time-period', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)

@app.callback(
    Output("table-switch-info","children"),
    [Input("table-switch-","on")],
)
def toggle_interval(n, disabled):
    if n:
        state = "on"
    else:
        state="off"
    return (n,"Pause on plots' updating is "+state)



app.run_server()