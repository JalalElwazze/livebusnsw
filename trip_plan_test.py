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

api_key = 'OKrlDQxvcM5lb8vguvZK58pZmgtYqFGb1dJ3'
header = {'Authorization': 'apikey ' + api_key}


# Constants
def get_id(station):
    station = station.replace(" ", "%20")
    url = "https://api.transport.nsw.gov.au/v1/tp/stop_finder?outputFormat=rapidJSON&type_sf=stop&name_sf= " + \
        station + "&coordOutputFormat=EPSG%3A4326&TfNSWSF=true&version=10.2.1.42"
    stop = requests.get(url, headers=header).json()['locations'][0]['id']

    return str(stop)


def make_trips(depart, arrive):
    print(depart)
    print(arrive)
    date = '20180305'
    time = '0600'
    url = "https://api.transport.nsw.gov.au/v1/tp/trip?outputFormat=rapidJSON&coordOutputFormat=EPSG%3A4326&" + \
          "depArrMacro=arr&itdDate=" + date + "&itdTime=" + time + "&type_origin=any&name_origin=" + get_id(depart) + \
          "&type_destination=any&name_destination=" + get_id(arrive) + \
          "&calcNumberOfTrips=5&TfNSWTR=true&version=10.2.1.42"
    trip = requests.get(url, headers=header).json()['journeys']
    for set in trip:
        print(set)
    # times = []
    # for t in trip:
    #     times.append(t['legs'][0]['duration']/60)

    return trip

print(make_trips(get_id("Chester Hill Station"), get_id("Redfern Station")))
