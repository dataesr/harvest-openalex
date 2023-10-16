import json
import os
import requests
import time
import math
import multiprocess as mp
from retry import retry
from urllib.parse import quote_plus
import timeout_decorator
import pandas as pd

from project.server.main.logger import get_logger
from project.server.main.utils_swift import download_object, upload_object

logger = get_logger(__name__)

AFFILIATION_MATCHER_SERVICE = os.getenv('AFFILIATION_MATCHER_SERVICE')
matcher_endpoint_url = f'{AFFILIATION_MATCHER_SERVICE}/match_list'

def is_na(x):
    return not(not x)

def chunks(lst, n):
    if len(lst) == 0:
        return [[]]
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def exception_handler(func):
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exception:
            logger.error(f'{func.__name__} raises an error through decorator "exception_handler".')
            logger.error(exception)
            return None
    return inner_function

def get_data(collection_name, year_start, year_end):
    year_start_end = f'{year_start}_{year_end}'
    current_file = f'openalex_{year_start_end}.json'
    download_object('openalex', f'{collection_name}/raw/{current_file}.gz',  f'{current_file}.gz')
    return  f'{current_file}.gz'

@timeout_decorator.timeout(50*60)
def get_matcher_results(affiliations: list, proc_num = 0, return_dict = {}) -> list:
    r = requests.post(matcher_endpoint_url, json={'affiliations': affiliations,
                                                    'match_types': ['country'],
                                                  'queue': 'matcher_short'})
    task_id = r.json()['data']['task_id']
    logger.debug(f'New task {task_id} for matcher')
    for i in range(0, 100000):
        r_task = requests.get(f'{AFFILIATION_MATCHER_SERVICE}/tasks/{task_id}').json()
        try:
            status = r_task['data']['task_status']
        except:
            logger.error(f'Error in getting task {task_id} status : {r_task}')
            status = 'error'
        if status == 'finished':
            return_dict[proc_num] = r_task['data']['task_result']
            return return_dict[proc_num]
        elif status in ['started', 'queued']:
            time.sleep(2)
            continue
        else:
            logger.error(f'Error with task {task_id} : status {status}')
            logger.debug(f'{r_task}')
            return_dict[proc_num] = []
            return return_dict[proc_num]

@exception_handler
def get_matcher_parallel(affil_chunks):
    # prend une liste de liste d'affiliations
    logger.debug(f'start parallel with {len(affil_chunks)} sublists')

    manager = mp.Manager()
    return_dict = manager.dict()

    jobs = []
    for ix, c in enumerate(affil_chunks):
        if len(c) == 0:
            continue
        p = mp.Process(target=get_matcher_results, args=(c, ix, return_dict))
        p.start()
        jobs.append(p)
    for p in jobs:
        p.join()
    logger.debug(f'end parallel')
    flat_list = [item for sublist in return_dict.values() for item in sublist]
    return flat_list

def check_countries(collection_name, year_start, year_end) -> dict:
    data = get_data(collection_name, year_start, year_end)
    publications=pd.read_json(data).to_dict(orient='records')
    logger.debug(f'Matching affiliations for {len(publications)} publications')
    # Retrieve all affiliations
    all_affiliations = set([])
    for publication in publications:
        for aut in publication.get('authorships', []):
            current_aff = aut.get('raw_affiliation_string')
            if current_aff and current_aff not in all_affiliations:
                all_affiliations.add(current_aff)
    logger.debug(f'Found {len(all_affiliations)} affiliations in total.')
    # Deduplicate affiliations
    all_affiliations_list = list(filter(is_na, list(all_affiliations)))
    all_affiliations_dict = {}
    logger.debug(f'Found {len(all_affiliations_list)} different affiliations in total.')
    NB_PARALLEL_JOB = 10
    affiliations_list_chunks = list(chunks(all_affiliations_list, 1000))
    for affiliation_list in affiliations_list_chunks:
        nb_publis_per_group = math.ceil(len(affiliation_list)/NB_PARALLEL_JOB)
        groups = list(chunks(lst=affiliation_list, n=nb_publis_per_group))
        logger.debug(f'{len(groups)} groups with {nb_publis_per_group} each')
        all_affiliations_matches = get_matcher_parallel(groups)
        for elt in all_affiliations_matches:
            query = elt['query']
            all_affiliations_dict[query] = set([k['id'].upper() for k in elt['matches']])
    #compare with open alex
    mismatches = {}
    for publication in publications:
        publication_id = publication['id']
        publication_doi = publication.get('doi', 'no_doi')
        for aut in publication.get('authorships', []):
            current_aff = aut.get('raw_affiliation_string')
            if aut.get('raw_affiliation_string') and aut.get('raw_affiliation_string') in all_affiliations_dict:
                computed_countries = all_affiliations_dict[aut.get('raw_affiliation_string')]
                openalex_countries = set(aut.get('countries'))
                if computed_countries != openalex_countries:
                    mismatch_key = f'{publication_id}##{current_aff}'
                    if mismatch_key not in mismatches:
                        mismatches[mismatch_key] = {'id': publication_id, 'doi': publication_doi, 'affiliation': current_aff, 
                                'openalex_countries': list(openalex_countries), 'computed_countries': list(computed_countries)}
                        logger.debug(f'{mismatch_key}##{current_aff} ## {openalex_countries} in openalex ## {computed_countries} computed')
    mismatched = list(mismatches.values())
    mismatch_output = f'mismatch_country_{collection_name}_{year_start}_{year_end}.csv'
    pd.DataFrame(mismatched).to_csv(mismatch_output, index=False)
    upload_object('openalex', mismatch_output, f'{collection_name}/mismatch/{mismatch_output}')
