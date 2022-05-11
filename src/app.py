import os
import boto3
from dotenv import load_dotenv
from flask import Flask, flash, render_template, redirect, request, url_for, session, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from string import ascii_lowercase, ascii_uppercase
from uuid import uuid4
from secrets import token_hex

load_dotenv()
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "files")
ALLOWED_SHEET_TYPES = {"pdf"}
ALLOWED_SOUND_TYPES = {"wav"}

app = Flask(__name__, static_folder="./static")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY")

def prepend_id(filename):
    prefix = uuid4().__str__()
    return prefix + "_" + filename

def allowed_sheet(filename):
    return '.' in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_SHEET_TYPES

def allowed_sound(filename):
    return '.' in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_SOUND_TYPES

def upload_to_aws_s3(file, name):
    client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET")
    client.upload_fileobj(file, bucket, name)

def download_from_aws_s3(filename, file_path):
    try:
        client = boto3.client("s3")
        bucket = os.getenv("S3_BUCKET")
        client.download_file(bucket, filename, file_path)
        return file_path
    except Exception as e:
        print(f"Error at download:  {e}", "error")
        print(f"Tried to load {filename} to {file_path}")

def delete_from_aws_s3(filename):
    client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET")
    client.delete_object(Bucket=bucket, Key=filename)

@app.route("/")
def index():
    if "csrf_token" not in session and "username" in session:
        del session["username"]
        return redirect("/")
    sql = "SELECT c.id as id, c.title AS title, \
            c.composer AS composer, c.views AS views, \
            c.genre AS genre, c.notation AS notation, \
            AVG(d.difficulty) AS difficulty, \
            AVG(r.rating) AS rating \
            FROM compositions c, ratings r, \
            difficultyratings d \
            WHERE r.song_id=c.id AND d.song_id=c.id \
            GROUP BY c.id"
    result = db.session.execute(sql)
    compositions = result.fetchall()
    return render_template("index.html", count=len(compositions), compositions=compositions)

@app.route("/composition/<int:id>", methods=["GET"])
def view_music(id):
    sql = "UPDATE compositions SET views = views + 1 WHERE id=(:id)"
    db.session.execute(sql, {"id":id})
    db.session.commit()
    sql = "SELECT c.id AS id, c.title AS title, c.composer AS composer, \
        c.views as views, c.genre AS genre, c.notation AS notation, \
        AVG(r.rating) AS rating, AVG(d.difficulty) AS difficulty, \
        u.username as uploader, c.filename as filename FROM \
        compositions c, ratings r, difficultyratings d, users u \
        WHERE r.song_id=c.id AND d.song_id=c.id AND c.user_id=u.id \
        AND t.song_id=c.id AND c.id=(:id) GROUP BY c.id, u.id"
    result = db.session.execute(sql, {"id":id})
    music = result.fetchone()
    sql = "SELECT tag FROM tags WHERE song_id=:id"
    result = db.session.execute(sql, {"id":id})
    tags = result.fetchall()    
    sql = "SELECT n.note AS note, u.username AS uploader \
        FROM notes n, users u WHERE n.user_id=u.id \
        AND n.song_id=:id GROUP BY n.note, u.username"
    result = db.session.execute(sql, {"id":id})
    notes = result.fetchall()
    upload_folder = app.config["UPLOAD_FOLDER"]
    return render_template("view.html", music=music, notes=notes, tags=tags, upload_folder=upload_folder)

@app.route(app.config['UPLOAD_FOLDER'] + "/<filename>", methods=["GET"])
def get_pdf(filename):
    sql = "SELECT id FROM compositions WHERE filename=(:filename)"
    result = db.session.execute(sql, {"filename":filename})
    music = result.fetchone()
    if music:
        file_path = app.config['UPLOAD_FOLDER'] + "/" + filename
        file = download_from_aws_s3(filename, file_path)
        return send_file(file)
    else:
        flash(f"Music {filename} not found", "error")
        return redirect("/")

@app.route("/delete/<filename>")
def delete_file(filename):
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    sql = "DELETE FROM compositions WHERE filename=(:filename)"
    db.session.execute(sql, {"filename":filename})
    db.session.commit()
    delete_from_aws_s3(filename)
    return redirect("/")

@app.route("/notes/<id>", methods=["POST"])
def add_notes(id):
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    tags = []
    for word in request.form["notes"].split():
        if word[0] == '#':
            tags.append(word[1:])
    username = session["username"]
    id_fetch = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username})
    user_id = id_fetch.fetchone()[0]
    sql = "INSERT INTO tags (song_id, tag, user_id) VALUES (:song_id, :tag, :user_id)"
    for tag in tags:
        db.session.execute(sql, {"song_id": id, "tag": tag, "user_id": user_id})
    stripped_notes = request.form["notes"].replace("#", "")
    sql = "INSERT INTO notes (song_id, note, user_id) VALUES (:song_id, :note, :user_id)"
    db.session.execute(sql, {"song_id": id, "note": stripped_notes, "user_id": user_id})
    db.session.commit()
    return redirect("/composition/" + id)

@app.route("/guide")
def guide():
    return "Placeholder for user guide"

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route("/uploader", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        if "file" not in request.files:
            flash("No file submitted", "error")
            return redirect("/upload")
        file = request.files["file"]
        if file and allowed_sheet(file.filename):
            filename = secure_filename(prepend_id(file.filename))
            upload_to_aws_s3(file, filename)
            username = session["username"]
            id_fetch = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username})
            user_id = id_fetch.fetchone()[0]
            title = request.form["title"]
            composer = request.form["composer"]
            instrument_count = int(request.form["instrumentcount"])
            notation = request.form["notation"]
            genre = request.form["genre"]
            rating = int(request.form["rating"])
            difficulty = int(request.form["difficulty"])
            sql = "INSERT INTO compositions \
                (title, filename, composer, \
                instrumentcount, views, \
                notation, genre, user_id) VALUES \
                (:title, :filename, :composer, \
                :instrumentcount, :views, \
                :notation, :genre, :user_id)"
            db.session.execute(sql, {"title":title,
            "filename":filename, "composer":composer,
            "instrumentcount":instrument_count, "views":0,
            "notation":notation, "genre":genre, "user_id":user_id})
            sql = "INSERT INTO ratings (song_id, rating, user_id) \
                VALUES (lastval(), :rating, :user_id)"
            db.session.execute(sql, {"rating":rating, "user_id":user_id})
            sql = "INSERT INTO difficultyratings (song_id, difficulty, user_id) \
                VALUES (lastval(), :difficulty, :user_id)"
            db.session.execute(sql, {"difficulty":difficulty, "user_id":user_id})
            db.session.commit()
            flash("File uploaded succesfully")
            return redirect("/")
        else:
            flash("Unsupported filetype", "error")
            return redirect("/upload")

@app.route("/search", methods=["POST"])
def search():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    sql = "SELECT c.id as id, c.title AS title, \
            c.composer AS composer, c.views AS views, \
            c.genre AS genre, c.notation AS notation, \
            AVG(d.difficulty) AS difficulty, \
            AVG(r.rating) AS rating \
            FROM compositions c, ratings r, \
            difficultyratings d \
            WHERE r.song_id=c.id AND d.song_id=c.id "
    name = request.form["name"]
    composer = request.form["composer"]
    tags = request.form["tags"]
    min_difficulty = request.form["min-difficulty"]
    max_difficulty = request.form["max-difficulty"]
    min_rating = request.form["min-rating"]
    max_rating = request.form["max-rating"]
    if name:
        name = "%" + "%".join(name.split()) + "%"
        sql += "AND LOWER(c.title) LIKE LOWER(:name) "
    if composer:
        composer = "%" + "%".join(composer.split()) + "%"
        sql += "AND LOWER(c.composer) LIKE LOWER(:composer) "
    if tags:
        tags = "%" + "%".join(tags.split()) + "%"
        sql += "AND LOWER(c.tags) LIKE LOWER(:tags) "
    if min_difficulty:
        sql += "AND difficulty >= :min_difficulty "
    if max_difficulty:
        sql += "AND difficulty <= :max_difficulty "
    if min_rating:
        sql += "AND rating >= :min_rating "
    if max_rating:
        sql += "AND rating <= :max_rating "
    sql += "GROUP BY c.id"
    result = db.session.execute(sql, {"name": name, "composer": composer,
    "tags": tags, "min_rating": min_rating, "max_rating": max_rating,
    "min_difficulty": min_difficulty, "max_difficulty": max_difficulty})
    compositions = result.fetchall()
    return render_template("index.html", count=len(compositions), compositions=compositions)

@app.route("/rate/", methods=["POST"])
def rate():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    username = session["username"]
    id_fetch = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username})
    user_id = id_fetch.fetchone()[0]
    sql = "DELETE FROM ratings WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()
    sql = "INSERT INTO ratings (song_id, rating, user_id) VALUES (:song_id, :rating, :user_id)"
    db.session.execute(sql, {"song_id": request.form["song_id"], "rating": int(request.form["rating"]), "user_id": user_id})
    db.session.commit()
    return redirect("/composition/" + request.form["song_id"])

@app.route("/rate_difficulty/", methods=["POST"])
def rate_difficulty():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    username = session["username"]
    id_fetch = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username})
    user_id = id_fetch.fetchone()[0]
    sql = "DELETE FROM difficultyratings WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()
    sql = "INSERT INTO difficultyratings (song_id, difficulty, user_id) VALUES (:song_id, :difficulty, :user_id)"
    db.session.execute(sql, {"song_id": request.form["song_id"], "difficulty": int(request.form["difficulty"]), "user_id": user_id})
    db.session.commit()
    return redirect("/composition/" + request.form["song_id"])

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT username, password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if not user:
        flash("Invalid username or password", "error")
        return redirect("/")
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
            session["username"] = user["username"]
            session["csrf_token"] = token_hex(16)
            return redirect("/")
        else:
            flash("Invalid username or password", "error")
            return redirect("/")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/signuper", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]
    if len(username) < 3:
        flash("Username too short. Please use at least 3 characters", "error")
        return redirect("signup")
    rules = {"!#$%&()*+,-./:;<=>?@[\]^_`{|}~": False, ascii_uppercase: False, ascii_lowercase: False}
    for letter in str(password):
        for charlist in rules.keys():
            if letter in charlist:
                rules[charlist] = True
    for compliance in rules.values():
        if not compliance:
            flash("Please use at least 8 characters and at least one number, \
                at least one of both upper/lower case character and one special \
                character from !#$%&()*+,-./:;<=>?@[\]^_`{|}~ in the password.", "error")
            return redirect("/signup")
    password_repeat = request.form["password_repeat"]
    if password != password_repeat:
        flash("Passwords do not match")
        return redirect("/signup")
    hash_value = generate_password_hash(password)
    sql = "SELECT id FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    existing_user = result.fetchone()
    if not existing_user:
        sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
        db.session.execute(sql, {"username":username, "password":hash_value})
        db.session.commit()
        sql = "SELECT username FROM users WHERE username=:username"
        result = db.session.execute(sql, {"username":username})
        flash("Signup succesful")
        session["username"] = username
        session["csrf_token"] = token_hex(16)
        return redirect("/")
    else:
        flash("Username taken.", "error")
        return redirect("/signup")

@app.route("/logout", methods=["POST"])
def logout():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    del session["username"]
    return redirect("/")
