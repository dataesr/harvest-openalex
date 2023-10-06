import time
import datetime
import os
import requests
from project.server.main.feed import harvest_all

from project.server.main.logger import get_logger

logger = get_logger(__name__)

def create_task_harvest(arg):
    collection_name = arg.get('collection_name')
    query = arg.get('query', 'institutions.country_code:FR')
    year_start = arg.get('year_start', 2013)
    year_end = arg.get('year_start', 2023)
    if collection_name:
        harvest_all(collection_name, query, year_start, year_end)
