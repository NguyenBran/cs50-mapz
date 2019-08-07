import os
import requests
import urllib.parse
import urllib.request
import json

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

## Creates a URL using the directions API on MapQuest and returns the
## json dictionary of the URL
# @param start is a beginning location for the URL of the directions
# @param end is the ending location for the URL of the directions
# @return json dictionary of the URL

def buildDirections(start : str, end : str) -> dict:
    queryList = [("key", "U5eDB4aCg6RdRvLOMeuzlF82C629Jrr7"), ("from", start), ("to", end)]
    url = "http://open.mapquestapi.com/directions/v2/route?" + urllib.parse.urlencode(queryList)

    return getResults(url)


## Takes in a URL, opens it up, then returns the json dictionary
## resulting from the URL
# @param url is the string url that was created and what is being opened
# @return json dictionary of the URL

def getResults (url : str) -> dict:
    response = None

    try:
        response = urllib.request.urlopen(url)
        results = json.load(response)

        return results

    finally:
        if response != None:
            response.close()


## Builds URLs using the locations provided, obtains the information from
## the distance MapQuest API, then totals all of the distance between
## the locations from beginning to the ending location
# @param locations is a list of locations to go to
# @return the float of the total distance between all of the locations

def totalDistance(locations : list) -> float:
    if len(locations) <= 1:
        return 0

    total = 0.0
    start = locations[0]

    for i in range(1, len(locations)):
        results = buildDirections(start, locations[i])
        total += (results['route']['distance'])
        start = locations[i]

    return total


## Builds URLs using the locations provided and obtains information
## from the distance MapQuest API, then totals the time between
## the locations from the beginning location to the ending location
# @param locations is a list of locations to go to
# @return the integer of the total time between all of the locations

def totalTime(locations : list) -> int:
    if len(locations) <= 1:
        return 0

    start = locations[0]
    total = 0

    for i in range(1, len(locations)):
        results = buildDirections(start, locations[i])
        total += (results['route']['legs'][0]['time'])
        start = locations[i]

    return total


## builds URLs based on the locations provided, then creates a text
## using the directions provided by the directions API from MapQuest
# @param list of locations which will be used to build the
# navigation from the first location to the last
# @return is the string of the navigation from the beginning location
# to the ending location, going to all of the locations in between

def directions(locations : list) -> list:
    if len(locations) <= 1:
        return 0

    start = locations[0]
    navigation = []

    for i in range(1, len(locations)):
        results = buildDirections(start, locations[i])

        for legs in results['route']['legs']:
            for nav in legs['maneuvers']:
                navigation.append((nav['narrative'], nav["distance"]))
        start = locations[i]

    return navigation


## Creates a URL using the Geocode API from MapQuest, then opens it and
## obtains the coordinates, longitude and latitude and returns that
# @param location is the location where we will be getting coordinates
# @return tuple where the longitude is first, then latitude is second

def getCoords(location : str) -> tuple:
    queryList = [("key", "U5eDB4aCg6RdRvLOMeuzlF82C629Jrr7"), ("location", location)]
    url = "http://www.mapquestapi.com/geocoding/v1/address?" + urllib.parse.urlencode(queryList)

    results = getResults(url)
    coords = (results["results"][0]["locations"][0]["latLng"])

    return (coords["lng"], coords["lat"])


## Creates a search URL using the MapQuest Place Search API
## first obtains the coordinates, then builds the URL,
## then obtains
# @param location is the address of where the beginning search will begin
# @param keyword is the service or places that are being looked for
# @param results the number of desired places to be returned
# @return json dictionary of the URL that was created

def buildSearch (locations : str, keyword : str, results : int) -> dict:
    longitude, latitude = getCoords(locations)

    queryList = [("key", "U5eDB4aCg6RdRvLOMeuzlF82C629Jrr7"), ("q", keyword),
                 ("location", str(longitude) + "," + str(latitude)),
                 ("sort", "distance")]

    if 0 < results <= 50:
        queryList.append(("pageSize", str(results)))
    elif results > 50:
        queryList.append(("pageSize", "50"))

    url = "http://www.mapquestapi.com/search/v4/place?" + urllib.parse.urlencode(queryList)

    return getResults(url)


## Takes in a location and keyword and results and looks up a certain number
## of places surrounding that location
# @param locations is the location or address where the search begins
# @param keyword the places that the user is looking for around the location
# @param results the number of results or places that the user is looking for
# @return a list of the places around the location matching the keyword
# there are only a set number of results as defined by the results parameter

def pointOfInterest(locations : str, keyword : str, results : int) -> list:
    searchDict = buildSearch(locations, keyword, results)
    listLocations = []

    for place in searchDict["results"]:
        listLocations.append(place["displayString"])

    return listLocations

def reverseGeo(coords):
    reverse = buildReverse(coords)["results"][0]["locations"][0]
    return reverse["street"] + "," + reverse["adminArea5"] + "," + reverse["adminArea3"]

def buildReverse(coords):
    queryList = [("key", "U5eDB4aCg6RdRvLOMeuzlF82C629Jrr7"), ("location", coords)]
    url = "http://www.mapquestapi.com/geocoding/v1/reverse?" + urllib.parse.urlencode(queryList)

    return getResults(url)

print(reverseGeo("37.611929599999996,-122.413056"))