from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

images = ["cini"+ str(x) + "_d.png" for x in range(1,11)]


@app.route("/")
def home():
	return render_template("index.html", images=images)
if __name__ == "__main__":
	app.run()
