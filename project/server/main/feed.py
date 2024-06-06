import json
import math
import os
import requests
from retry import retry

from project.server.main.logger import get_logger
from project.server.main.parse import parse_notice
from project.server.main.utils import validate_json_schema
from project.server.main.utils_swift import upload_object

logger = get_logger(__name__)

CRAWLER_SERVICE = os.getenv('CRAWLER_SERVICE')
crawler_endpoint_url = f'{CRAWLER_SERVICE}/crawl'
PER_PAGE = 200
OPENALEX_API_KEY = os.getenv('OPENALEX_API_KEY')


def save_data(data, collection_name, year_start, year_end, data_type):
    year_start_end = f'{year_start}_{year_end}'
    current_file = f'openalex_{year_start_end}.json'
    json.dump(data, open(current_file, 'w'))
    os.system(f'gzip {current_file}')
    upload_object('openalex', f'{current_file}.gz', f'{collection_name}/{data_type}/{current_file}.gz')
    os.system(f'rm -rf {current_file}.gz')


@retry(delay=300, tries=5, logger=logger)
def query_openalex(query, start_year, end_year, per_page, cursor):
    url = f'https://api.openalex.org/works?filter={query}'
    url += f',publication_year:{start_year}-{end_year}'
    url += f'&per_page={per_page}'
    url += f'&cursor={cursor}'
    url += f'&api_key={OPENALEX_API_KEY}'
    r = requests.get(url)
    return r.json()


def send_to_crawler(current_data):
    crawl_list = []
    for c in current_data:
        title = c.get('title')
        doi = c.get('doi')
        if title and doi:
            doi = doi.strip()
            title = title.strip()
            url = f'{doi}'
            crawl_list.append({'url': url, 'title': title})
    logger.debug(f'posting {len(crawl_list)} elements to crawl')
    requests.post(crawler_endpoint_url, json={'list': crawl_list})


def harvest_and_save(collection_name, query, year_start, year_end, send_to_crawler):
    nb_results = query_openalex(query, year_start, year_end, 1, "*").get("meta", {}).get("count")
    logger.debug(f"{nb_results} results for {collection_name} and query {query} {year_start} {year_end}")
    nb_pages = math.ceil(nb_results / PER_PAGE)

    data, parsed_data = [], []
    for page in range(1, nb_pages + 1):
        if page == 1:
            cursor = "*"
        else:
            cursor = current_cursor
        query_res = query_openalex(query, year_start, year_end, PER_PAGE, cursor)
        current_data = query_res.get("results", [])
        current_cursor = query_res.get("meta", {}).get("next_cursor")
        if send_to_crawler:
            send_to_crawler(current_data)
        data += current_data
        parsed_data += [parse_notice(n) for n in current_data]

    schema = json.load(open("schema.json", "r"))
    is_valid = validate_json_schema(data=parsed_data, _schema=schema)
    if is_valid:
        logger.debug(f'{year_start}-{year_end} | {len(data)}')
        save_data(data, collection_name, year_start, year_end, 'raw')
        save_data(parsed_data, collection_name, year_start, year_end, 'parsed')
    else:
        logger.error("Parsed data are not validated against the JSON schema. Please see errors logged before.")


def harvest_all(collection_name, query, year_start, year_end, send_to_crawler):
    for year in range(year_start, year_end+1):
        harvest_and_save(collection_name, query, year, year, send_to_crawler)
