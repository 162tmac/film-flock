import os
from flask import (Flask, flash, render_template,
                   request, redirect, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env
from werkzeug.security import generate_password_hash, check_password_hash
from elasticsearch import Elasticsearch

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")
app.config.update(TEMPLATES_AUTO_RELOAD=True)

mongo = PyMongo(app)

elastic_client = Elasticsearch()


@app.route("/")
def index():
    if "user" in session:
        return redirect("dashboard")
    else:
        return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        user_email = session.get('user')
        user = mongo.db.users.find_one(
            {"email": user_email}
        )
        flock = {
            "creator_id": user["_id"],
            "name": request.form.get("name"),
            "films": [ObjectId("573a1390f29313caabcd4eaf")]
        }
        _id = mongo.db.flocks.insert_one(flock)
        return redirect(url_for('flocks', id=_id.inserted_id))
    return render_template("create.html")


@app.route("/dashboard")
def dashboard():
    user_email = session.get('user')
    user = mongo.db.users.find_one(
        {"email": user_email}
    )
    my_films = mongo.db.flocks.find(
        {"creator_id": user["_id"]}
    )
    return render_template("dashboard.html", films=my_films)


@app.route("/flocks/<id>")
def flocks(id):
    flock = mongo.db.flocks.aggregate([
        {
            "$match": {"_id": ObjectId(id)}
        },
        {
            "$lookup":
                {
                    "from": "movies",
                    "localField": "films",
                    "foreignField": "_id",
                    "as": "films"
                }
        },
    ])
    return render_template("flock_view.html.j2", flock=list(flock))


@ app.route("/discover")
def discover():
    return render_template("discover.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/films")
def films():
    films = mongo.db.movies.find()
    return render_template("films.html", films=films)


@app.route("/films/<id>")
def film_view(id):
    film = mongo.db.movies.find_one({"_id": ObjectId(id)})
    return render_template("film_view.html.j2", film=film)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email")}
        )

        if existing_user:
            if check_password_hash(existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("email")
                flash("Welcome, {}".format(existing_user["first_name"]))
                return redirect(url_for("index", email=session["user"]))
            else:
                flash("Incorrect Email and/or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Email and/or Password")
            return redirect(url_for("login"))
    return render_template('login.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email")}
        )

        if existing_user:
            flash("Email already exists")
            return redirect(url_for("register"))

        if request.form.get("password") != request.form.get("password_confirmation"):
            flash("Error: Password confirmation does not match!")
            return redirect(url_for("register"))

        register = {
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "email": request.form.get("email"),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        session["user"] = request.form.get("email")
        flash("Registration successful!")
    return render_template("register.html")


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=os.environ.get("PORT"),
            debug=True)
