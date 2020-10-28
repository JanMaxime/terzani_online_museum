from flask import Flask, redirect, url_for, render_template, request
from flask_pymongo import PyMongo

from search import *

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://terzani:terzanidb@terzani.4wrdm.mongodb.net/terzani_photos?retryWrites=true&w=majority"
mongo = PyMongo(app)

test_data = mongo.db["test_data"]
print(mongo.db)
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
	if request.method == "POST":
		anno = search_database(request.form["item"])
		display_full = request.form.get("display_full", False)
		link = ""
		if anno != None:
			upper_left_vertex = anno["bounding_poly"]["normalized_vertices"][0]
			lower_right_vertex = anno["bounding_poly"]["normalized_vertices"][2]


			x1 = upper_left_vertex["x"] * 1943
			y1 = upper_left_vertex["y"] * 1458

			x2 = lower_right_vertex["x"] * 1943
			y2 = lower_right_vertex["y"] * 1458

			width = x2-x1
			height = y2-y1

			
			if(display_full):
				link = "http://dl.cini.it:8080/digilib/Scaler/IIIF/cb46e00d902f9936224ca6ef81834a35/full/max/0/default.jpg"
			else:
				link = f"http://dl.cini.it:8080/digilib/Scaler/IIIF/cb46e00d902f9936224ca6ef81834a35/{x1},{y1},{width},{height}/max/0/default.jpg"


		return render_template("search.html", result=link, not_found = False, full_default = display_full, default_item=request.form["item"])
	else:
		return render_template("search.html", result=None, not_found = False, full_default = False)


if __name__ == "__main__":
	app.run(debug=True)
