#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#------------------------------------------------------------------------
# postgsail-helpers tools: saillogger exporter
#
# Copyright 2016-2023 xbgmsharp <xbgmsharp@gmail.com>. All Rights Reserved.
# License:  GNU General Public License version 3 or later; see LICENSE.txt
# Website:  https://github.com/xbgmsharp/postgsail-helpers
#------------------------------------------------------------------------
#
# Purpose:
# Requirement on Ubuntu/Debian Linux system
# $ apt-get install python3-dateutil python3-simplejson python3-requests python3-openssl jq
#
# Requirement
# $ python -m pip install requests simplejson python-dateutil
#
# Requirement on Windows on Python 3
# <python dir>\Scripts\pip3.exe install requests simplejson
#
# Create a PostgSail metrics
# $ head -1 `ls -d $(ls sailog_metrics*csv | head -1)` > sailog_metrics.csv
# $ cat `ls sailog_metrics*.csv | sort -V ` | grep -v time >> sailog_metrics.csv

import sys, os
# https://urllib3.readthedocs.org/en/latest/security.html#disabling-warnings
# http://quabr.com/27981545/surpress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho
# http://docs.python-requests.org/en/v2.4.3/user/advanced/#proxies
try:
        import simplejson as json
        import requests
        requests.packages.urllib3.disable_warnings()
        import csv
except:
        sys.exit("Please use your favorite method to install the following module requests and simplejson to use this script")

import datetime
import collections
import pprint
import re
from dateutil import parser

# my data rows as dictionary objects
mydict = []
mytrack = []
vessel_id = '1234567890'
vessel_name = ''
base_url = 'https://saillogger.com/log/'

_headers = {
    'User-Agent' : 'saillog exporter', # User-agent
    'Connection' : 'Keep-Alive',
}

pp = pprint.PrettyPrinter(indent=4)

def write_csv(results, filename):
        """Write list output into a CSV file format"""
        print("CSV output file: {0}".format(filename))
        # Write result CSV
        with open(filename, 'w', encoding = 'utf-8', newline='') as fp:
                mycsv = csv.DictWriter(fp, fieldnames=list(results[0].keys()), quoting=csv.QUOTE_ALL)
                mycsv.writeheader()
                for row in results:
                    mycsv.writerow(row)
        fp.close()

def js_to_python_dict(js_obj_str):
    # Step 1: Replace new Date(...) with quoted string (optional)
    #js_obj_str = re.sub(r'new Date\(.*\)', r'"\1"', js_obj_str)
    #js_obj_str = re.sub(r'new Date\(([^)]*)\)', r'"\1"', js_obj_str)
    js_obj_str = re.sub(r'\n(\w+):', r'"\1":', js_obj_str)
    #print('js_obj_str1', js_obj_str)

    js_obj_str = re.sub(r'new Date\(\"(.*?)\"\)', r'"\1"', js_obj_str)
    #print('js_obj_str2', js_obj_str)

    # Step 3: Replace single quotes with double quotes (optional, if you expect single quotes)
    js_obj_str = js_obj_str.replace("'", '"')
    #print('js_obj_str3', js_obj_str)

    # Step clean up json
    # Remove the last comma before }
    js_obj_str = re.sub(r',\s*}', '}', js_obj_str)

    try:
        # Step 4: Use ast.literal_eval safely
        return json.loads(js_obj_str)
    except Exception as e:
        print(f"Failed to parse: {js_obj_str}\nError: {e}")
        return None

def api_get_log(url, vessel_name):
        """Fetch log entry and parse it"""
        print(base_url+url)
        r = requests.get(base_url+url, headers=_headers, timeout=(5, 60))
        if r.status_code != 200:
            print("Error fetching log entry : {status} [{text}]".format(
                status=r.status_code, text=r.text))
            return None
        else:
            reg_id = re.findall('var id = (.*);', r.text)
            #print(reg_id[0])
            #reg_trackPoints = re.findall('var trackPoints = (.*)\.reverse\(\);', r.text)
            match = re.search(r'var\s+trackPoints\s*=\s*(\[[\s\S]*?\])\.reverse\(\);', r.text)
            reg_trackPoints = match.group(1)
            #print(reg_trackPoints)
            object_blocks = re.findall(r'{[^{}]*}', reg_trackPoints)
            #print(object_blocks)
            parsed_objects = [js_to_python_dict(obj) for obj in object_blocks]
            #print(parsed_objects[0]['id'])
            #trackPoints = re.sub(r'new Date\(', '', reg_trackPoints[0])
            #trackPoints = re.sub(r'\)', '', trackPoints)
            #trackPoints = re.sub(r'],]', ']]', trackPoints)
            # [41.4417083333, 2.250975, 158.9, new Date("Sat, 14 May 2022 12:22:33 +0000"), 0.0, 7.4, 524569]
            # [ lat, lng , COG, time, SOG, wind_speed, id]
            # [38.1240411, 13.3709678, 343.5, new Date("Sun, 23 Apr 2023 13:28:23 +0000"), 0.0, 12.9, '', 1024791]
            #print(trackPoints)
            #trackPoints = trackPoints[2:-2].split('],[')
            reg_linePoints = re.findall('var linePoints = (.*);', r.text)
            #print(reg_linePoints[0])
            reg_name = re.findall('var name = "(.*)";', r.text)
            #print(reg_name[0])
            reg_start_loc = re.findall('var start_location = "(.*)";', r.text)
            #print(reg_start_loc[0])
            reg_end_loc = re.findall('var end_location = "(.*)";', r.text)
            #print(reg_end_loc[0])
            reg_max_speed = re.findall('var max_speed = (.*);', r.text)
            reg_avg_speed = re.findall('var avg_speed = (.*);', r.text)
            reg_max_wind_speed = re.findall('var max_wind_speed = (.*);', r.text)
            reg_avg_wind_speed = re.findall('var avg_wind_speed = (.*);', r.text)
            # create csv from trackPoints
            mytrack = []
            i = 0
            for entry in parsed_objects:
                #print(entry)
                #lat, lng, cog, day, time, sog, wind_speed, note, _id = entry.split(', ')
                lat = entry['lat']
                lng = entry['lng']
                cog = entry['speed']
                time = entry['date']
                sog = entry['speed']
                wind_speed = entry['windSpeed']
                note = entry['notes']
                heading = entry['heading']
                _id = entry['id']  # `id` is a Python builtin, so safer to call it `_id`

                # map to metrics table
                # first entry moored
                if i == 0:
                    dt = parser.parse(time)
                    newtime = dt - datetime.timedelta(0,60) # - 30 seconds
                    mylog = {}
                    mylog['time'] = newtime
                    mylog['client_id'] = None
                    mylog['vessel_id'] = vessel_id
                    mylog['latitude'] = lat
                    mylog['longitude'] = lng
                    mylog['speedoverground'] = sog
                    mylog['courseovergroundtrue'] = None
                    mylog['anglespeedapparent'] = None
                    mylog['windspeedapparent'] = wind_speed
                    mylog['status'] = 'moored'
                    mylog['metrics'] = json.dumps({
                        "navigation.headingTrue": heading,
                        "environment.wind.speedTrue": wind_speed
                    })
                    #print(mylog)
                    mytrack.append(mylog)
                mylog = {}
                mylog['time'] = time
                mylog['client_id'] = None
                mylog['vessel_id'] = vessel_id
                mylog['latitude'] = lat
                mylog['longitude'] = lng
                mylog['speedoverground'] = sog
                mylog['courseovergroundtrue'] = None
                mylog['anglespeedapparent'] = None
                mylog['windspeedapparent'] = wind_speed
                mylog['status'] = 'sailing'
                mylog['metrics'] = json.dumps({
                      "navigation.headingTrue": heading,
                      "environment.wind.speedTrue": wind_speed
                })
                #print(mylog)
                mytrack.append(mylog)
                # last entry moored
                #print(len(trackPoints))
                #print(i+1)
                if len(parsed_objects) == i+1:
                    dt = parser.parse(time)
                    newtime = dt + datetime.timedelta(0,60) # + 30 seconds
                    mylog = {}
                    mylog['time'] = newtime
                    mylog['client_id'] = None
                    mylog['vessel_id'] = vessel_id
                    mylog['latitude'] = lat
                    mylog['longitude'] = lng
                    mylog['speedoverground'] = sog
                    mylog['courseovergroundtrue'] = None
                    mylog['anglespeedapparent'] = None
                    mylog['windspeedapparent'] = wind_speed
                    mylog['status'] = 'moored'
                    mylog['metrics'] = json.dumps({
                         "navigation.headingTrue": heading,
                         "environment.wind.speedTrue": wind_speed
                    })
                    #print(mylog)
                    mytrack.append(mylog)
                i += 1
            write_csv(mytrack, f'sailog_metrics_{vessel_name}_{reg_id[0]}.csv')
            # create geom gis linestring from linePoints
            linestring = ""
            # Convert string to array
            linePoints = reg_linePoints[0][2:-3].split('],[')
            #print(linePoints[0])
            #print(linePoints[-1])
            for coord in linePoints:
                #print(coord)
                lat, lng = coord.split(',')
                linestring += "{} {},".format(lng, lat)
            #print(linestring)
            # Return Geometry linestring alone with first and last coordinates
            return ("LINESTRING ({})".format(linestring[1:-1]), linePoints[0], linePoints[-1])

def main():
        """
        Main program loop
        * Read CSV
        * Write to CSV
        """
        with open('./Saillogger_Logs_Export.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            vessel = None
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    vessel_name = row[2]
                    geom = api_get_log(row[0], vessel_name)
                    #print(f'[{row[1]}] FROM [{row[2]}] TO [{row[3]}] start [{row[4]}] end [{row[5]}] geom {geom}.')
                    _from_lat, _from_lng = geom[1].split(',')
                    _to_lat, _to_lng = geom[2].split(',')
                    # map to logbook table
                    mylog = {}
                    mylog['is_in_trip'] = False
                    mylog['name'] = row[1]
                    mylog['_from'] = row[2]
                    mylog['_from_lat'] = _from_lat
                    mylog['_from_lng'] = _from_lng
                    mylog['_to'] = row[3]
                    mylog['_to_lat'] = _to_lat
                    mylog['_to_lng'] = _to_lng
                    mylog['_from_time'] = row[4]
                    mylog['_to_time'] = row[5] 
                    mylog['track_geom'] = geom[0]
                    #print(mylog)
                    mydict.append(mylog)
                    line_count += 1
                    #sys.exit()

            print(f'Processed {line_count} lines.')
            write_csv(mydict, f'sailog_logbook_{vessel_name}.csv')
            
if __name__ == '__main__':
        main()
