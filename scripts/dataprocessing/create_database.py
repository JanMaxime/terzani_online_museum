from pathlib import Path
from purl import URL
from typing import List
import os
import json
import pymongo
import random
# Import Vison API related libraries
from google.cloud import vision
# Import dotenv library to get environment variables
from dotenv import load_dotenv
from tqdm import tqdm
from terzani.scrapping.photo_scrapping import get_collections, get_iiif_collection
from terzani.annotation.photo_annotation import get_annotation, add_tag
from terzani.featurevec.photo_vector import get_vector, load_resnet_model
from terzani.utils.diskop import dict_to_json, json_to_dict, list_to_pickle, pickle_to_list


def main(data_folder: Path, scrap_image_iiif: bool,
         collection_url: URL, unsupported_collections: List,
         col_cntry_json: Path, server: str, manifest: str,
         annotate_iiif: bool, nu_photos: str,
         create_db: bool, db_name: str,  tag_collection_name: str,
         annotation_collection_name: str,
         fvector_collection_name: str):

    # setting up the service account to use Google Vision API and Mongo DB
    load_dotenv()

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv(
        'GOOGLE_APPLICATION_CREDENTIALS')

    MONGO_CLIENT_URI = os.getenv('MONGO_URI')
    os.environ['MONGO_CLIENT_URI'] = MONGO_CLIENT_URI

    iiif_annotation_file = data_folder.joinpath("recto_iiif_images.json")

    # scrap images
    if scrap_image_iiif:
        recto_iiif = list()

        image_collections = get_collections(
            collection_url, unsupported_collections)

        col_cntry_map = json_to_dict(col_cntry_json)

        for sub_col in tqdm(image_collections):

            sub_col_url = server + sub_col + manifest
            sub_col_cntry = col_cntry_map[sub_col]

            recto_iiif.extend(get_iiif_collection(sub_col_url, sub_col_cntry))

        try:

            list_to_pickle(recto_iiif, iiif_annotation_file)

        except:
            raise Exception("Failed to save the scrapped images to json")

    # read the images with iiif annotation
    try:
        all_photos = pickle_to_list(iiif_annotation_file)
        if nu_photos == "full":
            nu_photos = len(all_photos)
        else:
            nu_photos = int(nu_photos)

        all_photos = random.sample(all_photos, nu_photos)
    except FileNotFoundError:
        raise Exception("JSON with IIIF image information not existent")

    # load the already tagged, annotated images.
    tagged_images_file = data_folder.joinpath("tagged_images.json")
    annotated_images_file = data_folder.joinpath("annotated_images.json")
    annotation_failed_images_file = data_folder.joinpath(
        "annotation_failed_images.json")
    image_vectors_file = data_folder.joinpath("image_vectors.json")
    fvector_failed_images_file = data_folder.joinpath(
        "fvector_failed_images.json")

    try:
        tagged_images = json_to_dict(tagged_images_file)
        annotated_images = json_to_dict(annotated_images_file)
    except FileNotFoundError:
        tagged_images = dict()
        annotated_images = dict()

    try:
        annotation_failed_images = json_to_dict(annotation_failed_images_file)
    except FileNotFoundError:
        annotation_failed_images = dict()

    try:
        image_vecs = json_to_dict(image_vectors_file)
    except FileNotFoundError:
        image_vecs = dict()

    try:
        fvector_failed_images = json_to_dict(fvector_failed_images_file)
    except FileNotFoundError:
        fvector_failed_images = dict()

    if annotate_iiif:
        # Client to access the Google vision API
        client = vision.ImageAnnotatorClient()

        # loading pretrained resent model
        model, layer, scaler, normalize, to_tensor = load_resnet_model()

        # go over each photo in the photo collection and get the annotation and feature vector

        for photo in tqdm(all_photos):
            # if the image is already not present in the either annotated and failed dictionaries
            if (
                    photo.iiif["label"] not in annotated_images and
                    photo.iiif["label"] not in annotation_failed_images and
                    photo.iiif["label"] not in image_vecs and
                    photo.iiif["label"] not in fvector_failed_images
            ):
                # get the image label
                img_lbl = photo.iiif["label"]
                img_country = photo.country

                result = get_annotation(photo, client)

                if not result["success"]:
                    annotation_failed_images[img_lbl] = {}
                    annotation_failed_images[img_lbl]["error"] = [
                        result["error_code"], result["error_message"]]

                else:
                    annotated_images[img_lbl] = {}

                    # store the iiif description
                    annotated_images[img_lbl]["iiif"] = photo.iiif

                    # Add the label and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["labels"], tagged_images, img_lbl)

                    # Add the web entity and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["webent"], tagged_images, img_lbl)

                    # we add the landmarks and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["lndmks"], tagged_images, img_lbl)

                    # we add the logo names and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["logos"], tagged_images, img_lbl)

                    # we add the object names and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["objects"], tagged_images, img_lbl)

                    # we add the text and image label to the dictionary to perform search
                    tagged_images = add_tag(
                        result["text"], tagged_images, img_lbl)

                    # store the generated object boxes into the dictionary.
                    annotated_images[img_lbl]["obj_boxes"] = result["obj_boxes"]

                    # store the generated land mark information into the dictionary.
                    if result["landmark_info"]:
                        annotated_images[img_lbl]["landmark_info"] = result["landmark_info"]

                    # store the generated land mark information into the dictionary.
                    annotated_images[img_lbl]["country"] = img_country

                    # get the feature vector of the image
                    try:
                        feature_vec = get_vector(photo.get_photo_link(
                        ), model, layer, scaler, normalize, to_tensor)
                        image_vecs[img_lbl] = feature_vec.tolist()
                    except:
                        fvector_failed_images.append(img_lbl)

        # save the tagged, annotated images.
        dict_to_json(tagged_images, tagged_images_file)
        dict_to_json(annotated_images, annotated_images_file)
        dict_to_json(annotation_failed_images, annotation_failed_images_file)
        dict_to_json(image_vecs, image_vectors_file)
        dict_to_json(fvector_failed_images, fvector_failed_images_file)

    if create_db:
        # creating a client to work with mongo db
        mongoclient = pymongo.MongoClient(MONGO_CLIENT_URI)
        # selecting the photo database
        mongo_db = mongoclient[db_name]

        # Storing the Image Tags in the collection tag_collection_name
        mongo_tag_collection = mongo_db[tag_collection_name]

        # checking if the collection is not empty
        if mongo_tag_collection.estimated_document_count() != 0:
            # empty the collection
            mongo_tag_collection.drop()
            # create a empty collection
            mongo_tag_collection = mongo_db[tag_collection_name]
        # inserting the dictionary into the db
        for tag, img_labels in tqdm(tagged_images.items()):
            mongo_tag_collection.insert_one({"tag": tag, "images": img_labels})

        # Storing the Image Annotation in the collection annotation_collection_name
        mongo_box_collection = mongo_db[annotation_collection_name]

        # checking if the collection is not empty
        if mongo_box_collection.estimated_document_count() != 0:
            # empty the collection
            mongo_box_collection.drop()
            # create a empty collection
            mongo_box_collection = mongo_db[annotation_collection_name]

        # inserting the dictionary into the db
        for img_label, annotation in tqdm(annotated_images.items()):
            mongo_box_collection.insert_one(
                {"label": img_label, "annotation": annotation})

        # Storing the Image feature vector in the collection named fvector_collection_name
        mongo_vec_collection = mongo_db[fvector_collection_name]

        # checking if the collection is not empty
        if mongo_vec_collection.estimated_document_count() != 0:
            # empty the collection
            mongo_vec_collection.drop()
            # create a empty collection
            mongo_vec_collection = mongo_db[fvector_collection_name]

        # inserting the dictionary into the db
        for img_label, img_vec in tqdm(image_vecs.items()):
            mongo_vec_collection.insert_one(
                {"image": img_label, "feature_vec": img_vec})


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file",
                        help="the path to the configuration file", type=Path, required=True)
    args = parser.parse_args()

    config_file_path = Path(args.config_file)

    with open(args.config_file) as jfile:
        params = json.load(jfile)

    params["data_folder"] = Path(params["data_folder"])
    params["data_folder"].mkdir(parents=True, exist_ok=True)

    params["scrap_image_iiif"] = eval(params["scrap_image_iiif"])
    params["annotate_iiif"] = eval(params["annotate_iiif"])
    params["create_db"] = eval(params["create_db"])

    if params["scrap_image_iiif"]:
        if ("collection_url" not in params) or (not params["collection_url"]):
            raise Exception(
                "Collection URL not specified in the configuration file")
        if ("unsupported_collections" not in params) or (not params["unsupported_collections"]):
            raise Exception(
                "Unsupported collections not specified in the configuration file")
        if ("col_cntry_json" not in params) or (not params["col_cntry_json"]):
            raise Exception(
                "Country collection mapping Json not specified in the configuration file")
        if ("server" not in params) or (not params["server"]):
            raise Exception(
                "Collection server not specified in the configuration file")
        if ("manifest" not in params) or (not params["manifest"]):
            raise Exception(
                "Collection manifest not specified in the configuration file")

    if params["create_db"]:
        if ("db_name" not in params) or (not params["db_name"]):
            raise Exception(
                "Database name not specified in the configuration file")

        if ("tag_collection_name" not in params) or (not params["tag_collection_name"]):
            raise Exception(
                "tag collection name not specified in the configuration file")

        if ("annotation_collection_name" not in params) or (not params["annotation_collection_name"]):
            raise Exception(
                "Annotation collection name not specified in the configuration file")

        if ("fvector_collection_name" not in params) or (not params["fvector_collection_name"]):
            raise Exception(
                "Feature vectors collection name not specified in the configuration file")

    if "nu_photos" not in params:
        params["nu_photos"] = "full"

    main(**params)
