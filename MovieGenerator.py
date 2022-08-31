# My movie generating project
from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    logout_user,
    current_user,
)
from flask_wtf import FlaskForm
from sqlalchemy import true
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectMultipleField,
    widgets,
    SelectField,
    RadioField,
)
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import json, requests, random

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "thisisasecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

global_user_id = None
key = "insert key here"

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# User Class For Database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


# Movies the User has already seen
class SeenMovies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movieid = db.Column(db.String(100), nullable=False)


# Form For Registration
class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )

    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )

    submit = SubmitField("Register")

    # ensures valid username
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one."
            )


# Form for Login
class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )

    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )

    submit = SubmitField("Login")


# Multiple Input Field
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# Form for checkBoxes
class MovieForm(FlaskForm):
    genre_url = (
        "https://api.themoviedb.org/3/genre/movie/list?api_key="
        + key
        + "&language=en-US"
    )

    response = requests.get(genre_url)
    stuff = json.loads(response.text)

    genres = [(str(x["id"]), x["name"]) for x in stuff["genres"]]

    example = MultiCheckboxField("Label", choices=genres)


# Form for SeenMovie
class SeenCheckbox(FlaskForm):
    example = SelectField(choices=[("1", "Check if you have seen this movie before")])


# Home page
@app.route("/")
def home():
    return render_template("home.html")


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                global_user_id = str(user.id)
                return redirect(url_for("dashboard"))
    return render_template("login.html", form=form)


# Dashboard Page
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")


# Logout page
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


# Random Movie Method With no Specifications
def random_Movie():
    a = False
    url = None

    while a == False:
        random_page = str(random.randint(1, 500))
        disc = (
            "https://api.themoviedb.org/3/discover/movie?api_key="
            + key
            + "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page="
            + random_page
            + "&with_watch_monetization_types=flatrate"
        )
        responseD = requests.get(disc)
        stuff = json.loads(responseD.text)

        print(stuff["results"])
        if len(stuff["results"]) < 1:
            return "<h1> No results </h1>"

        random_discovery_result = random.choice(stuff["results"])
        url = (
            "https://api.themoviedb.org/3/movie/"
            + str(random_discovery_result["id"])
            + "?api_key="
            + key
        )
        a = True
        # alreadySeen = SeenMovies.query.filter(
        #    db.SeenMovies.id == global_user_id,
        #    db.SeenMovies.movieid == random_discovery_result.id,
        # ).first()

    responseU = requests.get(url)
    stuff = json.loads(responseU.text)
    return stuff


# Random Movie Method with a one or more genres
def randomMovieWithGenre(genre):
    a = False
    url = None

    while a == False:

        disc = (
            "https://api.themoviedb.org/3/discover/movie?api_key="
            + key
            + "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1"
            + "&with_watch_monetization_types=flatrate"
            + "&with_genres="
            + genre
        )

        responseD = requests.get(disc)
        stuff = json.loads(responseD.text)

        if stuff["total_results"] == 0:
            return "<h1> No results </h1>"

        max_page_results = stuff["total_pages"]

        if max_page_results > 500:
            max_page = 500
        else:
            max_page = max_page_results

        random_page = str(random.randint(1, max_page))

        disc = (
            "https://api.themoviedb.org/3/discover/movie?api_key="
            + key
            + "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page="
            + random_page
            + "&with_watch_monetization_types=flatrate"
            + "&with_genres="
            + genre
        )

        responseD = requests.get(disc)
        stuff = json.loads(responseD.text)

        random_discovery_result = random.choice(stuff["results"])
        url = (
            "https://api.themoviedb.org/3/movie/"
            + str(random_discovery_result["id"])
            + "?api_key="
            + key
        )
        a = True
        # alreadySeen = SeenMovies.query.filter(
        #    db.SeenMovies.id == global_user_id,
        #    db.SeenMovies.movieid == random_discovery_result.id,
        # ).first()

    responseU = requests.get(url)
    stuff = json.loads(responseU.text)
    return stuff


# adds movie to seen list
def add_seen_movie(movId):
    seenMovie = SeenMovies(id=global_user_id, movieid=movId)


# checks to see if the movie was seen by the user
def check_if_seen(movId):
    return SeenMovies.query.filter(
        db.SeenMovies.id == global_user_id,
        db.SeenMovies.movieid == movId.id,
    ).first()


# Random Movie page
@app.route("/randomMovie", methods=["GET", "POST"])
@login_required
def randomMovie():
    form = MovieForm()
    if form.validate_on_submit():
        genre_data = form.example.data
        genres = ",".join(genre_data)

        movie = randomMovieWithGenre(genres)
        form = SeenCheckbox()

        print(movie["id"])

        if form.validate_on_submit:
            print("hi")
            add_seen_movie(movie["id"])

    else:
        print("Validation Failed")
        print(form.errors)
    return render_template("random.html", form=form)


# Random Genre page
@app.route("/randomGenre", methods=["GET", "POST"])
@login_required
def randomGenre():
    genre_url = (
        "https://api.themoviedb.org/3/genre/movie/list?api_key="
        + key
        + "&language=en-US"
    )

    response = requests.get(genre_url)
    stuff = json.loads(response.text)
    genre = random.choice(stuff["genres"])

    url = (
        "https://api.themoviedb.org/3/discover/movie?api_key="
        + key
        + "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1"
        + "&with_watch_monetization_types=flatrate"
        + "&with_genres="
        + str(genre["id"])
    )

    return "<h1>" + genre["name"] + "</h1>"


if __name__ == "__main__":
    app.run(debug=True)
