from datetime import date, datetime
import plotly .graph_objs as go

from listener import getTracesBetween, getTraces

sensors = ["L0","L1","L2","R0","R1","R2"]

def createScatterPlot(df):
    # print(df)
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
    fig = go.Figure(data=data)
    fig.update_layout(go.Layout(
        xaxis=dict(range=[min(X), max(X)]),         ## wronng !
        yaxis=dict(range=[min(Y), max(Y)]),         ## wronng !
        hovermode='closest'))

    anomal = df[((df['L0_ANOMALY']==1) |(df['L1_ANOMALY']==1) |(df['L2_ANOMALY']==1) |(df['R0_ANOMALY']==1) |(df['R1_ANOMALY']==1) |(df['R2_ANOMALY']==1))].values.tolist()
    annot = []
    for r in anomal:
        annot.append(dict(
                showarrow=True,
                x=r[0],
                y=500,
                text="ANOMALY ! ",
                xanchor="left",
                xshift=10,
                opacity=0.7))

    fig.update_layout(
            xaxis=dict(type="date"),
            yaxis=dict(type="linear"),
            annotations=annot
    )
    return fig


def createBoxPlot(df):

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
            autorange=False,
            range=[0,1050],
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
    return box_plot


def getTracesBetweenTimes(conn,patient, time1,time2,time_period=30):
    #checking the time1 and time2 format correct?
    if validate(time1):
        if validate(time2):
            return getTracesBetween(conn,patient,time1,time2)
        else:
            return getTracesBetween(conn,patient,time1,datetime.now())
    else:
        return getTraces(conn,patient)[:][:time_period]


def validate(date_text):
    if date_text== None:
        return False
    try:
        datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    return True
