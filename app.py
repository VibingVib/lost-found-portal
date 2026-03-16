from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///lostfound.db"
app.config['UPLOAD_FOLDER'] = "static/uploads"

db = SQLAlchemy(app)


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))


class LostItem(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(200))
    desc = db.Column(db.String(500))
    image = db.Column(db.String(200))
    type = db.Column(db.String(20))
    owner = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/", methods=["GET","POST"])
def home():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        item = request.form["item"]
        desc = request.form["desc"]
        type = request.form["type"]

        image = request.files["image"]
        filename = image.filename

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        new_item = LostItem(
            item=item,
            desc=desc,
            image=filename,
            type=type,
            owner=session["user"]
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect("/")

    search = request.args.get("search")

    if search:
        lost_items = LostItem.query.filter(
            LostItem.item.contains(search),
            LostItem.type=="Lost"
        ).all()

        found_items = LostItem.query.filter(
            LostItem.item.contains(search),
            LostItem.type=="Found"
        ).all()

    else:

        lost_items = LostItem.query.filter_by(type="Lost").all()
        found_items = LostItem.query.filter_by(type="Found").all()

    return render_template(
        "index.html",
        lost_items=lost_items,
        found_items=found_items
    )


@app.route("/contact/<int:id>")
def contact(id):

    item = LostItem.query.get_or_404(id)

    return f"Contact owner: {item.owner}"


@app.route("/myitems")
def myitems():

    if "user" not in session:
        return redirect("/login")

    items = LostItem.query.filter_by(owner=session["user"]).all()

    return render_template("myitems.html", items=items)


@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User(username=username, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user"] = username
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


@app.route("/delete/<int:id>")
def delete(id):

    item = LostItem.query.get_or_404(id)

    db.session.delete(item)
    db.session.commit()

    return redirect("/")


@app.route("/update/<int:id>", methods=["GET","POST"])
def update(id):

    item = LostItem.query.get_or_404(id)

    if request.method == "POST":

        item.item = request.form["item"]
        item.desc = request.form["desc"]

        db.session.commit()

        return redirect("/")

    return render_template("update.html", item=item)


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)