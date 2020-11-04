from flask import Flask, redirect, url_for, render_template, request
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

images = ["cini"+ str(x) + "_d.png" for x in range(1,11)]


@app.route("/")
def home():
	return render_template("home.html")

@app.route("/gallery")
def gallery():
	return render_template("gallery.html", images=images)


@app.route("/search", methods=["GET", "POST"])
def search_page():
	iiif_and_links = []
	number_of_boxes = 0
	display_full = False
	item = ""
	if request.method == "POST":
		item = request.form["item"]
		photos = search_item_in_database(item, sample_annotations)
		display_full = request.form.get("display_full", False)
		for photo in photos:
			if display_full:
				new_item = (json.dumps(photo["iiif"]), [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/full/max/0/default.jpg"])
			else:
				new_item = (json.dumps(photo["iiif"]), [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/" + str (box[0]) + "," + str (box[1]) + "," +str (box[2]) + "," + str (box[3]) + "/max/0/default.jpg" for box in photo["obj_boxes"][request.form["item"]]])
			number_of_boxes += len(new_item[1])
			iiif_and_links.append(new_item)
			
	return render_template("search.html", results = iiif_and_links, number_of_boxes=number_of_boxes, display_full = display_full, item=item)


if __name__ == "__main__":
	app.run(debug=True)
