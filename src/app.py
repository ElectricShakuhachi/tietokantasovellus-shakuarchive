import os
import boto3
import botocore
from dotenv import load_dotenv
from flask import Flask, flash, render_template, redirect, request, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from string import ascii_lowercase, ascii_uppercase
from uuid import uuid4

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
        return send_file(filename)
    except botocore.exceptions.Clienterror as error:
        print(error.response["Error"]["Code"])
        print(error.response["Error"]["Message"])

@app.route("/")
def index():
    result = db.session.execute("SELECT id, title FROM compositions")
    compositions = result.fetchall()
    return render_template("index.html", count=len(compositions), compositions=compositions)

@app.route("/composition/<int:id>", methods=["GET"])
def view_music(id):
    sql = "UPDATE compositions SET views = views + 1 WHERE id=(:id)"
    db.session.execute(sql, {"id":id})
    db.session.commit()
    sql = "SELECT * FROM compositions WHERE id=(:id)"
    result = db.session.execute(sql, {"id":id})
    music = result.fetchone()
    upload_folder = app.config["UPLOAD_FOLDER"]
    return render_template("view.html", music=music, upload_folder=upload_folder)

@app.route(app.config['UPLOAD_FOLDER'] + "/<filename>", methods=["GET"])
def get_pdf(filename):
    sql = "SELECT id FROM compositions WHERE filename=(:filename)"
    result = db.session.execute(sql, {"filename":filename})
    music = result.fetchone()
    if music:
        file_path = app.config['UPLOAD_FOLDER'] + "/" + filename
        file = download_from_aws_s3(filename, file_path)
        return send_file(file)

@app.route("/delete/<filename>")
def delete_file(filename):
    sql = "DELETE FROM compositions WHERE filename=(:filename)"
    db.session.execute(sql, {"filename":filename})
    db.session.commit()
    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return redirect("/")

@app.route("/guide")
def guide():
    return "Placeholder for user guide"

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route("/uploader", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file submitted", "error")
            return redirect(request.url)
        file = request.files["file"]
        if file and allowed_sheet(file.filename):
            filename = secure_filename(prepend_id(file.filename))
            upload_to_aws_s3(file, filename)
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploader = session["username"]
            title = request.form["title"]
            composer = request.form["composer"]
            difficulty = request.form["difficulty"]
            genre = request.form["genre"]
            instrument_count = request.form["instrumentcount"]
            notation = request.form["notation"]
            sql = "INSERT INTO compositions \
                (title, filename, difficulty, \
                composer, genre, uploader, \
                instrumentcount, views, notation) VALUES \
                (:title, :filename, :difficulty, \
                :composer, :genre, :uploader, \
                :instrumentcount, :views, :notation)"
            db.session.execute(sql, {"title":title,
            "filename":filename, "difficulty":difficulty,
            "composer":composer, "genre":genre,
            "uploader":uploader, "instrumentcount":instrument_count,
            "notation":notation, "views":0})
            db.session.commit()
            flash("File uploaded succesfully")
            return redirect("/")
        else:
            flash("Unsupported filetype", "error")
            return redirect("/upload")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if not user:
        flash("Invalid username or password", "error")
        return redirect("/")
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
            session["username"] = username
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
        flash("Singup succesful")
        session["username"] = username
        return redirect("/")
    else:
        flash("Username taken.", "error")
        return redirect("/signup")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")