import requests
import numpy as np
import pandas as pd
import argparse
import json
from string import Template
from datetime import datetime, timezone
import sys

# gets instagram "locations" around a particular lat/lng using internal API
#   (requires session cookie for authentication)
def get_instagram_locations(lat, lng, cookie):
    locs = requests.get("https://www.instagram.com/location_search/?latitude=" + str(lat) + "&longitude=" + str(lng) + "&__a=1", headers={
            'Cookie': cookie
        }).json()
    return locs['venues']


def get_instagram_locations_by_query(query):
    locs = requests.get("https://www.instagram.com/web/search/topsearch/?context=place&query=" + query).json()
    
    return [v['place']['location'] for v in locs['places']]

# queries the instagram location API for several points around a central lat/lng
# in order to return additional results
def get_fuzzy_locations(lat, lng, cookie, sigma=2):
    locs = get_instagram_locations(lat, lng, cookie)
    
    std_lat = np.std([v['lat'] for v in locs if 'lat' in v])
    std_lng = np.std([v['lng'] for v in locs if 'lng' in v])
    
    for delta_lat in range(-sigma, sigma+1):
        for delta_lng in range(-sigma, sigma+1):
            new_locs = get_instagram_locations(lat + delta_lat * std_lat, lng + delta_lng * std_lng, cookie)
            loc_ids = [v['external_id'] for v in locs]
            
            for loc in new_locs:
                if loc['external_id'] not in loc_ids:
                    locs.append(loc)
                    
    return locs

# converts list of instagram locations into valid geojson
def make_geojson(locs):
    features = []

    for l in [l for l in locs if 'lng' in l]:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [l["lng"], l["lat"]]
                },
            "properties": l}
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}

def encode_date(date_str: str):
    '''Convert date into Instagram "snowflake" ID'''
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print('Unable to parse date. Please use format "yyyy-mm-dd".', file=sys.stderr)
            sys.exit(1)
    date = date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    date_ts = int(date.timestamp()) * 1000 # milliseconds
    insta_epoch = date_ts - 1314220021300
    max_id_num = insta_epoch << 23

    return str(max_id_num)

html_template = '''<html>
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
</html>'''

def main():
    parser = argparse.ArgumentParser(description="Get a list of Instagram locations near a lat/lng")
    parser.add_argument("--session", action="store", dest="session")
    parser.add_argument("--json", action="store", dest="output")
    parser.add_argument("--geojson", action="store", dest="geojson")
    parser.add_argument("--map", action="store", dest="map")
    parser.add_argument("--csv", action="store", dest="csv")
    parser.add_argument("--lat", action="store", dest="lat")
    parser.add_argument("--lng", action="store", dest="lng")
    parser.add_argument("--date", action="store", dest="date")

    args = parser.parse_args()

    cookie = 'sessionid=' + args.session

    date_var = ''
    if args.date is not None:
        date_var = '?max_id=' + encode_date(args.date)

    locations = get_fuzzy_locations(float(args.lat), float(args.lng), cookie)

    if (args.output):
        json.dump(locations, open(args.output, 'w'))

    if (args.geojson):
        json.dump(make_geojson(locations), open(args.geojson, 'w'))

    if (args.map):
        s = Template(html_template)
        viz = s.substitute(lat=args.lat, lng=args.lng, locs=json.dumps(make_geojson(locations)), date_var=date_var)

        f = open(args.map, 'w')
        f.write(viz)
        f.close()

    if (args.csv):
        df = pd.DataFrame(locations)
        df['url'] = df['external_id'].apply(lambda v: 'https://www.instagram.com/explore/locations/' + str(v) + date_var)
        df.to_csv(args.csv)

if __name__ == "__main__":
    main()

