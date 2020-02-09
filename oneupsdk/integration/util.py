
import csv as _csv


def parse_csv(content):
    records = [
        record
        for record in _csv.DictReader(
            content.decode().splitlines(),
            quotechar='"',
            delimiter=',',
            quoting=_csv.QUOTE_ALL,
            skipinitialspace=True)
    ]
    return records
