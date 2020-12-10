import json
import pickle
from typing import Dict, List
from pathlib import Path


def dict_to_json(dict_to_save: Dict, path: Path):
    with open(path, "w", encoding='utf-8') as outfile:
        json.dump(dict_to_save, outfile, indent=4, ensure_ascii=False)


def json_to_dict(path: Path):
    with open(path, encoding='utf-8') as jfile:
        return json.load(jfile)


def list_to_pickle(list_to_save: List, path: Path):
    with open(path, 'wb') as file:
        pickle.dump(list_to_save, file)


def pickle_to_list(path: Path):
    return pickle.load(open(path, "rb"))
