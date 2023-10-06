import json
import os
import requests
import math
from retry import retry
from urllib.parse import quote_plus

from project.server.main.logger import get_logger
from project.server.main.utils_swift import upload_object

logger = get_logger(__name__)

CRAWLER_SERVICE = os.getenv('CRAWLER_SERVICE')
crawler_endpoint_url = f'{CRAWLER_SERVICE}/crawl'

PER_PAGE = 200
OPENALEX_API_KEY = os.getenv('OPENALEX_API_KEY')

def save_data(data, collection_name, year_start, year_end):
    year_start_end = f'{year_start}_{year_end}'
    current_file = f'openalex_{year_start_end}.json'
    json.dump(data, open(current_file, 'w'))
    os.system(f'gzip {current_file}')
    upload_object('openalex', f'{current_file}.gz', f'{collection_name}/raw/{current_file}.gz')
    os.system(f'rm -rf {current_file}.gz')

@retry(delay=300, tries=5, logger=logger)
def query_openalex(query, start_year, end_year, per_page):
    url = f'https://api.openalex.org/works?filter={query}'
    url += f',publication_year:{start_year}-{end_year}'
    url += f'&per_page={per_page}'
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
            url = f'http://doi.org/{doi}'
            crawl_list.append({'url': url, 'title': title})
    logger.debug(f'posting {len(crawl_list)} elements to crawl')
    requests.post(crawler_endpoint_url, json={'list': crawl_list})

def harvest_and_save(collection_name, query, year_start, year_end):
    
    nb_results = query_openalex(query, year_start, year_end, 1)['meta']['count']
    nb_pages = math.ceil(nb_results/PER_PAGE)

    data = []
    for p in range(1, nb_pages+1):
        current_data = query_openalex(query, 2021, 2021, 200)['results']
        send_to_crawler(current_data)
        data += current_data

    logger.debug(f'{year_start_end}|{len(data)}')
    save_data(data, collection_name, year_start, year_end)

def harvest_all(collection_name, query, year_start, year_end):
    for year in range(year_start, year_start+1):
        harvest_and_save(collection_name, query, year, year)
