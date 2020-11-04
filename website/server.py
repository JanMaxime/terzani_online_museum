from flask import Flask, redirect, url_for, render_template, request
from flask_pymongo import PyMongo
import os

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
	x  = test_data.insert_one({"Name" : "Maxime", "age" : 23})
	return render_template("home.html")

@app.route("/gallery")
def gallery():
	return render_template("gallery.html", images=images)


@app.route("/search", methods=["GET", "POST"])
def search_page():
	iiif_and_link = []
	if request.method == "POST":
		photos = search_item_in_database(request.form["item"], sample_annotations)
		for photo in photos:
			iiif_and_link.append((photo["iiif"], [photo["iiif"]["images"][0]["resource"]["service"]["@id"][:-4] + "/" + str (box[0]) + "," + str (box[1]) + "," +str (box[2]) + "," + str (box[3]) + "/max/0/default.jpg" for box in photo["obj_boxes"][request.form["item"]]]  ))
			
	return render_template("search.html", results = iiif_and_link)


if __name__ == "__main__":
	app.run(debug=True)
