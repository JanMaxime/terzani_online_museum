# Import Vison API related libraries
from ..utils.types import IIIF_Photo
from ..utils.clean_text import clean_text
from typing import List, Dict
from google.cloud import vision
from google.cloud.vision_v1 import types
# Import dotenv library to get environment variables
# Import urllib to read images
import urllib.request as ur


def add_tag(new_tags: List, tag_collection: dict, image_label: str):
    """
    This function accepts the new tags, the collection to store the tag, the label of the image and
    returns the updated collection by adding the tags and image label to the collection.

    :param new_tags (List): The List of tags to be added
    :param tag_collection (Dict): The collection containing the tags
    :param image_label (str): The label of the image
    :return tag_collection (Dict): The collection containing the updated tags
    """

    for tag in new_tags:
        if tag not in tag_collection:
            tag_collection[tag] = []
        if image_label not in tag_collection[tag]:
            tag_collection[tag].append(image_label)
    return tag_collection


def add_bbox(new_bbox, new_bbox_name: str, bbox_collection: Dict, is_lobject: bool = False, img_width: float = None,  img_height: float = None) -> Dict:
    """
    This function accepts the detected JSON object, its name, the collection to store the object and
    returns the updated collection by adding the object bounding box to the collection.

    The localised object in google vision API has relative coordinates and the additional
    function parameters serve to identified if the object is a localised object or others

    :param new_bbox (JSON Object): The JSON response of the Google Vision API for the detected object
    :param new_bbox_name (str): The name of the detected object
    :param bbox_collection (Dict): The collection containing the bounding boxes
    :param is_lobject (bool): Boolean value to indicate if the object is a localised object to distinguish from text, logo, landmark
    :param img_width (float): The width of the photograph in which the object is detected
    :param img_height (float):  The height of the photograph in which the object is detected
    :return bbox_collection (Dict): The collection containing the updated bounding boxes
    """

    if new_bbox_name not in bbox_collection:
        bbox_collection[new_bbox_name] = list()

    ulx, uly, box_width, box_height = None, None, None, None
    if not is_lobject:
        ulx, uly = new_bbox.bounding_poly.vertices[0].x, new_bbox.bounding_poly.vertices[0].y
        box_width = abs(
            new_bbox.bounding_poly.vertices[1].x - new_bbox.bounding_poly.vertices[0].x)
        box_height = abs(
            new_bbox.bounding_poly.vertices[3].y - new_bbox.bounding_poly.vertices[0].y)

    else:
        if (not img_width) or (not img_height):
            raise Exception("Image width/height cannot be empty")

        else:
            ulx, uly = new_bbox.bounding_poly.normalized_vertices[0].x * \
                img_width, new_bbox.bounding_poly.normalized_vertices[0].y * img_height
            box_width = (
                new_bbox.bounding_poly.normalized_vertices[1].x - new_bbox.bounding_poly.normalized_vertices[0].x) * img_width
            box_height = (
                new_bbox.bounding_poly.normalized_vertices[3].y - new_bbox.bounding_poly.normalized_vertices[0].y) * img_height

    if (ulx and uly and box_width and box_height) is not None:
        vert = [ulx, uly, box_width, box_height]
        bbox_collection[new_bbox_name].append(vert)

    return bbox_collection


def get_annotation(photo: IIIF_Photo, client: vision.ImageAnnotatorClient):
    """
    This function accepts the photo, the google vision client and
    returns the annotation provided by Google Vision API

    :param photo (IIIF_Photo): The photo for which the annotation is needed.
    :param client (vision.ImageAnnotatorClient): The client to call the Google Vision Annotation API
    :return result (Dict): The result of annotation as a dictionary
    """

    result = {}
    # reading the image
    image_data = ur.urlopen(photo.get_photo_link()).read()
    image = types.Image(content=image_data)

    # call the goole vision api to get the annotations of various types
    response = client.annotate_image({
        'image': image,
        'features': [{'type': vision.enums.Feature.Type.LANDMARK_DETECTION},
                     {'type': vision.enums.Feature.Type.LOGO_DETECTION},
                     {'type': vision.enums.Feature.Type.LABEL_DETECTION},
                     {'type': vision.enums.Feature.Type.TEXT_DETECTION},
                     {'type': vision.enums.Feature.Type.OBJECT_LOCALIZATION},
                     {'type': vision.enums.Feature.Type.WEB_DETECTION}], })

    success = False
    # check if there is any error returned by the api
    if response.error.code != 0:
        result["success"] = success
        result["error_code"] = response.error.code
        result["error_message"] = response.error.message
        return result

    else:
        success = True
        result["success"] = success

        # Initialising empty lists to store string tags
        result["lndmks"] = []
        result["logos"] = []
        result["objects"] = []
        result["text"] = []

        # get the list of labels
        labels = list()
        for lbl in response.label_annotations:
            labels.extend(clean_text(lbl.description))
        labels = list(set(labels))
        result["labels"] = labels

        # get the list of web entities
        webent = list()
        for weben in response.web_detection.web_entities:
            webent.extend(clean_text(weben.description))
        webent = list(set(webent))
        result["webent"] = webent

        # this dictionary will store the information of annotations along with bounding boxes.
        obj_boxes = {}
        # The key will the the name to identify the annotation and the value be a list of lists containing the top left x coordinate
        # top left y coordinate, width and height of for the bounding box.
        # It would be a list of list to store coordinates for different boxes for same tag

        # storing the landmarks
        # this dictionary will store the information of landmarks which are name, latitude, longitude.
        landmark_info = dict()
        for lndmk in response.landmark_annotations:
            # if there are any landamrks identified, we store them in a seperate field,to access easily.
            landmark_name = lndmk.description
            landmark_info[landmark_name] = {
                "latitude": lndmk.locations[0].lat_lng.latitude, "longitude": lndmk.locations[0].lat_lng.longitude}

            lndmks = clean_text(lndmk.description)
            result["lndmks"].extend(lndmks)

            # storing the landmarks with bounding boxes
            lndmk_desc = '_'.join(lndmks)
            obj_boxes = add_bbox(lndmk, lndmk_desc, obj_boxes)

        result["landmark_info"] = landmark_info

        # storing the logos
        for lgo in response.logo_annotations:

            logos = clean_text(lgo.description)
            result["logos"].extend(logos)

            lgo_desc = '_'.join(logos)
            obj_boxes = add_bbox(lgo, lgo_desc, obj_boxes)

        # storing the localised objects
        if len(response.localized_object_annotations) > 0:
            img_width, img_height = photo.iiif["width"], photo.iiif["height"]

            for lobj in response.localized_object_annotations:

                objects = clean_text(lobj.name)
                result["objects"].extend(objects)

                lobj_name = '_'.join(objects)
                obj_boxes = add_bbox(
                    lobj, lobj_name, obj_boxes, is_lobject=True, img_width=img_width, img_height=img_height)

        # storing the text
        for txt in response.text_annotations:
            modified_text = txt.description.replace(".", "_").lower()
            result["text"].extend(modified_text)

            # the text identified on the images in not cleaned to store the original information.
            obj_boxes = add_bbox(txt, modified_text, obj_boxes)

        result["obj_boxes"] = obj_boxes

        return result
