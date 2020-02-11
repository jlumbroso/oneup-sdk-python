
import csv as _csv

import bs4 as _bs4


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


def find_table(soup, header_query, exact=True):
    # (_bs4.BeautifulSoup, str, _typing.Optional[bool]) -> _typing.Optional[_bs4.BeautifulSoup]
    """
    Locates a table in a BeautifulSoup object by its header row.
    """
    # Normalize header query
    header_query = header_query.strip().lower()

    # Locate all table elements
    tables = soup.find_all("table")

    # Search through them to filter according to the query string
    for i in range(len(tables)):
        try:
            table_caption = tables[i].find("th").text.strip().lower()
            if (exact and header_query == table_caption) or (not exact and header_query in table_caption):
                return tables[i]
        except:
            continue