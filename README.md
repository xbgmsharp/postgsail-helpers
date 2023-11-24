# PostgSail Helpers

There is 2 way to import data from Saillogger.

You can import logs, moorings directly using [PostgSAIL API](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/xbgmsharp/postgsail/main/openapi.json).

Otherwise using the helper script, you can export all the metrics to be import directly in the database. During the import it will generate the logs, stays, moorage and other dependency.

## Purpose:
Python3 script to export saillogger data.

## Requirements
```bash
$ python -m pip install requests simplejson python-dateutil 
```

### On Ubuntu/Debian Linux system
```bash
$ apt-get install python3-dateutil python3-simplejson python3-requests python3-openssl jq
```

### Windows on Python 3
```bash
$ <python dir>\Scripts\pip3.exe install requests simplejson
```

### Docker Python 3 devcontainer
```bash
% docker run --rm -v $PWD:/data postgsail-helpers -i -t mcr.microsoft.com/devcontainers/python bash
```

## Get started
In Saillogger web portal, make you log public in the settings, then export your logs as CSV, you should get a file like `Saillogger_Logs_Export.csv`.

The script read this file and access each log to export all metrics for each log.

If everything goes well, the output consist in a list of files, `sailog_metrics_<boatName>_<logId>.csv` and `sailog_logbook_<boatName>.csv`.

Generate the CSV header file and merge the file in the correct time order.
```bash
$ head -1 `ls -d $(ls sailog_metrics*csv | head -1)` > sailog_metrics.csv
$ cat `ls sailog_metrics*.csv | sort -V` | grep -v time >> sailog_metrics.csv
```

Send the file `sailog_metrics.csv` to me to import it in the database.
