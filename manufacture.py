from datetime import date, datetime
import plotly .graph_objs as go

from listener import getTracesBetween, getTraces

sensors = ["L0","L1","L2","R0","R1","R2"]
colors = ['rgba(99, 160, 203, 0.5)', 'rgba(255, 166, 87, 0.5)', 'rgba(108, 189, 108, 0.5)',
          'rgba(226, 104, 105, 0.5)', 'rgba(180, 149, 209, 0.5)', 'rgba(175, 137, 129, 0.5)']
def createScatterPlot(df):
    # print(df)
    data = []

    for sensor, cls in zip(sensors, colors):
        X = df["T"]
        Y = df[sensor]
        data.append(go.Scatter(
            x=list(X),
            y=list(Y),
            name=sensor,
            mode='lines',
            fillcolor=cls,
            opacity=0.7,
            marker={'size': 15},
        ))
    fig = go.Figure(data=data)
    try:
        fig.update_layout(
            margin=dict(t=150),
            xaxis=dict(title="time", range=[min(df['T']), max(df['T'])], type="date"),
            yaxis=dict(title="preasure",
                       range=[min(df[sensors].values.min(axis=1)), max(df[sensors].values.max(axis=1)) + 20],
                       type="linear"),
            # annotations=annot,
            hovermode='closest'
        )
    except:
        print('Error, df is empty')
    anomal = df[((df['L0_ANOMALY']==1) |(df['L1_ANOMALY']==1) |(df['L2_ANOMALY']==1) |(df['R0_ANOMALY']==1) |(df['R1_ANOMALY']==1) |(df['R2_ANOMALY']==1))].values.tolist()
    for r in anomal:
        fig.add_shape(type='line',
                      x0=r[0],
                      y0=0,
                      x1=r[0],
                      y1=1,
                      line=dict(color='red', dash='dot'),
                      xref='x',
                      yref='paper'
                      )
        fig.add_annotation(dict(font=dict(color="black", size=12),
                                # x=x_loc,
                                x=r[0],
                                y=1.06,
                                showarrow=False,
                                text='!',
                                textangle=0,
                                xref="x",
                                yref="paper"
                                ))

    return fig


def createBoxPlot(df):

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
        xaxis=dict(
            title="sensor",
        ),
        yaxis=dict(
            title="pressure",
            type="linear",
            autorange=True,
            tickmode="array",
            showgrid=True,
            zeroline=True,
            nticks=10,
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
