import time
import datetime
import os
import requests
from project.server.main.feed import harvest_all, reset_mongo, to_light_all, to_bso_local
from project.server.main.matcher import check_countries

from project.server.main.logger import get_logger

logger = get_logger(__name__)

def create_task_harvest(arg):
    collection_name = arg.get('collection_name')
    query = arg.get('query', 'institutions.country_code:FR')
    year_start = arg.get('year_start', 2013)
    year_end = arg.get('year_end', 2024)
    send_to_crawler = arg.get('send_to_crawler', False)
    if collection_name:
        harvest_all(collection_name, query, year_start, year_end, send_to_crawler)

def create_task_light(arg):
    collection_name = arg.get('collection_name')
    year_start = arg.get('year_start', 2013)
    year_end = arg.get('year_end', 2024)
    if collection_name:
        to_light_all(collection_name, year_start, year_end)

def create_task_bso(arg):
    collection_name = arg.get('collection_name')
    year_start = arg.get('year_start', 2013)
    year_end = arg.get('year_end', 2024)
    if collection_name:
        to_bso_local(collection_name, year_start, year_end)

def create_task_check_affiliations(arg):
    collection_name = arg.get('collection_name')
    year_start = arg.get('year_start', 2013)
    year_end = arg.get('year_end', 2023)
    if collection_name:
        check_countries(collection_name, year_start, year_end)
