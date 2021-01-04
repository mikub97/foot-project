import dash_core_components as dcc
import dash_html_components as html



## Dash core components to create by cirit
#for now its



components  = [];

components.append(dcc.Graph( id='example-graph',
                         figure={'data': [
                             {'x': [1, 2, 3], 'y': [4, 1, 2],
                              'type': 'bar', 'name': 'SF'},
                             {'x': [1, 2, 3], 'y': [2, 4, 5],
                              'type': 'bar', 'name': u'Montréal'},
                         ],'layout': {'title': 'Dash Data Visualization',
                                      'font': {'size': 8}
                                      }
                         }))

components.append(html.P('''BLABLABLBAL'''))
components.append(dcc.Graph( id='second-graph',
                         figure={'data': [
                             {'x': [1, 2, 3], 'y': [4, 1, 2],
                              'type': 'bar', 'name': 'SF'},
                             {'x': [1, 2, 3], 'y': [2, 4, 5],
                              'type': 'bar', 'name': u'Montréal'},
                         ],'layout': {'title': 'Dash Data Visualization',
                                      'font': {'size': 8}
                                      }
                }))