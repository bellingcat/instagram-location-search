# Instagram Location Search

[![PyPI version](https://badge.fury.io/py/instagram-location-search.svg)](https://badge.fury.io/py/instagram-location-search)
## Installation
This Python application can be installed from [PyPI](https://pypi.org/project/instagram-location-search/) using pip:
`pip install instagram-location-search`

or the latest from the repo:
`pip install git+https://github.com/bellingcat/instagram-location-search`

## Example usage

The following command will search for Instagram locations nearby the coordinates 32.22 N, 110.97 W (downtown Tucson, Arizona.) The list of locations is saved as a CSV file at "locs.csv".

```instagram-location-search --cookie "<instagram-cookies>" --lat 32.22 --lng -110.97 --csv locs.csv```

Note that this requires Instagram cookies in order to work! See below for how to obtain one from your account.

### Other output formats

Using the `--json <output-location>` command line argument, the list can be saved as a JSON file, almost identical to the raw API response.

Using the `--geojson <output-location>` command line argument, the list can be saved as a GeoJSON file for other geospatial applications.

Using the `--ids <output-location>` command line argument, all the found location IDs are output, suitable to pass into another tool, like [instagram-scraper](https://github.com/arc298/instagram-scraper).

Using the `--map <output-location>` command line argument, a simple Leaflet map is made to visualize the locations of the returned points.

![Example of map visualization](docs/map-example.png)

Multiple types of output can be generated. For example, the following command will search for Instagram locations, save the JSON list, a CSV file, and a map for viewing the locations visually.

```instagram-location-search --cookie "<instagram-cookie>" --lat 32.22 --lng -110.97 --json locs.json --csv locs.csv --map map.html```

## Sample Usage with `instagram-scraper`
The ID list generated with the `--ids` flag can be passed into `instagram-scraper` to pull down image metadata.

### :rotating_light: Undocumented API :rotating_light:
`instagram-scraper` relies on an undocumented API for the mobile apps. YMMV.

First, get the proximal location IDs of your target location:
```sh
instagram-location-search --cookies "<instagram-cookie>" --lat <lat> --lng <lng> --ids location_ids.txt
```

Be sure to install `instagram-scraper`:
```
pip install instagram-scraper
```

Location scraping requires an authenticated request. Save your creds in a local file:
```sh
echo "-u=<your username>" >> creds.txt
echo "-p=<your password>" >> creds.txt
```

Now use `instagram-scraper` to pull down all the photos at those locations:
```sh
instagram-scraper @creds.txt --filename @location_ids.txt --location --include-location --destination <output dir>
```

## Getting Instagram cookies

### Improved Tool Usage Process

The updated process allows you to obtain cookies through a pop-up browser window. To use this new flow, simply omit the `--cookie` parameter when running the command.

__Important: An Instagram session ID should be treated like a password, as it provides full access to your Instagram account. Using this session ID in multiple places or on multiple computers may cause Instagram to invalidate all session IDs. Using this session ID for any purpose other than the official Instagram website or application may violate the Instagram Terms of Service and could lead to account suspension.__

Follow these steps to use the improved tool usage process:

1. Run the command without the `--cookie` parameter.
2. In the opened Google Chrome instance, create a new profile.
   ![Creating a new profile](docs/selenium1.png)
3. Click "Continue without email".
   ![Continue without email](docs/selenium2.png)
4. Enter a name for the profile you'd like to link to instagram account, and click "Done".
   ![Creating an account](docs/selenium3.png)
5. Select "Only allow essential cookies".
   ![Only allow essential cookies](docs/selenium4.png)
6. Log in to your Instagram account. The browser will close automatically shortly afterward.
   ![Log in to Instagram](docs/selenium5.png)

Once you've completed the initial setup, you can simply click on the created profile in subsequent runs to use the associated Instagram account.


### Old flow
This now requires the entire cookie string, in the format of an HTTP request header. Details TK.

__Important: an Instagram session ID should be treated like a password — it provides full access to the Instagram account. Using this session ID in multiple places or on multiple computers may trigger Instagram to invalidate all session IDs. Using this session ID for any purpose other than the official Instagram website or application may be a violation of the Instagram Terms of Service and could lead to account suspension.__

1. In Google Chrome, log-in to Instagram.
2. Right click on the page and press "Inspect" to bring up the Chrome Developer Tools.
3. Click the "Application" tab in the Developer Tools Box.
4. Under "Cookies" select "https://www.instagram.com."
![Finding the Instagram cookie](docs/cookies.jpg)

5. Right click on any item and click "Show Requests With This Cookie".
6. Click on any request. In the "Headers" tab, scroll down to "Request Headers".

![Finding the full cookie string](docs/cookies2.png)

7. Copy all text after "cookie: ". This is your cookie string. Replace `<instagram-cookies>` with this value when running `instagram-location-search`.
