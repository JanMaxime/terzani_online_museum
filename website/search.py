from imageRetrieval import get_imagevector, get_similarity
from terzani.utils.clean_text import clean_text
from itertools import chain, islice


def search_photos(item, tag_collection, annotation_collection, page_number, page_size, min_len=3, exact_match=False):

    if not exact_match:
        clean_query = clean_text(item)
    else:
        clean_query = clean_text(item, stem=False)
    clean_query_ocr = clean_text(
        item, lower=True, rmv_punc=False, stem=False)
    search_items = list(set(clean_query + clean_query_ocr))
    selected_photos = []
    for query in search_items:
        if len(query) >= min_len:
            if not exact_match:
                search_query = "(.*)"+query+"(.*)"
            else:
                search_query = query
            for query_photos in tag_collection.aggregate([
                {
                    "$search": {
                        "regex": {
                            "query": search_query,
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
                },
            ]
            ):
                selected_photos.extend([query_photos])
    sorted_selected_photos = sorted(
        selected_photos, key=lambda photo: photo["score"], reverse=True)
    photo_sorted = [res_dict['images']
                    for res_dict in sorted_selected_photos if 'images' in res_dict]
    photo_sorted_flat = list(chain.from_iterable(photo_sorted))
    photo_results = list(set(photo_sorted_flat))
    n_total_results = len(photo_results)
    photo_results = photo_results[page_number *
                                  page_size: page_number * page_size + page_size]
    full_images = list()
    for res_image in photo_results:
        image_iiif = list(annotation_collection.find({"label": res_image}))
        if image_iiif:
            full_images.append(image_iiif[0])
    return full_images, search_items, n_total_results


def search_country(country, collection, page_number, page_size):
    return list(collection.find({"annotation.country": country}).skip(page_number * page_size).limit(page_size)), collection.count({"annotation.country": country})


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
