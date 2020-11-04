import pandas as pd

def search_item_in_database(item, collection):
    return list(collection.find( {"obj_boxes." + item : {"$exists" : True}}))