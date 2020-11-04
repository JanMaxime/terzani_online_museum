import pandas as pd

def search_database(item, collection):
    print("search " + item)
    for y in collection.find({ "obj_boxes." + item : {"$exists" : True}}):
        print(y)
        print("hshsdh")
    return None