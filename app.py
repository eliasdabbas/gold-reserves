import base64

import pandas as pd
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

img_base64 = base64.b64encode(open('./gold-ingots-golden-treasure-47047.jpeg', 'rb').read()).decode('ascii')
gold_reserves = pd.read_csv('gold_quarterly_reserves_ounces.csv',
                            dtype={'Country Name': 'category'})
gold_reserves['Time Period'] = [pd.Period(p) for p in gold_reserves['Time Period']]
gold_reserves['tonnes'] = gold_reserves['Value'].div(32_000)

periods = sorted(gold_reserves['Time Period'].astype('str').unique())

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

server = app.server

app.layout = dbc.Container([
    html.Br(), html.Br(),
    dbc.Row([
        dbc.Col([
            html.H2(html.B('International Gold Reserves'),
                    style={'color': '#A29061'}),
        ]),
    ], style={'text-align': 'center'}),
    dbc.Row([
        dbc.Col(lg=1),
        dbc.Col([
            html.Div(id='slider_output_quarter'),
            dcc.Slider(id='quarter',
                       included=False,
                       marks={i: str(periods[i])
                              for i in range(0, len(periods)-1, 16)},
                       min=0, max=len(periods) - 1,
                       value=len(periods) - 1),
            html.Br(),
            dcc.Loading([
                dcc.Graph(id='top_countries_chart',
                          config={'displayModeBar': False}),
            ]),
        ], lg=8),
        dbc.Col([
            html.Div(
                [html.Br() for i in range(5)] + [
                    html.Img(src='data:image/png;base64,' + img_base64,
                             width=300, style={'display': 'inline-block'}),
                    html.Br(),
                    html.B('Data: '),
                    html.A(href='https://data.imf.org',
                           children='International Monetary Fund'),
                    html.Br(),
                    html.B('Source: '),
                    html.A(href='https://github.com/eliasdabbas/gold-reserves',
                           children='Code on GitHub')
            ])
        ]),
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col(lg=1),
        dbc.Col([
            dcc.Dropdown(id='countries',
                         placeholder='Select country(s) and/or region(s):',
                         multi=True,
                         value=['Turkey', 'Russian Federation',
                                'China, P.R.: Mainland'],
                         options=[{'label': c, 'value': c}
                                  for c in sorted(gold_reserves['Country Name'].unique())]),
            html.Br(),
            html.Div(id='slider_output_quarters'),
            dcc.RangeSlider(id='quarters',
                            marks={i: str(periods[i])
                                   for i in range(0, len(periods) - 1, 16)},
                            min=0, max=len(periods) - 1,
                            value=[len(periods) - 41, len(periods) - 1]),
        ], lg=8),
        dbc.Col([
        ], lg=7),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Loading([
                dcc.Graph(id='chart_by_country_quarter',
                          config={'displayModeBar': False}),
            ]),
        ], lg=7),
        dbc.Col([
            dcc.Loading([
                dcc.Graph(id='chart_top_gainers',
                          config={'displayModeBar': False}),
            ]),

        ], lg=4),
    ]),
    html.Br(), html.Br(), html.Br(),
], style={'background-color': '#eeeeee'}, fluid=True)

excluded_regions = ['World', 'Advanced Economies', 'Euro Area',
                    'Europe', 'CIS',
                    'Central African Economic and Monetary Community',
                    'Emerging and Developing Europe',
                    'Emerging and Developing Countries',
                    'Middle East, North Africa, Afghanistan, and Pakistan',
                    'Emerging and Developing Asia', 'Western Hemisphere']

@app.callback(Output('chart_top_gainers', 'figure'),
              [Input('quarters', 'value')])
def plot_top_gainers_losers(quarters):
    if quarters is None:
        raise PreventUpdate
    quarters = [pd.Period(periods[quarters[0]]),
                pd.Period(periods[quarters[1]])]
    df = (gold_reserves
          [gold_reserves['Time Period']
           .isin([quarters[0], quarters[1]]) &
           (~gold_reserves['Country Name'].isin(excluded_regions))]
          .__getitem__(lambda df: df.duplicated(['Country Name'], keep=False))
          .pivot(index='Country Name', values='tonnes', columns='Time Period')
          .assign(diff=lambda df: df[max(df.columns)].sub(df[min(df.columns)]))
          .sort_values('diff').reset_index())
    df = df.head(10).append(df.tail(10))

    fig = go.Figure()
    fig.add_bar(x=df['diff'], y=df['Country Name'], orientation='h',
                marker={'color': ['red'] * 10 + ['green'] * 10})
    fig.layout.height = 600
    fig.layout.paper_bgcolor = '#eeeeee'
    fig.layout.plot_bgcolor = '#eeeeee'
    fig.layout.xaxis.title = 'Tonnes'
    fig.layout.margin = {'r': 10}
    title_text = ('Top gold buyers and sellers: ' + str(quarters[1]) +
                  '  vs ' + str(quarters[0]) +
                  '<br>(amount of gold added/reduced to reserves)')
    fig.layout.title = {'font': {'color': '#A29061'}, 'text': title_text}
    fig.layout.font = {'color': '#A29061'}
    return fig.to_dict()


@app.callback(Output('top_countries_chart', 'figure'),
              [Input('quarter', 'value')])
def plot_top_countries(quarter):
    if quarter is None:
        raise PreventUpdate
    quarter = pd.Period(periods[quarter])
    df = (gold_reserves
          [(gold_reserves['Time Period']==quarter) &
           (~gold_reserves['Country Name'].isin(excluded_regions))]
          .sort_values('tonnes', ascending=False))
    fig = go.Figure()
    fig.add_bar(x=df['tonnes'][:15][::-1],
                y=[str(x) + ': ' for x in range(len(df['Country Name'][:15]), 0, -1)] + df['Country Name'][:15][::-1].astype('str'),
                marker={'color': '#A29061'},
                orientation='h')
    fig.layout.paper_bgcolor = '#eeeeee'
    fig.layout.plot_bgcolor = '#eeeeee'
    fig.layout.height = 600
    fig.layout.title = 'Top Countries in Gold reserves ' + str(quarter)
    fig.layout.xaxis.title = 'Tonnes'
    fig.layout.font = {'color': '#A29061'}
    return fig.to_dict()


@app.callback(Output('slider_output_quarters', 'children'),
              [Input('quarters', 'value')])
def display_selected_quarters(quarters):
    if quarters is None:
        raise PreventUpdate
    return ('Selected time range - from: ' +
            ' to: '.join([periods[quarters[0]], periods[quarters[1]]]))


@app.callback(Output('slider_output_quarter', 'children'),
              [Input('quarter', 'value')])
def display_selected_quarter(quarters):
    if quarters is None:
        raise PreventUpdate
    return 'Selected quarter: ' + str(periods[quarters])


@app.callback(Output('chart_by_country_quarter', 'figure'),
              [Input('countries', 'value'),
               Input('quarters', 'value')])
def plot_countries_in_quarters(countries, quarters):
    if countries is None or quarters is None:
        raise PreventUpdate
    quarters = [pd.Period(periods[quarters[0]]),
                pd.Period(periods[quarters[1]])]
    fig = go.Figure()
    for country in countries:
        df = (gold_reserves
              [(gold_reserves['Country Name'] == country) &
               gold_reserves['Time Period'].between(quarters[0], quarters[1])]
              .sort_values('Time Period'))
        fig.add_scatter(x=df['Time Period'].astype('str'),
                        y=df['tonnes'],
                        mode='lines+markers',
                        name=country)
    fig.layout.paper_bgcolor = '#eeeeee'
    fig.layout.plot_bgcolor = '#eeeeee'
    fig.layout.hovermode = 'x'
    fig.layout.height = 600
    fig.layout.title = ('Quarterly gold reserves in tonnes - IMF Data<br>' +
                        ', '.join(countries))
    fig.layout.yaxis.title = 'Tonnes'
    fig.layout.legend = {'x': 0, 'y': -0.2, 'orientation': 'h'}
    fig.layout.margin = {'r': 10}
    fig.layout.font = {'color': '#A29061'}
    return fig.to_dict()


if __name__ == '__main__':
    app.run_server()
