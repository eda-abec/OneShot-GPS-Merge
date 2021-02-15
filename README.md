# OneShot report with Coordinates Merger

**os_gps_merge.py** is a Python script to match WiFi networks from reports of [OneShot](https://github.com/drygdryg/OneShot) (`stored.csv`) to their real-life coordinates.
For this, a wardriving DB is needed. Currently, a .csv file exported from [WiGLE app](https://wigle.net/tools) is supported.
Those two files are compared and their conjunction (based on MAC addresses) is then written to output file.

Matched coordinates are those with highest signal for given MAC.

You can then feed the result in CSV to [OneShot-GPS-Visualizer](https://github.com/eda-abec/OneShot-GPS-Visualizer), which displays it on map, or use arbitrary service to display KML.

Any suggestions and pull requests are welcome. :)

### Requirements
- Python3 (Python2 is not supported!)
- libraries:
   - argparse
   - csv
   - simplekml
- the input files :)

## Usage

Makefile is included, default target runs the script.\
Make expects specific filenames.

```
make

# same as
python3 os_gps_merge.py stored.csv wigle/WigleWifi_*.csv stored_gps.csv -p pins/

# prints running time of the script
make benchmark

# delete the results file and run again
make force


#### manual running

# also export to KML, use different file for networks with only PIN available
python3 os_gps_merge.py stored.csv wigle/WigleWifi_*.csv stored_gps.csv -k stored_gps.kml --kml-pins stored_pins_gps.kml

```

From help:
```
usage: os_gps_merge.py [-h] [-d DELIMITER] [-p PINS_FOLDER]
                       [--kml-pins-output KML_PINS_OUTPUT]
                       [--csv-pins-output CSV_PINS_OUTPUT] [-o CSV_OUTPUT] [-k KML_OUTPUT]
                       [-u UNMATCHED]
                       OneShot_report WiGLE_file [WiGLE_file ...]

OneShot GPS Merger (c) 2020 eda-abec
based on OneShotPin 0.0.2 (c) 2017 rofl0r, modded by drygdryg

positional arguments:
  OneShot_report        input file generated by OneShot, usually named stored.csv
  WiGLE_file            input file(s) with APs and their GPS coordinates, generated by
                        Wigle, usually named WigleWifi_{date}.csv. Note: must be latin-1
                        encoded, which is default

optional arguments:
  -h, --help            show this help message and exit
  -d DELIMITER, --delimiter DELIMITER
                        delimiter for output CSV file, like semicolon (default), comma, or
                        anything else
  -p PINS_FOLDER, --pins_folder PINS_FOLDER
                        a folder with saved PINs from Pixiewps, by default
                        ~/.OneShot/pixiewps
  --kml-pins-output KML_PINS_OUTPUT
                        save PIN-only networks to this KML file. If not specified, written
                        to default KML file
  --csv-pins-output CSV_PINS_OUTPUT
                        output CSV file with for PIN-only networks. If not specified,
                        written to default CSV file

output:
  Generates file with merged OneShot networks and their GPS coordinates

  -o CSV_OUTPUT, --csv-output CSV_OUTPUT
                        save as CSV
  -k KML_OUTPUT, --kml-output KML_OUTPUT
                        save as KML
  -u UNMATCHED, --unmatched UNMATCHED
                        save only OneShot entries not found in WiGLE, as CSV.
                        Complementary to -o

Example: os_gps_merge.py stored.csv WiGLE.csv -o stored_gps.csv

```

## File Formats

### CSV
#### OneShot
A standard, as-is from OneShot
```
encoding="utf-8"
delimiter=';'
```

#### WiGLE
[specification](https://api.wigle.net/csvFormat.html)

Does not have UTF-8 encoding.
```
encoding="latin-1"
delimiter=','
```

#### Output
Columns are same as in OneShot report, with `CurrentLatitude`, `CurrentLongitude` and `RSSI` added to end.
```
encoding="utf-8"
delimiter= default is ';', could be changed by -d
```

### KML
Use the `-k` option to save output to KML file. Uses standard settings:
```
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
...
```

## TODOs

- better name
- integrate DB from https://github.com/drygdryg/wigle_companion
- choose columns and their order in output .csv
- matching by time (not a priority, probbably will not be implemented)
- fuzzy checking (alert about unmatched network within -+hour from matched network)
- small TODOs
    - parameters
    - add switch for WiGLE encoding
    - quiet mode
    - output to stdout?
    - handle missing/incorrect input files

## Acknowledgements

Author: [eda-abec](https://github.com/eda-abec)\
Date: 12/2020\
Based on and Thanks to:
- [OneShot](https://github.com/drygdryg/OneShot)
- [WiGLE.net](https://github.com/wiglenet)

