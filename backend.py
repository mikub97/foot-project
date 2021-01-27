from datetime import date, datetime
import pandas as pd
import numpy as np
import plotly.express as px
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly .graph_objs as go
import sqlite3
import threading
#Init
from listener import get_users, getTraces, fetch_data, getTracesBetween, prepare

visualize_clicks=0
time = 2 #Secs on PLOT
historical_display = False
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()
prepare()
storageThread = threading.Thread(name="fetch",
                                 target=fetch_data,
                                 args=(conn, ))

storageThread.start()
users = get_users(c)
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

statistical_vs = ['avg','min','max','sth',"some",
                  'avg1','min1','max1','sth1',"some1",
                  'avg2','min2','max2','sth2',"some2",
                  'avg3','min3','max3','sth3',"some3",
                  'avg4','min4','max4','sth4',"some4"]
nrows=5
patient_info = ["firstname","secondname",'birthdate','is disabled?']
tab =  html.Div([
                html.Div(
                    html.Table(
                        # Header
                        [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                        # Body
                        ([html.Tr([html.Td(val),html.Td(val+"_v",id=val+"_v")]) for val in statistical_vs][0:nrows])),className="three columns")
                ,
                html.Div(
                    html.Table(
                        # Header
                        [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                        # Body
                        ([html.Tr([html.Td(val),html.Td(val+"_v",id=val+"_v")]) for val in statistical_vs][nrows:nrows*2])),className="three columns"),
                html.Div(
                    html.Table(
                        # Header
                        [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                        # Body
                        ([html.Tr([html.Td(val),html.Td(val+"_v",id=val+"_v")]) for val in statistical_vs][nrows*2:nrows*3])),className="three columns"),
                html.Div(
                    html.Table(
                        # Header
                        [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                        # Body
                        ([html.Tr([html.Td(val),html.Td(val+"_v",id=val+"_v")]) for val in statistical_vs][nrows*3:nrows*4])),className="three columns")
            ])
patient_div =html.Div([
        html.Div([
            dcc.Dropdown(id='patient-picker', options=patient_picker_options, value=users[0]['secondname'], placeholder="Select a user",),
            html.H3("PATIENT INFO"),
            html.Table(
                ([html.Tr([html.Td(val), html.Td(val + "_v", id=val + "_v")]) for val in patient_info]))
        ], className="three columns"),
        html.Div([
            html.Div(dcc.Graph(id="box-plot")),

        ], className="seven columns"),
    html.Div([html.Img(src=app.get_asset_url('table.png'), className="img"),
              html.Img(src=app.get_asset_url('feet.png'), className="img")], className="two columns")
],className="patient_details")


#################################################### CONTROL AREA - BUTTONS, SLIDERS AND SO ON ####################################################

control_div = html.Div([
            html.Div([
                html.Div([html.Span(html.H3("REAL-TIME MEASUREMENT"), className="logo")], className="four columns"),
                html.Div([html.Span(html.H3("DISPLAY SETTINGS"))], className="four columns"),
                html.Div([html.Span(html.H3("VIEW HISTORICAL DATA"))], className="four columns")],className="twelve columns"),
            html.Div([
                html.Label("Real time values"),
                daq.BooleanSwitch(id='real-switch',on=True, color = "#666666",),
                html.Label('Refresh rate'),
                dcc.Slider(id='refresh-slider', value=20, min=10, max=40, step=1,),
            ], className="three columns"),

            html.Div([
                html.Div(html.Label('How many last values?')),
                dcc.Slider(id='time-period', value=20, min=5, max=100, step=1,),
            ], className="four columns"),
            html.Div([
                dcc.Input(id='time1-input', placeholder="%Y-%m-%d %H:%M:%S"),
                dcc.Input(id='time2-input', placeholder="%Y-%m-%d %H:%M:%S")]
            ,className="four columns"),
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
    df = getTracesBetweenTimes(selected_patient, time1, time2,time_period)
    data = []
    for s in sensors:
        X = df["T"]
        Y = df[s]
        data.append(go.Scatter(
            x=list(X),
            y=list(Y),
            name=s,
            mode='lines',
            opacity=0.7,
            marker={'size': 15},
        ))

    scatter_plot ={"data": data, "layout": go.Layout(
        xaxis=dict(range=[min(X), max(X)]),
        yaxis=dict(range=[min(Y), max(Y)]),
        hovermode='closest')}


    colors = ['rgba(99, 160, 203, 0.5)', 'rgba(255, 166, 87, 0.5)', 'rgba(108, 189, 108, 0.5)',
              'rgba(226, 104, 105, 0.5)', 'rgba(180, 149, 209, 0.5)', 'rgba(175, 137, 129, 0.5)']
    box_plot = go.Figure()
    for sensor, cls in zip(sensors, colors):
        box_plot.add_trace(go.Box(
            y=df[sensor],
            name=sensor,
            boxpoints='all',
            jitter=0.5,
            whiskerwidth=0.2,
            fillcolor=cls,
            marker_size=2,
            line_width=1)
        )
    box_plot.update_layout(
        title='Sensor Statistics',
        yaxis=dict(
            autorange=True,
            showgrid=True,
            zeroline=True,
            dtick=5,
            gridcolor='rgb(255, 255, 255)',
            gridwidth=1,
            zerolinecolor='rgb(255, 255, 255)',
            zerolinewidth=2,
        ),
        margin=dict(
            l=40,
            r=30,
            b=80,
            t=100,
        ),
        paper_bgcolor='rgb(243, 243, 243)',
        plot_bgcolor='rgb(243, 243, 243)',

    )
    return (scatter_plot,box_plot)

# @app.callback(Output("box-plot","figure"),
#             [Input("plot-update", "n_intervals"),
#              Input('patient-picker', 'value'),
#              Input("time-period",'value'),
#              Input('time1-input','value'),
#              Input('time2-input', 'value')])
# def update(data,selected_patient,time_period,time1,time2):
#     df = getTracesBetweenTimes(selected_patient, time1, time2,time_period)
#     colors = ['rgba(99, 160, 203, 0.5)', 'rgba(255, 166, 87, 0.5)', 'rgba(108, 189, 108, 0.5)',
#               'rgba(226, 104, 105, 0.5)', 'rgba(180, 149, 209, 0.5)', 'rgba(175, 137, 129, 0.5)']
#     fig = go.Figure()
#     for sensor, cls in zip(sensors, colors):
#         fig.add_trace(go.Box(
#             y=df[sensor],
#             name=sensor,
#             boxpoints='all',
#             jitter=0.5,
#             whiskerwidth=0.2,
#             fillcolor=cls,
#             marker_size=2,
#             line_width=1)
#         )
#     fig.update_layout(
#         title='Sensor Statistics',
#         yaxis=dict(
#             autorange=True,
#             showgrid=True,
#             zeroline=True,
#             dtick=5,
#             gridcolor='rgb(255, 255, 255)',
#             gridwidth=1,
#             zerolinecolor='rgb(255, 255, 255)',
#             zerolinewidth=2,
#         ),
#         margin=dict(
#             l=40,
#             r=30,
#             b=80,
#             t=100,
#         ),
#         paper_bgcolor='rgb(243, 243, 243)',
#         plot_bgcolor='rgb(243, 243, 243)',
#
#     )
#     return fig

def validate(date_text):
    if date_text== None:
        return False
    try:
        datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    return True

def getTracesBetweenTimes(patient, time1,time2,time_period=30):
    #checking the time1 and time2 format correct?
    if validate(time1):
        if validate(time2):
            return getTracesBetween(conn,patient,time1,time2)
        else:
            return getTracesBetween(conn,patient,time1,datetime.now())
    else:
        return getTraces(conn,patient)[:][:time_period]



@app.callback(Output("patient-firstname","children"),
             [Input('recalc-historical', 'n-clicks'),
              Input('visualize-historical','n-clicks'),
              Input('historical-date-range-picker','value')])
def hisotrical(selected_patient,eqw, rew, res):
    return "fasdlkjflkdsamlkfslfslnfdslknfdsa"

app.run_server()