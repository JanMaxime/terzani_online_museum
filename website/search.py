import pandas as pd

def search_bb_and_tags(item, collection):
    return list(collection.find({"$or" : [{"obj_boxes." + item : {"$exists" : True}}, {"tags" : item }]}))

def search_bb(item, collection):
    return list(collection.find({"obj_boxes." + item : {"$exists" : True}}))


def search_country(country, collection):
    return list(collection.find({ "annotation.country" : country}))

    
def get_markers(collection):
    return list(collection.find({"annotation.landmark_info" : {"$exists" : True}}))