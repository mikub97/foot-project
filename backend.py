import pandas as pd
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly .graph_objs as go
import sqlite3

#Init
from listener import get_users

time = 2 #Secs on PLOT
conn = sqlite3.connect("realtime.db", check_same_thread=False)#DB connection
c = conn.cursor()


users = get_users(c)
sensors = ["L0","L1","L2","R0","R1","R2",]
patient_picker_options = []
for user in users:
    patient_picker_options.append({'label': str(user['firstname'] + " " + user['secondname']), 'value':user['secondname']})

app = dash.Dash(__name__,assets_url_path="assets",) #Here we implement the app but for now smth really basic is included

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

patient_div =html.Div([
        html.Div([
            dcc.Dropdown(id='patient-picker', options=patient_picker_options, value=users[0]['secondname'], placeholder="Select a user",),
            html.H3("PATIENT INFO"),
            html.Table(
                ([html.Tr([html.Td(val), html.Td(val + "_v", id=val + "_v")]) for val in patient_info]))
        ], className="three columns"),
        html.Div([
            html.Div([
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
                        ([html.Tr([html.Td(val),html.Td(val+"_v",id=val+"_v")]) for val in statistical_vs][nrows*3:nrows*4])),className="three columns")])

        ], className="seven columns"),
    html.Div([html.Img(src=app.get_asset_url('table.png'), className="img"),
              html.Img(src=app.get_asset_url('feet.png'), className="img")], className="two columns")
],className="patient_details")


#################################################### CONTROL AREA - BUTTONS, SLIDERS AND SO ON ####################################################

control_div = html.Div([
        html.Div([
            html.Label('How many last values?'),
            dcc.Slider(id='time-period', value=20, min=10, max=40, step=1),
            html.Label('Refresh rate'),
            dcc.Slider(id='refresh_slider', value=20, min=10, max=40, step=1),
            html.Label("Real time values"),
            daq.BooleanSwitch(id='real_switch',on=True)] ,className="four columns"),
        html.Div([
            html.Div([
                html.Table(
                        [html.Tr([html.Td("From when?"),html.Td(dcc.Input(id="from"))]),
                          html.Tr([html.Td("Till when"), html.Td(dcc.Input(id="till"))]),]),
                html.Button('Submit(online in non-real-time)', id='submit-historical'),
            ],className="six columns"),

            html.Div([
                html.Table(
                    [html.Tr([html.Td("blablabdsla"), html.Td(dcc.Input(id="bldsa"))]),
                     html.Tr([html.Td("blablabla"), html.Td(dcc.Input(id="blabla"))]),
                     ]),
                html.Button('Submit blabla', id='submit-blabla'),
            ], className="six columns")
        ],className="eight columns")
        # html.Div([
        #     html.Button('Real-Time Values', id='real-time-run'),
        #     html.Label("Refresh time"),
        #     dcc.Input(id="refresh_time"),
        #     html.Label("From when?"),
        #     dcc.Input(id="from"),
        #     html.Label("Until when?"),
        #     dcc.Input(id="until"),
        #     html.Button('Submit(online in non-real-time)', id='submit-historical')], className="three columns")
])



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
    dash.dependencies.Output('boolean-switch-output', 'children'),
    [dash.dependencies.Input('my-boolean-switch', 'on')])
def update_output(on):
    if on:
        return 'Display real-time values is on'
    else:
        return 'Display real-time values is off'



@app.callback(Output("real-time-plot","figure"),
            [Input("plot-update", "n_intervals"),
             Input('patient-picker', 'value'),
             Input("time-period",'value')])
def update(data,selected_patient,time_period):
    c.execute("SELECT TRACETIME,L0,L1,L2,R0,R1,R2 FROM 'traces' WHERE SECONDNAME = '"+str(selected_patient)+"' ORDER BY TRACETIME DESC ")
    rows = c.fetchall()
    dataSQL = [list(row) for row in rows]
    labels = ["T","L0",'L1','L2','R0','R1','R2']
    df = pd.DataFrame.from_records(dataSQL, columns=labels)
    data = []
    for s in sensors:
        X = df["T"][:time_period]
        Y = df[s][:time_period]

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

@app.callback(Output("patient-firstname","children"),
             [Input('patient-picker', 'value')])
def update(selected_patient):
    return "fasdlkjflkdsamlkfslfslnfdslknfdsa"


app.run_server()