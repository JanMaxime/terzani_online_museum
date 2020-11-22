from flask import Flask, redirect, url_for, render_template, request, jsonify
from flask_pymongo import PyMongo
import os
import json
from dotenv import load_dotenv
load_dotenv()

from search import *

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)
sample_annotations = mongo.db["sample_annotations"]


@app.route("/")
def home():
	return render_template("home.html")

@app.route("/gallery", methods=["GET", "POST"])
def gallery():
	iiifs_and_links = []
	if request.method == "POST":
		display_markers = request.form.get("display_markers", False)
		if display_markers:
			results = get_markers(sample_annotations)
			iiif_lat_lng_name = [(result["annotation"]["iiif"], result["annotation"]["landmark_info"]) for result in results]
			print(iiif_lat_lng_name)
			return jsonify({"iiif_lat_lng_name" : iiif_lat_lng_name})
		else:
			results = search_country(request.form["country"], sample_annotations)
			iiifs_and_links = [(result["annotation"]["iiif"], result["annotation"]["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/full/,1080/0/default.jpg") for result in results]
			return jsonify({"data" : render_template("display_images.html", iiifs_and_links=iiifs_and_links)})

	return render_template("gallery.html")


@app.route("/search", methods=["GET", "POST"])
def search_page():
	iiif_and_links = []
	number_of_results = 0
	display_bb = False
	item = ""
	if request.method == "POST":
		item = request.form["item"]
		display_bb = request.form.get("display_bb", False)

		if not display_bb:
			photos = search_bb_and_tags(item, sample_annotations)
			for photo in photos:
				new_item = (json.dumps(photo["iiif"]), [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/full/,1080/0/default.jpg"])
				number_of_results += len(new_item[1])
				iiif_and_links.append(new_item)
		else:
			photos = search_bb(item, sample_annotations)
			for photo in photos:
				new_item = (json.dumps(photo["iiif"]), [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/" + str (box[0]) + "," + str (box[1]) + "," +str (box[2]) + "," + str (box[3]) + "/max/0/default.jpg" for box in photo["obj_boxes"][request.form["item"]]])
				number_of_results += len(new_item[1])
				iiif_and_links.append(new_item)
		
	return render_template("search.html", results = iiif_and_links, number_of_results=number_of_results, display_bb = display_bb, item=item, cold_start = request.method == "GET")


if __name__ == "__main__":
	app.run(debug=True)
