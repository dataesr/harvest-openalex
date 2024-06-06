from project.server.main.logger import get_logger

logger = get_logger(__name__)


def get_author_position(name, numbers_of_authors):
  if name == "first":
    return 1
  if name == "last":
    return numbers_of_authors
  return False


def get_author_affiliations(institutions):
  affiliations = []
  for institution in institutions:
    a = {}
    country = institution.get("country_code")
    if country:
      a["country"] = country
    a["external_ids"] = [{ "id_type": "openalex", "id_value": institution.get("id") }]
    ror = institution.get("ror")
    if ror:
      a["external_ids"].append({ "id_type": "ror", "id_value": ror })
    name = institution.get("display_name")
    if name:
      a["name"] = name
    affiliations.append(a)
  return affiliations


def get_authors(authorships):
    numbers_of_authors = len(authorships)
    authors = []
    for author in authorships:
        a = {}
        affiliations = get_author_affiliations(author.get("institutions", []))
        if affiliations:
            a["affiliations"] = affiliations
        author_position = get_author_position(author.get("author_position"), numbers_of_authors)
        if author_position:
            a["author_position"] = author_position
        a["corresponding"] = author.get("is_corresponding")
        a["external_ids"] = [{ "id_type": "openalex", "id_value": author.get("author").get("id") }]
        a["full_name"] = author.get("raw_author_name")
        orcid = author.get("author", {}).get("orcid")
        if orcid:
            a["orcid"] = orcid.replace("https://orcid.org/", "")
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
    classification["label"] = topic.get("subfield").get("display_name")
    classification["code"] = topic.get("subfield").get("id")
    classification["reference"] = "openalex"
    classification["level"] = "subfield"
    classification["label"] = topic.get("field").get("display_name")
    classification["code"] = topic.get("field").get("id")
    classification["reference"] = "openalex"
    classification["level"] = "field"
    classification["label"] = topic.get("domain").get("display_name")
    classification["code"] = topic.get("domain").get("id")
    classification["reference"] = "openalex"
    classification["level"] = "domain"
    classifications.append(classification)
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

def parse_notice(notice):
    res = {}
    res["sources"] = ["openalex"]
    doi = notice.get("doi")
    if doi:
        doi = doi.replace('https://doi.org/', '').lower()
        res["doi"] = doi
        res["id"] = "doi"+doi
    external_ids = []
    external_ids.append({ "id_type": "openalex", "id_value": res.get("openalex_id") })
    if doi:
        external_ids.append({ "id_type": "doi", "id_value": doi })
    for id in notice.get("ids"):
        if id not in ["doi", "openalex"]:
            external_ids.append({ "id_type": id, "id_value": notice.get("ids").get(id) })
    res["title"] = notice.get("title", "")
    source = notice.get("primary_location", {}).get("source", {})
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
    publication_type = notice.get("type_crossref")
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
                issn_print = [issn for issn in issn_print if issn != issn_electronic]
            if len(issn_print) > 0:
                res["issn_print"] = issn_print[0]
    return res



