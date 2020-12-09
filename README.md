# Instagram Location Search

## Prerequisites

This Python application requires `requests` and `numpy` to be properly installed.

## Example usage

The following command will search for Instagram locations nearby the coordinates 32.22 N, 110.97 W (downtown Tucson, Arizona.) The list of locations is saved as a JSON file at "locs.json".

```python3 instagram-locations.py --session "<session-id-token>" --lat 32.22 --lng -110.97 --json locs.json```

Note that this requires an Instagram session ID in order to work! See below for how to obtain one from your account.

### Other output formats

Using the `--geojson <output-location>` command line argument, the list can be saved as a GeoJSON file for other geospatial applications.

Using the `--map <output-location>` command line argument, a simple Leaflet map is made to visualize the locations of the returned points.

![docs/map-example.png]

Multiple types of output can be generated. For example, the following command will search for Instagram locations, save the JSON list, a GeoJSON file, and a map for viewing the locations visually.

```python3 instagram-locations.py --session "3888090946%3AhdKd2fA8d72dqD%3A16" --lat 32.22 --lng -110.97 --json locs.json --geojson locs.geojson --map map.html```

## Getting an Instagram session ID