#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import re
import os
import signal as sig
import simplekml


latname = "CurrentLatitude"
longname = "CurrentLongitude"
signal = "RSSI"

def strongest_signal (AP):
    return int(AP["RSSI"])

def signal_handler(signal, frame):
        print ("Interrupted, exitting...")
        exit(0)
sig.signal(sig.SIGINT, signal_handler)

parser = argparse.ArgumentParser (
    description = "OneShot GPS Merger (c) 2020 eda-abec\n" +
        "based on OneShotPin 0.0.2 (c) 2017 rofl0r, modded by drygdryg",
    epilog = "Example: %(prog)s stored.csv Wigle.csv stored_gps.csv"
)

parser.add_argument(
    "OneShot_report",
    type = str,
    default = "stored.csv",
    help = "Input file generated by OneShot, usually named stored.csv"
)

parser.add_argument(
 #   "-w", "--WiGLE-file",  # will be optional when time matching is implemented
    "WiGLE_file",
    type = str,
    nargs = "+",
    default = "WiGLE.csv",
    help = "Input file(s) with APs and their GPS coordinates, generated by Wigle, usually named WigleWifi_{date}.csv. Note: must be latin-1 encoded, which is default"
)


parser.add_argument(
    "-g", "--GPS_file",
    type = str,
    default = "GPS.csv",
    help = "Input file with GPS coordinates and timestamps, more info TBA, not yet implemented"
)

parser.add_argument(
    "-d", "--delimiter",
    type = str,
    default = ";",
    help = "Delimiter for output file, like semicolon (default), comma, or anything else"
)

parser.add_argument(
    "-p", "--pins_folder",
    type = str,
    default = None,
    help = "A folder with saved PINs from Pixiewps"
)

parser.add_argument(
    "-k", "--kml-output",
    type = str,
    default = None,
    help = "Specifies filename for KML output"
)

parser.add_argument(
    "--kml-pins",
    type = str,
    default = None,
    help = "Save PIN-only networks to separate KML file. If not specified, written to default KML file"
)

parser.add_argument(
    "-u", "--unmatched",
    type = str,
    default = None,
    help = "Output CSV file with OneShot entries not found in WiGLE"
)

parser.add_argument(
    "--pins-output",
    type = str,
    default = None,
    help = "Output CSV file with for PIN-only networks. If not specified, written to default output file"
)

parser.add_argument(
    "output",
    type = str,
    default = "stored_gps.csv",
    help = "Output CSV file with merged APs and GPS coordinates"
)

args = parser.parse_args()






APs = []

reader =  csv.DictReader(open(args.OneShot_report, encoding="utf-8"), delimiter=';')

for row in reader:
    # it is faster to convert OneShot reports to lower than vice versa, since there are usually less entries
    row["BSSID"] = row["BSSID"].lower()
    APs.append(row)

orig_header =  list(APs[0].keys())
header = orig_header + [latname] + [longname] + [signal]      # tmp

print("[OneShot] Loaded {} networks".format(len(APs)))

unique_APs = {i["BSSID"]:i for i in APs}.values()
if len(unique_APs) < len(APs):
    print("[OneShot] Found {} duplicated networks!".format(len(APs) - len(unique_APs)))
    duplicates = [AP for AP in APs if AP not in unique_APs]
    # to print duplicates, uncomment the following line
   # print([AP["ESSID"] for AP in duplicates])
    APs = unique_APs

PIN_APs_folder = args.pins_folder
PIN_APs = []
if (PIN_APs_folder != None):
    for PIN_file in os.listdir(PIN_APs_folder):
        row = {}
        reader = open(PIN_APs_folder + "/" + PIN_file)     # encoding should not matter for digits only
        row["BSSID"] = str(PIN_file).replace(".run", "").lower()
        # add colons. https://stackoverflow.com/a/61669445
        row["BSSID"] = ':'.join(row["BSSID"][i:i+2] for i in range(0,12,2))
        row["WPS PIN"] = reader.readline().replace("\n", "")
     #   row["Date"] = ctime(os.path.getmime(PIN_file))     # TODO
        PIN_APs.append(row)
    print("[OneShot] Loaded {} PIN-only networks".format(len(PIN_APs)))
    
    unique_PIN_APs = [PIN_row["BSSID"] for OS_row in APs for PIN_row in PIN_APs if OS_row["BSSID"] == PIN_row["BSSID"] and OS_row["WPS PIN"] == PIN_row["WPS PIN"]]
    if len(unique_PIN_APs) > 0:
        print('[OneShot] Found {} networks in both "{}" and "{}"!'.format(len(unique_PIN_APs), args.OneShot_report, PIN_APs_folder))
        # for now, uncomment this line to show them
       # print(unique_PIN_APs)
    
    unique_colliding_PIN_APs = [PIN_row["BSSID"] for OS_row in APs for PIN_row in PIN_APs if OS_row["BSSID"] == PIN_row["BSSID"] and OS_row["WPS PIN"] != PIN_row["WPS PIN"]]
    if len(unique_colliding_PIN_APs) > 0:
        print('[OneShot] Found {} networks in both "{}" and "{}" with different PIN!'.format(len(unique_colliding_PIN_APs), args.OneShot_report, PIN_APs_folder))
        # for now, uncomment this line to show them
       # print(unique_colliding_PIN_APs)

locations = []
for file_path in args.WiGLE_file:
    WiGLE_file = open(file_path, encoding="latin-1")
    next(WiGLE_file)    # because the first line is not csv header yet
    reader = csv.DictReader(WiGLE_file, delimiter=',')

    for row in reader:
        locations.append(row)

print("[ Wigle ] Loaded {} networks".format(len(locations)))


# this is an optimisation. Will be replaced to make an average of all occurrences, hopefully
# it filters all non-unique networks and leaves only one with strongest signal, so that the scripts works with less data and runs much faster
locations = {i["MAC"]:i for i in sorted(locations, key=strongest_signal)}.values()
locations_len = len(locations)
print("[ Wigle ] Shrunk to {} unique MACs".format(locations_len))

# there is no use in filtering out BT and GSM devices. They will be removed along with non-WPS WiFis

# another optimisation. Depending on input, it can decrease execution time by half
locations = list(filter(lambda line: "WPS" in line["AuthMode"], locations))
print("[ Wigle ] {} (~{} %) of which with WPS".format(len(locations), round(100 * len(locations) / locations_len)))



# the actual matching
matchedMACs = [dict(OS_row, **{latname: W_row[latname]}, **{longname: W_row[longname]}, **{signal: W_row[signal]})
               for OS_row in APs for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]

matchedMACsPIN = [dict(OS_row, **{latname: W_row[latname]}, **{longname: W_row[longname]}, **{signal: W_row[signal]}, **{"ESSID": W_row["SSID"]})
               for OS_row in PIN_APs for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]


if (args.unmatched != None):
    # this is ugly. I know. But somehow, it doesn't slow down the script much. So whatever.
    pureMatchedMACs = [OS_row for OS_row in APs for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]
    unmatchedMACs = [OS_row for OS_row in APs if OS_row not in pureMatchedMACs]

    with open(args.unmatched, 'w', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, orig_header, delimiter=args.delimiter)
        writer.writeheader()
        writer.writerows(unmatchedMACs)


print("[ result] Matched {} (~{} %) networks with their coordinates".format(len(matchedMACs), round(100 * len(matchedMACs) / len(APs))))

if (PIN_APs_folder != None):
    print("[ result] Matched {} (~{} %) PIN-only networks with their coordinates".format(len(matchedMACsPIN), round(100 * len(matchedMACsPIN) / len(PIN_APs))))

# convert back to uppercase
for row in matchedMACs:
    row["BSSID"] = row["BSSID"].upper()

for row in matchedMACsPIN:
    row["BSSID"] = row["BSSID"].upper()


with open(args.output, 'w', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, header, delimiter=args.delimiter)
    writer.writeheader()
    writer.writerows(matchedMACs)
    
    if args.pins_output != None:
        with open(args.pins_output, 'w', encoding="utf-8") as pins_csv:
            writer = csv.DictWriter(pins_csv, header, delimiter=args.delimiter)
            writer.writeheader()
            writer.writerows(matchedMACsPIN)
    else:
        writer.writerows(matchedMACsPIN)

if args.kml_output != None:
    stylePSK = simplekml.Style()
    #TODO give then colors and so
    
    stylePIN = simplekml.Style()
    
    kml = simplekml.Kml()
    
    for row in matchedMACsPIN:
        pnt = kml.newpoint(name=row["ESSID"], coords=[(row[longname],row[latname])])
        pnt.description = "BSSID: " + row["BSSID"] + "<br/>" + "Signal: " + row[signal]
        pnt.style = stylePIN

    if args.kml_pins != None:
        kml.save(args.kml_pins)
        kml = simplekml.Kml()

    
    for row in matchedMACs:
        pnt = kml.newpoint(name=row["ESSID"], coords=[(row[longname],row[latname])])
        pnt.timestamp.when = row["Date"]
        pnt.description = "BSSID: " + row["BSSID"] + "<br/>" + "Signal: " + row[signal]
        pnt.style = stylePSK
    
    kml.save(args.kml_output)
