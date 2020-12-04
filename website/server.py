from search import *
from flask import Flask, redirect, url_for, render_template, request, jsonify, flash
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os
import json
from dotenv import load_dotenv
from DeOldify.imagecolorise import colorise_me
load_dotenv()


app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)
sample_annotations = mongo.db["terzani_annotations"]
sample_tags = mongo.db["terzani_taggings"]
sample_imageVectors = mongo.db["terzani_image_vecs"]

COLORISED_FOLDER = os.path.join('static', 'colorised_images')

ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])
app.config['UPLOAD_FOLDER'] = COLORISED_FOLDER

PAGE_SIZE = 21


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/colorised/<label>", methods=["GET"])
def colorised(label):
    return "<img style='display:block;width:100%;height:100%;object-fit:cover;'src = '/static/colorised_images/" + label + ".png'>"


@app.route("/colorise", methods=["POST"])
def colorise():
    link = request.form["link"]
    label = request.form["label"]
    colorise_me(link, label, 5)
    return label


@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    iiifs_and_links = []

    if request.method == "POST":
        display_markers = request.form.get("display_markers", False)
        landmark_name = request.form.get("landmark_name", "")
        if display_markers:
            results = get_markers(sample_annotations)
            lat_lng_name = [result["annotation"]["landmark_info"] for result in results]
            return jsonify({"lat_lng_name": lat_lng_name})
        elif len(landmark_name) > 0:
            results = get_markers(sample_annotations)
            iiifs_and_links = [(json.dumps(result["annotation"]["iiif"]), result["annotation"]["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/square/360,/0/default.jpg") for result in results if next(iter(result["annotation"]["landmark_info"])) == landmark_name]
            return jsonify({"data": render_template("display_images.html", country=landmark_name, iiifs_and_links=iiifs_and_links, page_size = PAGE_SIZE, page_number = 0)})
        else:
            page_number = int(request.form["page_number"])
            results, number_of_total_results = search_country(request.form["country"], sample_annotations, page_number, PAGE_SIZE)
            iiifs_and_links = [(json.dumps(result["annotation"]["iiif"]), result["annotation"]["iiif"]["images"]
                                [0]["resource"]["service"]["@id"][:-4] + "/square/360,/0/default.jpg") for result in results]
            return jsonify({"data": render_template("display_images.html", number_of_results = number_of_total_results, country=request.form["country"], iiifs_and_links=iiifs_and_links, page_size = PAGE_SIZE, page_number = page_number)})

    return render_template("gallery.html")


@app.route("/search", methods=["GET", "POST"])
def search_page():
    iiif_and_links = []
    number_of_results = 0
    page_number = 0
    display_bb = False
    item = ""
    if request.method == "POST":
        if request.form["submit"] == "text_search":
            page_number = int(request.form["page_number"])
            item = request.form["item"]
            display_bb = request.form.get("display_bb", False)
            photos, searched_items, number_of_results = search_photos(
                item, sample_tags, sample_annotations, page_number, PAGE_SIZE)

            if not display_bb:
                for res_photo in photos:
                    photo = res_photo["annotation"]
                    new_item = (json.dumps(photo["iiif"]), [
                                photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/square/360,/0/default.jpg"])
                    iiif_and_links.append(new_item)
            else:
                for res_photo in photos:
                    photo = res_photo["annotation"]
                    for sitem in searched_items:
                        box_key = next(
                            (key for key in photo["obj_boxes"] if sitem in key), None)
                        if box_key:
                            new_item = (json.dumps(photo["iiif"]), [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/" + str(
                                box[0]) + "," + str(box[1]) + "," + str(box[2]) + "," + str(box[3]) + "/360,360/0/default.jpg" for box in photo["obj_boxes"][box_key]])
                            iiif_and_links.append(new_item)
        elif request.form["submit"] == "image_search":

            if 'image_file' not in request.files:
                return redirect(request.url)
            else:
                image_file = request.files["image_file"]
                if image_file and allowed_file(image_file.filename):
                    similar_photos = search_similar_photos(image_file, sample_imageVectors, sample_annotations, count=20)
                    for res_photo in similar_photos:
                        photo = res_photo["annotation"]
                        new_item = (json.dumps(photo["iiif"]), [
                            photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/square/360,/0/default.jpg"])
                        number_of_results += len(new_item[1])
                        iiif_and_links.append(new_item)

    return render_template("search.html", results=iiif_and_links, number_of_results=number_of_results, display_bb=display_bb, item=item, cold_start=request.method == "GET", page_size = PAGE_SIZE, page_number = page_number)


if __name__ == "__main__":
    app.run(debug=True)