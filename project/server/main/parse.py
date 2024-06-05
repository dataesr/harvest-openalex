from project.server.main.logger import get_logger

logger = get_logger(__name__)

def parse_notice(notice):
    res = {}
    res["sources"] = ["openalex"]
    doi = notice.get("doi")
    if doi:
        doi = doi.replace('https://doi.org/', '').lower()
        res["doi"] = doi
        res["id"] = "doi"+doi
    res["title"] = notice.get("title", "")
    external_ids = []
    external_ids.append({ "id_type": "openalex", "id_value": res.get("openalex_id") })
    if doi:
        external_ids.append({ "id_type": "doi", "id_value": doi })
    for id in notice.get("ids"):
        if id not in ["doi", "openalex"]:
            external_ids.append({ "id_type": id, "id_value": notice.get("ids").get(id) })
    if notice.get("publication_year"):
        res["publication_year"] = str(notice["publication_year"])
    if notice.get("language"):
        res["lang"] = notice.get("language")
    res["url"] = notice.get("id")
    # Add authors & affiliations
    # Add classifications
    # TODO: Validate against schema.json
    return res



