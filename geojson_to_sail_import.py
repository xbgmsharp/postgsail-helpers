#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ------------------------------------------------------------------------
# postgsail-helpers tools: saillogger exporter
#
# Copyright 2024 Monty Taylor <monty.taylor@gmail.com>
# License:  GNU General Public License version 3 or later; see LICENSE.txt
# Website:  https://github.com/xbgmsharp/postgsail-helpers
# ------------------------------------------------------------------------
#
# Requires geographiclib and geopy libraries from PyPI.
# pip install geopy geographiclib

import argparse
import datetime
import time
import operator
import os
import sys

try:
    import geographiclib.geodesic
    import geopy.distance
except ImportError:
    sys.exit(
        "Please use your favorite method to install the following module geographiclib and geopy to use this script"
    )
import json
import csv

data = []


def getSpeedOverGround(old_coords, old_time, new_coords, new_time):
    # We have coordinates and time, we can calculate speed
    if not old_coords:
        return 0
    interval = (
        (
            datetime.datetime.fromisoformat(new_time)
            - datetime.datetime.fromisoformat(old_time)
        ).total_seconds()
        / 60
        / 60
    )
    return geopy.distance.geodesic(old_coords, new_coords).nm / interval


def getBearing(old_coords, new_lat, new_long):
    # We have coordinates, we can calculate bearing
    if not old_coords:
        return 0
    return geographiclib.geodesic.Geodesic.WGS84.Inverse(
        old_coords[0],
        old_coords[1],
        new_lat,
        new_long,
    )["azi1"]


def write_csv(results, filename):
    print("CSV output file: {0}".format(filename))
    # Write result CSV
    with open(filename, "w", encoding="utf-8", newline="") as fp:
        mycsv = csv.DictWriter(
            fp, fieldnames=list(results[0].keys()), quoting=csv.QUOTE_ALL
        )
        mycsv.writeheader()
        for row in results:
            mycsv.writerow(row)
    fp.close()


def process_geojson_file(data, infile):
    with open(infile, "r") as INFILE:
        json_data = json.load(INFILE)
    old_coords = None
    old_time = 0
    for feature in json_data["features"]:
        for idx, coordtime in enumerate(feature["properties"]["coordTimes"]):
            longitude, latitude = feature["geometry"]["coordinates"][idx][0:2]
            entry = {
                "time": coordtime,
                "client_id": None,
                "vessel_id": "1234567890",
                "latitude": latitude,
                "longitude": longitude,
                "courseoverground": getBearing(old_coords, latitude, longitude),
                "speedoverground": getSpeedOverGround(
                    old_coords, old_time, (latitude, longitude), coordtime
                ),
                "anglespeedapparent": "",
                "windspeedapparent": "",
                "metrics": "",
            }
            if idx == 0 or idx == (len(feature["properties"]["coordTimes"]) - 1):
                entry["status"] = "moored"
            else:
                entry["status"] = "sailing"

            data.append(entry)
            old_time = coordtime
            old_coords = (latitude, longitude)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--outfile",
        help="Output file to write. Defaults to sailog_metrics.csv",
        default="sailog_metrics.csv",
    )
    parser.add_argument("args", nargs="+")
    return parser.parse_args()


def main():
    args = parse_arguments()
    file_list = args.args
    data = []
    for filename in file_list:
        process_geojson_file(data, filename)

    write_csv(sorted(data, key=operator.itemgetter("time")), args.outfile)


if __name__ == "__main__":
    main()
