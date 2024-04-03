import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import product
from statistics import pstdev
from string import Template
from time import sleep

import requests


# gets instagram "locations" around a particular lat/lng using internal API
#   (requires session cookie for authentication)
def get_instagram_locations(lat, lng, cookie):
    timeout = 5.0
    lat_long = f"lat: {lat:.6f} | lng: {lng:.6f}"
    url = "https://www.instagram.com/location_search/"
    params = {"latitude": lat, "longitude": lng, "__a": 1}
    headers = {"Cookie": cookie}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection failed for {lat_long}: {e}")
        return []
    except requests.exceptions.Timeout:
        print(f"Connections timed out after {timeout} seconds")
        return []

    try:
        locations = response.json()
    except json.JSONDecodeError:
        print(f"Failed to get location data for {lat_long}: please check you have a valid cookie")
        return []

    if not isinstance(locations, dict):
        print(f"Got invalid response for {lat_long}")
        return []

    locations = locations.get("venues", [])
    return locations


def get_instagram_locations_by_query(query):
    locs = requests.get("https://www.instagram.com/web/search/topsearch/?context=place&query=" + query).json()

    return [v["place"]["location"] for v in locs["places"]]


# queries the instagram location API for several points around a central lat/lng
# in order to return additional results
def get_fuzzy_locations(lat, lng, cookie, sigma=2):
    locs = get_instagram_locations(lat, lng, cookie)
    print(locs)
    loc_ids = {v["external_id"] for v in locs if "external_id" in v}

    std_lat = pstdev([v["lat"] for v in locs if "lat" in v])
    std_lng = pstdev([v["lng"] for v in locs if "lng" in v])

    # filter to avoid calling with both lat and lng deltas equal zero (which would duplicate the call
    # to obtain the initial loc)
    deltas = (
        (lat + delta_lat * std_lat, lng + delta_lng * std_lng)
        for delta_lat, delta_lng in filter(lambda x: any(x), product(range(-sigma, sigma + 1), repeat=2))
    )

    # to change args order for convenient unpacking
    insta_loc_func = lambda ckie, lt, ln: get_instagram_locations(lt, ln, ckie)

    with ThreadPoolExecutor() as ex:
        results = ex.map(lambda x: insta_loc_func(cookie, *x), deltas)

    for new_locs in results:
        for loc in new_locs:
            if "external_id" in loc and loc["external_id"] not in loc_ids:
                locs.append(loc)
                loc_ids.add(loc["external_id"])

    return locs


# converts list of instagram locations into valid geojson
def make_geojson(locations):
    features = []

    for location in [location for location in locations if "lng" in location]:
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [location["lng"], location["lat"]]},
            "properties": location,
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def encode_date(date_str: str):
    """Convert date into Instagram "snowflake" ID"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print('Unable to parse date. Please use format "yyyy-mm-dd".', file=sys.stderr)
            sys.exit(1)
    date = date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    date_ts = int(date.timestamp()) * 1000  # milliseconds
    insta_epoch = date_ts - 1314220021300
    max_id_num = insta_epoch << 23

    return str(max_id_num)


def get_insta_cookies():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    import os.path
    """
    Attempts to run selenium, provide user with the login form and extract cookies from page to be used in program.
    Returns cookies formatted as name=value;name=value;...
     """
    options = webdriver.ChromeOptions()
    options.add_argument(r"--user-data-dir=" + os.path.expanduser("~/.instagram-location-search/chrome-data/"))
    options.add_argument(r"--profile-directory=instagram-location-profile")

    service = Service()
    driver = webdriver.Chrome(options=options, service=service)
    driver.get("https://www.instagram.com/")
    # Check that there is cookie with name sessionid (mean we logged in)
    cookies = driver.get_cookies()
    while not any([cookie.get("name") == "sessionid" for cookie in cookies]):
        sleep(1)
        cookies = driver.get_cookies()
    return "; ".join([f"{cookie['name']}={cookie['value'] }"for cookie in cookies])


html_template = """<html>
  <head>
    <title>Instagram location visualizations</title>

    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <link
      rel="stylesheet"
      href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
      integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A=="
      crossorigin=""
    />
    <script
      src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"
      integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA=="
      crossorigin=""
    ></script>

    <style>
      html,
      body {
        height: 100%;
        margin: 0;
      }
      #map {
        width: 100%;
        height: 600px;
      }
      img.selected-location {
        filter: hue-rotate(120deg);
        z-index: 999 !important;
      }
    </style>
  </head>
  <body>
    <div id="map"></div>

    <script>
      var map = L.map("map").setView([$lat, $lng], 14);

      var locs = $locs;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        id: "mapbox/light-v9",
      }).addTo(map);

      function onEachFeature(feature, layer) {
        layer.bindPopup(`<a href="https://www.instagram.com/explore/locations/` + feature.properties.external_id + `$date_var" target="_blank">` + feature.properties.name + `</a><br />` + feature.properties.address );
      }

      L.geoJSON(locs, {
        onEachFeature: onEachFeature
      }).addTo(map);

      var centerMarker = L.marker([$lat, $lng]).addTo(map);
      centerMarker._icon.classList.add('selected-location');
    </script>
  </body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Get a list of Instagram locations near a lat/lng")
    parser.add_argument("--cookie", action="store", dest="cookie")
    parser.add_argument("--json", action="store", dest="output")
    parser.add_argument("--geojson", action="store", dest="geojson")
    parser.add_argument("--map", action="store", dest="map")
    parser.add_argument("--csv", action="store", dest="csv")
    parser.add_argument("--lat", action="store", dest="lat")
    parser.add_argument("--lng", action="store", dest="lng")
    parser.add_argument("--date", action="store", dest="date")
    parser.add_argument("--ids", action="store", dest="dump_ids")

    args = parser.parse_args()

    cookie = args.cookie
    # If user run command without cookie we are trying to perform automated flow to acquire the cookie
    if not cookie:
        cookie = get_insta_cookies()

    date_var = ""
    if args.date is not None:
        date_var = "?max_id=" + encode_date(args.date)

    locations = get_fuzzy_locations(float(args.lat), float(args.lng), cookie)

    if args.output:
        json.dump(locations, open(args.output, "w"))

    if args.geojson:
        json.dump(make_geojson(locations), open(args.geojson, "w"))

    if args.map:
        s = Template(html_template)
        viz = s.substitute(lat=args.lat, lng=args.lng, locs=json.dumps(make_geojson(locations)), date_var=date_var)

        f = open(args.map, "w")
        f.write(viz)
        f.close()

    if args.csv:
        for i in locations:
            i["url"] = f"https://www.instagram.com/explore/locations/{i['external_id']}{date_var}"

        # leading empty string for 'id' column is for backward compatibility since that's the pandas behavior.
        fieldnames = ["", "name", "external_id", "external_id_source", "lat", "lng", "address", "minimum_age", "url"]

        with open(args.csv, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for idx, row in enumerate(locations):
                row[""] = idx
                writer.writerow(row)

    if args.dump_ids:
        ids = map(lambda loc: str(loc["external_id"]), locations)
        with open(args.dump_ids, "w") as f:
            f.write("\n".join(ids))
            

if __name__ == "__main__":
    main()
