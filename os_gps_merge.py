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


def strongest_signal(AP):
    return int(AP["RSSI"])

# added error handling, original source: https://stackoverflow.com/a/6520795
def count_lines(filename):
    try:
        with open(str(filename)) as f:
            for i, l in enumerate(f, 1):
                pass
            return i - 1        # minus header row
    except FileNotFoundError:
        return 0



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
    default = "stored.csv",
    help = "Input file generated by OneShot, usually named stored.csv"
)

parser.add_argument(
 #   "-w", "--WiGLE-file",  # will be optional when time matching is implemented
    "WiGLE_file",
    nargs = "+",
    default = "WiGLE.csv",
    help = "Input file(s) with APs and their GPS coordinates, generated by Wigle, usually named WigleWifi_{date}.csv. Note: must be latin-1 encoded, which is default"
)


parser.add_argument(
    "-g", "--GPS_file",
    default = "GPS.csv",
    help = "Input file with GPS coordinates and timestamps, more info TBA, not yet implemented"
)

parser.add_argument(
    "-d", "--delimiter",
    default = ";",
    help = "Delimiter for output file, like semicolon (default), comma, or anything else"
)

parser.add_argument(
    "-p", "--pins_folder",
    help = "A folder with saved PINs from Pixiewps"
)

parser.add_argument(
    "-k", "--kml-output",
    help = "Specifies filename for KML output"
)

parser.add_argument(
    "--kml-pins",
    help = "Save PIN-only networks to separate KML file. If not specified, written to default KML file"
)

parser.add_argument(
    "-u", "--unmatched",
    help = "Output CSV file with OneShot entries not found in WiGLE"
)

parser.add_argument(
    "--pins-output",
    help = "Output CSV file with for PIN-only networks. If not specified, written to default output file"
)

parser.add_argument(
    "output",
    default = "stored_gps.csv",
    help = "Output CSV file with merged APs and GPS coordinates"
)

args = parser.parse_args()






nets = []


prev_matched = count_lines(args.output)
if prev_matched > 0:
    print("[  info ] Previous run matched {} networks".format(prev_matched))


reader =  csv.DictReader(open(args.OneShot_report, encoding="utf-8"), delimiter=';')

for row in reader:
    # it is faster to convert OneShot reports to lower than vice versa, since there are usually less entries
    row["BSSID"] = row["BSSID"].lower()
    nets.append(row)

orig_header =  list(nets[0].keys())
header = orig_header + [latname] + [longname] + [signal]      # tmp

print("[OneShot] Loaded {} networks".format(len(nets)))

unique_nets = {net["BSSID"]:net for net in nets}.values()
if len(unique_nets) < len(nets):
    print("[OneShot] Found {} duplicated networks!".format(len(nets) - len(unique_nets)))
    duplicates = [AP for AP in nets if AP not in unique_nets]
    # to print duplicates, uncomment the following line
   # print([AP["ESSID"] for AP in duplicates])
    nets = unique_nets

PIN_nets_folder = args.pins_folder
PIN_nets = []
if (PIN_nets_folder != None):
    for PIN_file in os.listdir(PIN_nets_folder):
        row = {}
        reader = open(PIN_nets_folder + "/" + PIN_file)     # encoding should not matter for digits only
        row["BSSID"] = str(PIN_file).replace(".run", "").lower()
        # add colons. https://stackoverflow.com/a/61669445
        row["BSSID"] = ':'.join(row["BSSID"][i:i+2] for i in range(0,12,2))
        row["WPS PIN"] = reader.readline().replace("\n", "")
     #   row["Date"] = ctime(os.path.getmime(PIN_file))     # TODO
        PIN_nets.append(row)
    print("[OneShot] Loaded {} PIN-only networks".format(len(PIN_nets)))
    
    unique_PIN_nets = [PIN_row["BSSID"] for OS_row in nets for PIN_row in PIN_nets if OS_row["BSSID"] == PIN_row["BSSID"] and OS_row["WPS PIN"] == PIN_row["WPS PIN"]]
    if len(unique_PIN_nets) > 0:
        print('[OneShot] Found {} networks in both "{}" and "{}"!'.format(len(unique_PIN_nets), args.OneShot_report, PIN_nets_folder))
        # for now, uncomment this line to show them
       # print(unique_PIN_nets)
    
    unique_colliding_PIN_nets = [PIN_row["BSSID"] for OS_row in nets for PIN_row in PIN_nets if OS_row["BSSID"] == PIN_row["BSSID"] and OS_row["WPS PIN"] != PIN_row["WPS PIN"]]
    if len(unique_colliding_PIN_nets) > 0:
        print('[OneShot] Found {} networks in both "{}" and "{}" with different PIN!'.format(len(unique_colliding_PIN_nets), args.OneShot_report, PIN_nets_folder))
        # for now, uncomment this line to show them
       # print(unique_colliding_PIN_nets)

locations = []
for file_path in args.WiGLE_file:
    WiGLE_file = open(file_path, encoding="latin-1")
    next(WiGLE_file)    # because the first line is not csv header yet
    reader = csv.DictReader(WiGLE_file, delimiter=',')

    for row in reader:
        # there is no use in filtering out BT and GSM devices. They will be removed along with non-WPS WiFis
        try:
            if "[WPS]" in row["AuthMode"]:
                locations.append(row)
        except:
            print('[ WiGLE ] Could not parse "{}"!'.format(row))

print("[ Wigle ] Loaded {} WPS networks".format(len(locations)))


# this is an optimisation. Will be replaced to make an average of all occurrences, hopefully
# it filters all non-unique networks and leaves only one with strongest signal, so that the scripts works with less data and runs much faster
locations = {i["MAC"]:i for i in sorted(locations, key=strongest_signal)}.values()
locations_len = len(locations)
print("[ Wigle ] Shrunk to {} unique MACs".format(locations_len))


# the actual matching
matchedMACs = [dict(OS_row, **{latname: W_row[latname]}, **{longname: W_row[longname]}, **{signal: W_row[signal]})
               for OS_row in nets for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]

matchedMACsPIN = [dict(OS_row, **{latname: W_row[latname]}, **{longname: W_row[longname]}, **{signal: W_row[signal]}, **{"ESSID": W_row["SSID"]})
               for OS_row in PIN_nets for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]


if (args.unmatched != None):
    # this is ugly. I know. But somehow, it doesn't slow down the script much. So whatever.
    pureMatchedMACs = [OS_row for OS_row in nets for W_row in locations if OS_row["BSSID"] == W_row["MAC"]]
    unmatchedMACs = [OS_row for OS_row in nets if OS_row not in pureMatchedMACs]

    with open(args.unmatched, 'w', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, orig_header, delimiter=args.delimiter)
        writer.writeheader()
        writer.writerows(unmatchedMACs)


print("[ result] Matched {} (~{} %) networks with their coordinates".format(len(matchedMACs), round(100 * len(matchedMACs) / len(nets))))

if (PIN_nets_folder != None):
    print("[ result] Matched {} (~{} %) PIN-only networks with their coordinates".format(len(matchedMACsPIN), round(100 * len(matchedMACsPIN) / len(PIN_nets))))

# convert back to uppercase
for net in matchedMACs:
    net["BSSID"] = net["BSSID"].upper()

for net in matchedMACsPIN:
    net["BSSID"] = net["BSSID"].upper()


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


def matchedMACs_to_kml(matchedMACs, doc, style):
    for net in matchedMACs:
            pnt = kml.newpoint(name=net["ESSID"], coords=[(net[longname], net[latname])])
            pnt.timestamp.when = net.get("Date")
            pnt.description = "BSSID: {}<br/>Signal: {}".format(net["BSSID"], net[signal])
            pnt.style = style

if args.kml_output != None:
    stylePSK = simplekml.Style()
    #TODO give then colors and so
    
    stylePIN = simplekml.Style()

    if args.kml_pins != None:
        kml = simplekml.Kml()
        doc = kml.newdocument(name="OneShot PIN-only")
        
        matchedMACs_to_kml(matchedMACsPIN, doc, stylePIN)
        
        kml.save(args.kml_pins)
        
        
        kml = simplekml.Kml()
        doc = kml.newdocument(name="OneShot networks")
        
        matchedMACs_to_kml(matchedMACs, doc, stylePSK)
        
        kml.save(args.kml_output)
    
    else:
        kml = simplekml.Kml()
        doc = kml.newdocument(name="OneShot networks")
        
        matchedMACs_to_kml(matchedMACs, doc, stylePSK)
        matchedMACs_to_kml(matchedMACsPIN, doc, stylePIN)
        
        kml.save(args.kml_output)

