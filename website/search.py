from imageRetrieval import get_imagevector, get_similarity
import string
from itertools import chain, islice
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
nltk.download('punkt')


def clean_text(text: str, lower: bool = True, rmv_punc: bool = True, stem: bool = True, norm: bool = True):
    """
    This function accepts a string and performs preprocessing steps on it. 

    :param text (str): The string or text on which the preprocessing has to be performed.
    :param lower (bool): Default=True, indicates if the text has to be made into lower case.
    :param rmv_punc (bool): Default=True, indicates if the punctuation should be removed in the text.
    :param stem (bool): Default=True, indicates if the stemming should be performed on the words in the text.
    :param norm (bool): Default=True, indicates if the words in the has to be normalised.
    :return cleaned_text (list): The modified text is returned as list after performing the indicated operations.
    """

    # split into words
    tokens = word_tokenize(text)
    if lower:
        # convert to lower case
        tokens = [w.lower() for w in tokens]
    if rmv_punc:
        # remove punctuation from each word
        table = str.maketrans('', '', string.punctuation)
        tokens = [w.translate(table)
                  for w in tokens if w.translate(table) != '']
    if stem:
        # stemming of words
        porter = PorterStemmer()
        tokens = [porter.stem(word) for word in tokens]
    cleaned_text = sorted(list(set(tokens)), key=str.lower)
    return cleaned_text


def search_photos(item, tag_collection, annotation_collection):
    clean_query = clean_text(item)
    clean_query_ocr = clean_text(
        item, lower=True, rmv_punc=False, stem=False, norm=False)
    search_items = list(set(clean_query + clean_query_ocr))
    selected_photos = []
    for query in search_items:
        for query_photos in tag_collection.aggregate([
            {
                "$search": {
                    "regex": {
                        "query": "(.*)"+query+"(.*)",
                        "path": "tag",
                        "allowAnalyzedField": True,
                    }
                }
            },
            {
                "$project":
                    {"images": 1,
                     "_id": 0,
                     "score": {"$meta": "searchScore"},
                     }
            }
        ]
        ):
            selected_photos.extend([query_photos])
    sorted_selected_photos = sorted(
        selected_photos, key=lambda photo: photo["score"], reverse=True)
    photo_sorted = [res_dict['images']
                    for res_dict in sorted_selected_photos if 'images' in res_dict]
    photo_sorted_flat = list(chain.from_iterable(photo_sorted))
    photo_results = list(set(photo_sorted_flat))
    full_images = []
    for res_image in photo_results:
        image_iiif = list(annotation_collection.find({"label": res_image}))
        if image_iiif:
            full_images.append(image_iiif[0])
    return full_images, search_items


def search_country(country, collection):
    return list(collection.find({"annotation.country": country}))


def get_markers(collection):
    return list(collection.find({"annotation.landmark_info": {"$exists": True}}))


def search_similar_photos(image_file, vector_collection, annotation_collection, count=20):
    upimage_vec = get_imagevector(image_file)
    similarity = {}
    # This dictionary stores the image label as key and the similarity with the uploaded image as value.
    similarity = {dbimage["image"]: get_similarity(
        upimage_vec, dbimage["feature_vec"]) for dbimage in vector_collection.find()}
    # sort the images based on similarity
    sorted_similarity = dict(
        sorted(similarity.items(), key=lambda item: item[1], reverse=True))

    # get the number of images based on count requested
    selected_images = list(islice(sorted_similarity.keys(), count))
    full_images = []
    for res_image in selected_images:
        image_iiif = list(annotation_collection.find({"label": res_image}))
        if image_iiif:
            full_images.append(image_iiif[0])
    return full_images
