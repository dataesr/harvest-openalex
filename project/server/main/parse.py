def get_cited_counts(notice):
    res = {}
    if notice.get("counts_by_year"):
        counts = {}
        for e in notice.get("counts_by_year"):
            y = e['year']
            cnt = e['cited_by_count']
            counts[y] = cnt
        res['cited_by_counts_by_year'] = counts
    return res

def light_parse(notice):
    res = {}
    openalex_id = notice.get("id").split("/")[-1]
    res['openalex_id'] = openalex_id
    doi = notice.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "").lower()
        res["doi"] = doi
        res["id"] = "doi" + doi
    locations = notice.get('locations')
    if isinstance(locations, list):
        for loc in locations:
            landing_page_url = loc.get('landing_page_url')
            if isinstance(landing_page_url, str) and 'hal.science' in landing_page_url:
                res["hal_id"] = landing_page_url.split('/')[-1]
    if doi is None:
        if res.get('hal_id'):
            res['id'] = 'hal'+res['hal_id']
        else:
            return None
    for f in ['apc_list', 'apc_paid', 'topics', 'cited_by_count', 'citation_normalized_percentile', 'fwci']:
        if f in notice:
            res[f] = notice[f]
    citation_counts = get_cited_counts(notice)
    res.update(citation_counts)
    corresponding = get_corresponding(notice)
    res.update(corresponding)
    return res


def get_corresponding(notice):
    countries = []
    if not isinstance(notice.get('authorships'), list):
        return {}
    for index, author in enumerate(notice['authorships']):
        if author.get('is_corresponding') is True:
            if isinstance(author.get('countries', []), list):
                countries += author.get('countries', [])
    countries = list(set(countries))
    countries.sort()
    return {'corresponding_countries': countries}

def get_author_affiliations(institutions):
    affiliations = []
    for institution in institutions:
        a = {}
        country = institution.get("country_code")
        if country:
            a["country"] = country
        a["external_ids"] = [
            {"id_type": "openalex", "id_value": institution.get("id").split('/')[-1]}]
        ror = institution.get("ror")
        if ror:
            a["external_ids"].append({"id_type": "ror", "id_value": ror.split('/')[-1]})
        name = institution.get("display_name")
        if name:
            a["name"] = name
        affiliations.append(a)
    return affiliations


def get_authors(authorships):
    authors = []
    for index, author in enumerate(authorships):
        a = {}
        affiliations = get_author_affiliations(author.get("institutions", []))
        if affiliations:
            a["affiliations"] = affiliations
        a["author_position"] = index + 1
        a["corresponding"] = author.get("is_corresponding")
        a["external_ids"] = [{"id_type": "openalex","id_value": author.get("author").get("id").split('/')[-1]}]
        if isinstance(author.get("raw_author_name"), str):
            a["full_name"] = author.get("raw_author_name")
        orcid = author.get("author", {}).get("orcid")
        if isinstance(orcid, str) and 'orcid' in orcid.lower():
            a["orcid"] = orcid.lower().replace("https://orcid.org/", "").upper()
        authors.append(a)
    return authors


def get_classifications(topics):
    classifications = []
    for topic in topics:
        classification = {}
        classification["label"] = topic.get("display_name")
        classification["code"] = topic.get("id")
        classification["reference"] = "openalex"
        classification["level"] = "topic"
        classifications.append(classification)
        subfield = topic.get("subfield")
        if subfield:
            classification2 = {}
            classification2["label"] = subfield.get("display_name")
            classification2["code"] = subfield.get("id")
            classification2["reference"] = "openalex"
            classification2["level"] = "subfield"
            classifications.append(classification2)
        field = topic.get("field")
        if field:
            classification3 = {}
            classification3["label"] = field.get("display_name")
            classification3["code"] = field.get("id")
            classification3["reference"] = "openalex"
            classification3["level"] = "field"
            classifications.append(classification3)
        domain = topic.get("domain")
        if domain:
            classification4 = {}
            classification4["label"] = domain.get("display_name")
            classification4["code"] = domain.get("id")
            classification4["reference"] = "openalex"
            classification4["level"] = "domain"
            classifications.append(classification4)
    return classifications


def get_grants(grants):
    gs = []
    for grant in grants:
        g = {}
        g["agency"] = grant.get("funder_display_name")
        g["agencyid"] = grant.get("funder")
        g["datasource"] = "openalex"
        gs.append(g)
    return gs


def get_location(notice):
    primary_location = notice.get("primary_location")
    if primary_location:
        return primary_location
    best_oa_location = notice.get("best_oa_location")
    if best_oa_location:
        return best_oa_location
    locations = notice.get("locations")
    if locations and len(locations) > 0:
        return locations[0]
    return False


def parse_notice(notice):
    res = {}
    res["sources"] = ["openalex"]
    external_ids = []
    openalex_id = notice.get("id").split("/")[-1].lower()
    res['openalex_id'] = openalex_id
    external_ids.append({ "id_type": "openalex", "id_value": openalex_id })
    doi = notice.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "").lower()
        res["doi"] = doi
        res["id"] = "doi" + doi
        external_ids.append({ "id_type": "doi", "id_value": doi })

    hal_id = None
    locations = notice.get("locations")
    if isinstance(locations, list):
        for loc in locations:
            if isinstance(loc.get("landing_page_url"), str) and "hal.science" in loc.get("landing_page_url"):
                hal_id = loc.get("landing_page_url").split("/")[-1]
                external_ids.append({ "id_type": "hal_id", "id_value": hal_id })

    for id in notice.get("ids"):
        if id not in ["doi", "openalex"]:
            external_ids.append(
                {"id_type": id, "id_value": notice.get("ids").get(id)})

    if res.get("id") is None and hal_id:
        res["id"] = "hal" + hal_id
    if res.get("id") is None:
        res["id"] = "openalex" + openalex_id
    title = notice.get("title", "")
    if title:
        res["title"] = notice.get("title", "")
    else:
        return None
    citation_counts = get_cited_counts(notice)
    res.update(citation_counts)
    location = get_location(notice)
    source = False
    if location:
        source = location.get("source", {})
    if source:
        publisher = source.get("host_organization_name")
        if publisher:
            res["publisher"] = publisher
    lang = notice.get("language")
    if lang:
        res["lang"] = lang
    publication_year = notice.get("publication_year")
    if publication_year:
        res["publication_year"] = str(publication_year)
    res["url"] = notice.get("id")
    publication_type = notice.get("type")
    if publication_type:
        res["publication_types"] = [publication_type]
    res["authors"] = get_authors(notice.get("authorships", []))
    res["classifications"] = get_classifications(notice.get("topics", []))
    res["grants"] = get_grants(notice.get("grants", []))
    res["has_grant"] = len(notice.get("grants", [])) > 0
    if source:
        issn_electronic = source.get("issn_l")
        if issn_electronic:
            res["issn_electronic"] = issn_electronic
        issn_print = source.get("issn")
        if issn_print:
            if issn_electronic:
                issn_print = [
                    issn for issn in issn_print if issn != issn_electronic]
            if len(issn_print) > 0:
                res["issn_print"] = issn_print[0]
    return res
