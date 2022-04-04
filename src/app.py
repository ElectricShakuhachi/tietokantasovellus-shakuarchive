import os
from dotenv import load_dotenv
from flask import Flask, flash, render_template, redirect, request, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
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

def allowed_shoud(filename):
    return '.' in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_SOUND_TYPES

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
        return send_file(file_path)

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
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file and allowed_sheet(file.filename):
            filename = secure_filename(prepend_id(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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
                :instrumentcount, 0, :notation)"
            db.session.execute(sql, {"title":title,
            "filename":filename, "difficulty":difficulty,
            "composer":composer, "genre":genre,
            "uploader":uploader, "instrumentcount":instrument_count,
            "notation":notation})
            db.session.commit()
            flash("File uploaded succesfully")
            return redirect("/")
        else:
            print("Should be flashing...")
            flash("Unsupported filetype")
            return redirect("/upload")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        flash("Invalid username or password")
        return redirect("/")
    else:
        hash_value = user.password
        if check_password_hash(hash_value, password):
            session["username"] = username
            return redirect("/")
        else:
            flash("Invalid username or password")
            return redirect("/")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/signuper", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
    db.session.execute(sql, {"username":username, "password":hash_value})
    db.session.commit()
    return "Singup succesful"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")