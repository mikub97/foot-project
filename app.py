from flask import Flask
import dash
import dash_html_components as html
import components as c

app = dash.Dash(__name__)


app.layout = html.Div(children=[
        html.H1(children='Real time feet movement analysis'),
        html.Div(className='row',  # Define the row element
                 children=[
                     html.Div(className='four columns div-user-controls',children=[
                         html.H2('Dash - STOCK PRICES'),
                         html.P('''Visualising time series with Plotly - Dash'''),
                         html.P('''Pick one or more stocks from the dropdown below.'''),
                     ]),  # Define the left element
                     html.Div(className='eight columns div-for-charts bg-grey',children=[c.components])  # Define the right element
                 ]),
    ]);




if __name__ == '__main__':
    app.run_server(debug=True)
