import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
 

app = dash.Dash()
 
df = pd.read_csv('data/sensors.csv')

lastname_options = []
for lastname in df['lastname'].unique():
    lastname_options.append({'label':str(lastname),'value':lastname})

app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Dropdown(id='patient-picker',options=lastname_options,value=df['lastname'].min())
])
 
@app.callback(Output('graph-with-slider', 'figure'),
              [Input('patient-picker', 'value')])
def update_figure(selected_patient):
    filtered_df = df[df['lastname'] == selected_patient]
    traces = []
    for sensor_name in filtered_df['trace.footname'].unique():
        df_by_sensor = filtered_df[filtered_df['trace.footname'] == sensor_name]
        traces.append(go.Scatter(
            x=df_by_sensor['birthdate'],#Will change it to period,
            y=df_by_sensor['trace.value'],
            text=df_by_sensor['firstname'],
            mode='markers',
            opacity=0.7,
            marker={'size': 15},
            name=sensor_name
        ))
    print(traces)
    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'type': 'log', 'title': 'Period'},
            yaxis={'title': 'Trace Value'},
            hovermode='closest'
        )
    }
 
if __name__ == '__main__':
    app.run_server()
