#!/usr/bin/env python3

import argparse
import csv
import dateparser
from pytz import timezone

TIMEZONE_UTC = timezone('UTC')
TIMEZONE_PST = timezone('US/Pacific')


def main(csv_file):
    f = open(csv_file, 'r')
    reader = csv.reader(f)
    headers = next(reader, None)

    column = {}
    for h in headers:
        column[h] = []

    for row in reader:
        for h, v in zip(headers, row):
            column[h].append(v)

    utc_hdr = headers[0]
    utc_col = column[utc_hdr]

    date_col = []
    time_col = []

    for utc in utc_col:
        date_raw = dateparser.parse(utc)
        date_utc = TIMEZONE_UTC.localize(date_raw)
        date_pst = date_utc.astimezone(TIMEZONE_PST)
        date_str = str(date_pst.date())
        time_str = str(date_pst.time())

        date_col.append(date_str)
        time_col.append(time_str)

    # Compute totals per day

    column2 = {}
    for h in headers:
        column2[h] = []

    n = len(date_col)
    j = -1
    d = None
    for i in range(n):
        if d != date_col[i]:
            d = date_col[i]
            j += 1

            column2[utc_hdr].append(d)
            for h in headers[1:]:
                column2[h].append(0.0)

        for h in headers[1:]:
            column2[h][j] += float(column[h][i])

    n = len(column2[utc_hdr])

    line = '"Date"'
    for h in headers[1:]:
        line += ',"{}"'.format(h)
    print(line)

    for i in range(n):
        line = '"{}"'.format(column2[utc_hdr][i])
        for h in headers[1:]:
            line += ',{:.3f}'.format(column2[h][i])
        print(line)


if __name__ == "__main__":
    # execute only if run as a script

    parser = argparse.ArgumentParser(description='Process electric usage.')
    parser.add_argument('-c', '--csv', help='CSV file to parse')

    args = parser.parse_args()
    main(args.csv)
