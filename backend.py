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

statistical_values = ['avg','min','max','sth','avg1','min1','max1','sth1','avg2','min2','max2','sth2','avg3','min3','max3','sth4']
nrows=4
patient_info = ["firstname","secondname",'birthdate','is disabled?']
app.layout = html.Div([
    html.H1("Real time plot"),
    html.Div([
        html.Div([
            dcc.Dropdown(id='patient-picker', options=patient_picker_options, value=users[0]['secondname']),
            html.H3("PATIENT INFO"),
            html.Table(
                ([html.Tr([html.Td(val), html.Td(val + "_value", id=val + "_value")]) for val in patient_info]))
        ], className="two columns"),
        html.Div([
            html.Span(html.H3("STATISTICAL DATA")),
            html.Div(
                html.Table(
                    # Header
                    [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                    # Body
                    ([html.Tr([html.Td(val),html.Td(val+"_value",id=val+"_value")]) for val in statistical_values][0:nrows])),className="three columns")
            ,
            html.Div(
                html.Table(
                    # Header
                    [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                    # Body
                    ([html.Tr([html.Td(val),html.Td(val+"_value",id=val+"_value")]) for val in statistical_values][nrows:nrows*2])),className="three columns"),
            html.Div(
                html.Table(
                    # Header
                    [html.Tr([html.Th(col) for col in ["MEASURE","VALUE"]])] +
                    # Body
                    ([html.Tr([html.Td(val),html.Td(val+"_value",id=val+"_value")]) for val in statistical_values][nrows*2:nrows*3])),className="three columns"),


        ], className="six columns"),
        html.Div(html.Img(src=app.get_asset_url('table_foot.png'),className="img"),className="four columns")
    ],className="patient_details"),
    html.Div(dcc.Graph(id = "real-time-plot",animate = True),className="twelve columns"),
    dcc.Interval(
        id = 'plot-update',
        interval = 1000
    ),
    html.Div([
        html.Div([
            html.Label("          PLACE FOR MANY OTHER CONTROL BUTTONS ETC.            "),
            html.Label('How many last values?'),
            dcc.Slider(id='time-period', value=20, min=10, max=40, step=1)
            ] ,className="six columns")
    ])
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