import json
import requests
from bs4 import BeautifulSoup
import urllib.request
from purl import URL
from typing import List, Union

from ..utils.types import Terzani_Photo


def valid_collection(tag: str, unsupported_collections: List) -> Union[str, None]:
    """
    This function accepts the html tag and returns id of the collection if the collection is valid.

    :param tag (str): The html link tag
    :param unsupported_collections (list):  The list of collections ids to be exculded
    :return col_id (str): The id of the collection.
    """

    try:
        link = tag["href"]

        if link.startswith("/collections/show/") and link[-4:] not in unsupported_collections:
            col_id = link[-4:]
        else:
            col_id = None

        return col_id

    except KeyError:
        raise("Tag is not a Refernce/Link tag")


def get_collections(collection_url: URL, unsupported_collections: List) -> List:
    """
    This function accepts the html content from the given URL and returns list of collection ids.

    :param collection_url (URL): The primary collection URL
    :param unsupported_collections (list):  The list of collections ids to be exculded
    :return clean_collections (list): The ids of the valid collections.
    """

    req = requests.get(collection_url)
    req_soup = BeautifulSoup(req.text, "html.parser")

    collections = [valid_collection(tag_a, unsupported_collections)
                   for tag_a in req_soup.find_all("a", href=True)]
    clean_collections = list(filter(None.__ne__, collections))

    return clean_collections


def get_iiif_collection(sub_collection_url: URL, collection_country: str) -> List:
    """
    This function accepts the sub collection url and country of the collection,
    and returns list of IIIF annotations along with the country information for images present in the collection.

    :param sub_collection_url (URL): The seconday collection URL
    :param collection_country (str):  The name of the country to which the collection belongs
    :return sub_collection_iiif (list): The list of IIIF annotation of photos in the collection
    """

    sub_collection_iiif = list()

    url_resp = urllib.request.urlopen(sub_collection_url)

    content = json.loads(url_resp.read())

    for entry in content["sequences"][0]["canvases"]:
        if entry["label"] == None:
            continue
        if entry["label"].lower().endswith("recto"):
            sub_collection_iiif.append(Terzani_Photo(
                entry, collection_country))

    return sub_collection_iiif
