import requests
from google.transit import gtfs_realtime_pb2
import dash
import dash_html_components as html
import dash_core_components as dcc
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
import time
from geopy.geocoders import Nominatim

# Constants
api_key = 'OKrlDQxvcM5lb8vguvZK58pZmgtYqFGb1dJ3'
header = {'Authorization': 'apikey ' + api_key}
url = "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses"
mapbox_access_token = 'pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w'
refresh_time = 4000
scl = [[0, 'rgb(0, 111, 199)'], [0.5, 'rgb(237, 92, 9)'], [1, 'rgb(183, 7, 7)']]
colours = dict(main='#161616', subs='#212121', plots='#2d2d2d')

# Pull static data
facilities = pd.read_csv("LocationFacilityData.csv")
facilities = facilities[['LOCATION_NAME', 'FACILITIES', 'ACCESSIBILITY']]
amenities, accessies = facilities.FACILITIES.values, facilities.ACCESSIBILITY.values

for index, items in enumerate(amenities):
    if items is not np.nan:
        amenities[index] = items.split("|")

for items in amenities:
    if items is not np.nan:
        for index, value in enumerate(items):
            items[index] = value.strip()

for index, items in enumerate(accessies):
    if items is not np.nan:
        accessies[index] = items.split("|")

for items in accessies:
    if items is not np.nan:
        for index, value in enumerate(items):
            items[index] = value.strip()

# Filter static data
bike_racks, bike_lockers = np.zeros(len(amenities), dtype='object'), np.zeros(len(amenities), dtype='object')
emergency, car_park = np.zeros(len(amenities), dtype='object'), np.zeros(len(amenities), dtype='object')
opal, toilets = np.zeros(len(amenities), dtype='object'), np.zeros(len(amenities), dtype='object')
wheelchairs, stairs = np.zeros(len(accessies), dtype='object'), np.zeros(len(amenities), dtype='object')
lifts = np.zeros(len(accessies), dtype='object')

for index, set in enumerate(amenities):
    if set is not np.nan:
        if "Bike racks" in set:
            bike_racks[index] = 'Yes'
        else:
            bike_racks[index] = 'No'

        if "Bike lockers" in set:
            bike_lockers[index] = 'Yes'
        else:
            bike_lockers[index] = 'No'

        if "Emergency help point" in set:
            emergency[index] = 'Yes'
        else:
            emergency[index] = 'No'

        if "Commuter car park" in set:
            car_park[index] = 'Yes'
        else:
            car_park[index] = 'No'

        if "Opal card top up or single trip ticket machine" in set:
            opal[index] = 'Yes'
        else:
            opal[index] = 'No'

        if "Toilets" in set:
            toilets[index] = 'Yes'
        else:
            toilets[index] = 'No'

    else:
        bike_racks[index] = 'No'
        bike_lockers[index] = 'No'
        emergency[index] = 'No'
        car_park[index] = 'No'
        opal[index] = 'No'
        toilets[index] = 'No'

for index, set in enumerate(accessies):
    if set is not np.nan:
        if "This location is wheelchair accessible" in set:
            wheelchairs[index] = 'Yes'
        else:
            wheelchairs[index] = 'No'

        if "Stairs" in set:
            stairs[index] = 'Yes'
        else:
            stairs[index] = 'No'

        if "Lift" in set or "Escalator" in set:
            lifts[index] = 'Yes'
        else:
            lifts[index] = 'No'
    else:
        wheelchairs[index] = 'No'
        stairs[index] = 'No'
        lifts[index] = 'No'

# Assign to pandas dataframe
facilities['Bike Racks'], facilities['Bike Lockers'] = bike_racks, bike_lockers
facilities['Emergency Help Point'], facilities['Car Park'] = emergency, car_park
facilities['Opal/Tickets'], facilities['Toilets'], facilities['Wheelchairs']= opal, toilets, wheelchairs
facilities["Stairs"], facilities["Lifts"] = stairs, lifts


# Pull live data
def get_live_data():
    train_positions = requests.get(url, headers=header)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(train_positions.content)

    latitudes = np.zeros(len(feed.entity))
    longitudes = np.zeros(len(feed.entity))
    occupancies = np.zeros(len(feed.entity))
    routes = np.zeros(len(feed.entity), dtype=object)
    speeds = np.zeros(len(feed.entity))

    for index, entity in enumerate(feed.entity):
        latitudes[index] = entity.vehicle.position.latitude
        longitudes[index] = entity.vehicle.position.longitude
        occupancies[index] = entity.vehicle.occupancy_status
        routes[index] = entity.vehicle.trip.route_id
        speeds[index] = entity.vehicle.position.speed

    # def rounder(series):
    #     for i, value in enumerate(series):
    #         value = float(value)
    #         series[i] = np.around(value, decimals=3)
    #
    #     return series

    occupancies_text = np.zeros(len(occupancies), dtype=object)
    for i, value in enumerate(occupancies):
        if value == 0:
            occupancies_text[i] = 'Empty'
        elif value < 3:
            occupancies_text[i] = 'Average'
        elif value < 5:
            occupancies_text[i] = 'Above Average'
        else:
            occupancies_text[i] = 'Full'

    for i, value in enumerate(routes):
        routes[i] = value.split('_', 1)[-1]

    speeds = np.array(speeds, dtype=object)*3.6
    for i, value in enumerate(speeds):
        value = np.around(value, decimals=2)
        speeds[i] = str(value)

    # latitudes = rounder(latitudes)
    # longitudes = rounder(longitudes)

    df = {'latitudes': latitudes, 'longitudes': longitudes, 'occupancies': occupancies,
          'occupancy_text': occupancies_text, 'routes': routes, 'speeds': speeds}

    df = pd.DataFrame(df)

    return df


# Get locations from strings
def get_pos(address):
    geolocater = Nominatim(scheme='http')
    location = geolocater.geocode(address)

    return location.latitude, location.longitude


# Get location from name
def get_spot(item):
    for index, row in facilities.iterrows():
        if row['LOCATION_NAME'] == item:
            return row.values[3:]

# Initial graph
initial_df = get_live_data()
data = [dict(
    type='scattermapbox',
    lon=initial_df.longitudes,
    lat=initial_df.latitudes,
    text="Bus Route: " + initial_df.routes + ", \n \n" + "Occupancy: " + initial_df.occupancy_text + ", \n \n" +
         "Speed: " + initial_df.speeds + "km/h",
    marker=dict(
        size=10,
        opacity=0.6,
        color=initial_df.occupancies,
        colorscale=scl,
    )
)]

layout = dict(height=500, font=dict(color='#CCCCCC'), titlefont=dict(color='#CCCCCC', size='14'), title="Live Bus Map",
              margin=dict(l=35, r=35, b=35, t=45), hovermode="closest", plot_bgcolor="#191A1A",
              paper_bgcolor=colours['subs'], mapbox=dict(accesstoken=mapbox_access_token, style="dark", center=dict(
                lon=151, lat=-33.8), zoom=9,))
fig = dict(data=data, layout=layout)

# Creating dash app
app = dash.Dash(__name__)
server = app.server
app.title = "Transport Dashboard"
app.css.append_css({'external_url': 'https://rawgit.com/JalalElwazze/livebuses/master/app.css'})


# App layout
app.layout = html.Div(
    html.Div(
    [
        # Heading
        html.Div([
            html.H2("Real Time Transport Tracker"),
        ],
            style={'textAlign': 'center',
                   'margin-top': '50', 'color': '#EFEFEF'}
        ),

        # First Row - Toolbar
        html.Div(
            [
                # Address search
                html.Div(
                    [
                        dcc.Input(
                            id='snap-address',
                            placeholder='Snap to Address',
                            type='text',
                            style={'width': '100%'},
                        )
                    ],
                    className='four columns', style={'margin-top': '20'}
                ),

                # Address button
                html.Div(
                    [
                        html.Button(
                            "snap", id='address-button', style={'width': '100%'}, n_clicks=0,
                        )
                    ],
                    className='two columns', style={'margin-top': '20'}
                ),

                # Bus Search
                html.Div(
                    [
                        dcc.Input(
                            id='snap-bus',
                            placeholder='Snap to Bus',
                            type='text',
                            style={'width': '100%'}
                        )
                    ],
                    className='four columns', style={'margin-top': '20'}
                ),

                # Bus button
                html.Div(
                    [
                        html.Button(
                            "snap", id='address-button', style={'width': '100%'}
                        )
                    ],
                    className='two columns', style={'margin-top': '20'}
                ),
            ],
            className='row'
        ),

        # Second row - map + trip planner
        html.Div(
            [
                # Map
                html.Div(
                    [
                        dcc.Graph(id='main-map', figure=fig, animate=True, config={'displayModeBar': False})
                    ],
                    id='plot-area',
                    className='eight columns',
                    style={'margin-top': '20'}
                ),

                # Update interval
                dcc.Interval(
                    id='interval-component',
                    interval=1*refresh_time,
                    n_intervals=0
                    ),

                # Trip Planner
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id='departure-select',
                                    options=[{'label': i, 'value': i} for i in facilities['LOCATION_NAME']],
                                    placeholder='Search or Select Departure Location',
                                    value='Chester Hill Station'
                                ),
                            ], className='row',
                        ),

                        html.Div(
                            [
                                dcc.Dropdown(
                                    id='arrival-select',
                                    options=[{'label': i, 'value': i} for i in facilities['LOCATION_NAME']],
                                    placeholder='Search or Select Arrival Location',
                                    value='Redfern Station'
                                ),
                            ], className='row', style={'margin-top': '10'}
                        ),

                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id='departure-hours-select',
                                            options=[{'label': i, 'value': i} for i in range(13)],
                                            placeholder='Hours',
                                        ),
                                    ], className='six columns'
                                ),

                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id='departure-minute-select',
                                            options=[{'label': i, 'value': i} for i in range(61)],
                                            placeholder='Minutes',
                                        ),
                                    ], className='six columns'
                                )
                            ], className='row', style={'margin-top': '10'}
                        )
                    ],
                    className='four columns',
                    style={'margin-top': '20', 'background': colours['subs']}
                ),
            ],

            className='row'
        ),

        # Dropdown
        html.Div(
            [
                dcc.Dropdown(
                    id='station-select',
                    options=[{'label': i, 'value': i} for i in facilities['LOCATION_NAME']],
                    multi=True,
                    value=['Redfern Station', 'Bargo Station', 'Chester Hill Station'],
                    placeholder='Search or Select a NSW Station',
                )
            ],
            className='row', style={'margin-top': '10'}
        ),
        # Third row - Facilities + graph
        html.Div(
            [
                # Left side graph
                html.Div(
                    [
                        dcc.Graph(
                            id='facilities-graph',
                            figure={
                                'data': [
                                ],
                                'layout': {
                                    'title': 'Facilities Check',
                                    'titlefont': dict(size='14'),
                                    'plot_bgcolor': colours['plots'],
                                    'paper_bgcolor': colours['subs'],
                                    'font': {
                                        'color': "#EFEFEF"
                                    },
                                    'height': '500',
                                    'legend': {'orientation': 'h'},
                                    'margin': dict(
                                        l=30,
                                        r=30,
                                        b=30,
                                        t=50
                                    ),
                                }
                            }
                        , config={'displayModeBar': False}, animate=True)
                    ],
                    className='twelve columns',
                    style={'margin-top': '10'}
                ),
            ],
            className='row'
        ),

        # Refresh post
        html.Div(
            [
                html.Div("Refreshing every {} seconds".format(refresh_time/1000), id='countdown'),
            ],
            className='row'
        ),
    ],
        className='ten columns offset-by-one',
    ),
    className='twelve columns',
    style={
        'background': colours['main'],
    },

)


# Plotting area --> Map plot
@app.callback(Output('plot-area', 'children'), [Input('address-button', 'n_clicks')], [State('snap-address', 'value')])
def zoomed_address(clicks, address):
    if clicks is not None:
        new_latitude = get_pos(address)[0]
        new_longitude = get_pos(address)[1]
        fresh_data = get_live_data()
        new_data = [dict(
            type='scattermapbox',
            lon=fresh_data.longitudes,
            lat=fresh_data.latitudes,
            text="Bus Route: " + fresh_data.routes + ", \n \n" + "Occupancy: " + fresh_data.occupancy_text + ", \n \n" +
                 "Speed: " + fresh_data.speeds + "km/h",
            marker=dict(
                size=10,
                opacity=0.6,
                color=fresh_data.occupancies,
                colorscale=scl,
            )
        )]

        new_layout = dict(mapbox=dict(accesstoken=mapbox_access_token, style="dark",
                                      center=dict(lon=new_longitude, lat=new_latitude), zoom=13,))
        new_fig = dict(data=new_data, layout=new_layout)

        return dcc.Graph(id='main-map', figure=new_fig, animate=True, config={'displayModeBar': False})

    else:
        return dcc.Graph(id='main-map', figure=fig, animate=True, config={'displayModeBar': False})


# Map plot --> Updated markers
@app.callback(Output('main-map', 'figure'), [Input('interval-component', 'n_intervals')])
def plot_markers(interval):
    time.sleep(1)
    fresh_data = get_live_data()
    new_data = [dict(
        type='scattermapbox',
        lon=fresh_data.longitudes,
        lat=fresh_data.latitudes,
        text="Bus Route: " + fresh_data.routes + ", \n \n" + "Occupancy: " + fresh_data.occupancy_text + ", \n \n" +
             "Speed: " + fresh_data.speeds + "km/h",
        marker=dict(
            size=10,
            opacity=0.6,
            color=fresh_data.occupancies,
            colorscale=scl,
        )
    )]

    return dict(data=new_data)


# Select --> Facilities plot
@app.callback(Output('facilities-graph', 'figure'), [Input('station-select', 'value')])
def plot_markers(items):
    to_plot = []

    if type(items) == str:
        to_plot.append({'x': facilities.columns.values[3:], 'y': get_spot(items), 'type': 'line', 'name': items})
    else:
        for item in items:
            to_plot.append({'x': facilities.columns.values[3:], 'y': get_spot(item), 'type': 'line', 'name': item})

    return dict(data=to_plot, layout={
                                    'title': 'Facilities Check',
                                    'titlefont': dict(size='14'),
                                    'plot_bgcolor': colours['plots'],
                                    'paper_bgcolor': colours['subs'],
                                    'font': {
                                        'color': "#EFEFEF"
                                    },
                                    'height': '500',
                                    'legend': {'orientation': 'h'},
                                    'margin': dict(
                                        l=30,
                                        r=30,
                                        b=30,
                                        t=50
                                    ),
                                })

if __name__ == '__main__':
    app.run_server(debug=True)

