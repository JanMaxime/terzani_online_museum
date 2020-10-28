import pandas as pd

def search_database(item):
    annos = pd.read_pickle("static/test_anno.pickle")
    for anno in annos:
        if anno["name"].lower() == item.lower():
            return anno
    return None