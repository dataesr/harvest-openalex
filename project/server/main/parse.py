import json
import os
import requests
import math
from retry import retry

from project.server.main.logger import get_logger
from project.server.main.utils_swift import upload_object

logger = get_logger(__name__)

def parse_notice(e):
    res = {}
    res['sources'] = ['openalex']
    res['openalex_id'] = e['id'].split('/')[-1]
    doi = None
    if e.get('doi'):
        doi = e['doi'].replace('https://doi.org/', '').lower()
        res['doi'] = doi
        res['id'] = 'doi'+doi
    res['title'] = e['title']
    external_ids = []
    external_ids.append( {'id_type': 'openalex', 'id_value': res['openalex_id'] })
    if doi:
        external_ids.append( {'id_type': 'doi', 'id_value': doi })
    for k in e.get('ids'):
        if k not in ['doi', 'openalex']:
            external_ids.append( {'id_type': k, 'id_value': e['ids'][k] })
    if e.get('publication_year'):
        res['publication_year'] = str(e['publication_year'])
    if e.get('language'):
        res['lang'] = e['language']
    return res



