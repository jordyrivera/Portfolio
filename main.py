import base64
from datetime import datetime

import werkzeug.security
from flask import Flask, render_template, redirect, request, session, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from Account import Account
from flask_session import Session

app = Flask(__name__)
post_id = 0

# SESSION
app.config.from_object(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# DATABASE
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

# INITIATE DB
db.init_app(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    lastName = db.Column(db.String, unique=False, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    likes = db.Column(db.Integer, default=0)
    post_content = db.Column(db.String)
    owner_name = db.Column(db.String)


class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    post_liker = db.Column(db.String)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    comment = db.Column(db.String)
    commented_by = db.Column(db.String)


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    if not session.get("name"):
        return render_template("index.html")
    else:
        users_db = db.session.execute(db.select(User)).scalars()
        users = [user.username for user in users_db]
        all_post = db.session.execute(db.select(Post).order_by(desc(Post.id))).scalars()
        likes = db.session.execute(db.select(Likes).filter_by(post_liker=session['name'])).scalars()
        l_like = [like.post_id for like in likes]
        return render_template("homepage.html", session=session, all_post=all_post, users=users, likes=likes,
                               l_like=l_like)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        new_user = Account(request.form["Name"],
                           request.form["LastName"],
                           request.form["Username"],
                           request.form["Password"],
                           request.form["Email"])

        dbuser = db.session.execute(db.select(User).filter_by(username=new_user.username)).scalar()

        # validate user inputs
        if new_user.validate_empty_inputs():
            return render_template("register.html", msg="All the fields are required, please fill all of them")

        if not new_user.validate_email():
            return render_template("register.html", msg="The email you have provided is not a valid email")

        try:
            if new_user.username == dbuser.username:
                return render_template("register.html", msg="Username is already taken. Please use another username.")

        except AttributeError:
            user = User(
                name=new_user.first_name,
                lastName=new_user.last_name,
                username=new_user.username,
                email=new_user.email,
                password=new_user.password_hash()
            )
            db.session.add(user)
            db.session.commit()
        return redirect("/")
    return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        query_account = db.session.execute(db.select(User).filter_by(username=request.form["username"])).scalar()
        print(query_account)
        try:
            if query_account.username == request.form["username"] and werkzeug.security.check_password_hash(
                    query_account.password, request.form["password"]):
                session['name'] = query_account.username
                print(session["name"])
                return redirect("/")
            else:
                return render_template("index.html", msg="Wrong Username or Password")
        except Exception:
            return Exception
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        try:
            search_user = db.session.execute(db.select(User).filter_by(username=request.form["search"])).scalar()
            all_post = db.session.execute(db.select(Post).filter_by(owner_name=request.form["search"])).scalars()
            if search_user.username == request.form["search"]:
                return render_template("profile.html", user=search_user, all_post=all_post)
        except AttributeError:
            return redirect("/")
    return render_template("homepage.html")


@app.route("/homepage", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        if request.form["new_post"] == "":
            return "", 204
        post = Post(
            post_content=request.form["new_post"],
            owner_name=session["name"]
        )
        db.session.add(post)
        db.session.commit()
        return redirect("/")
    return redirect("/")


@app.route("/delete/<int:id>")
def delete_post(id):
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    return redirect("/")


@app.route("/like_post/<int:id>")
def like_post(id):
    check_db = db.session.execute(db.select(Likes).filter_by(post_id=id, post_liker=session['name'])).scalar()
    get_post = db.session.execute(db.select(Post).filter_by(id=id)).scalar()
    if check_db == None:
        new_like = Likes(
            post_id=id,
            post_liker=session["name"]
        )
        get_post.likes += 1
        db.session.add(new_like)
        db.session.commit()
        print("liked added")
        return "", 204
    else:
        db.session.delete(check_db)
        get_post.likes -= 1
        db.session.commit()
        print("like removed")
        return "", 204


@app.route("/add_comment", methods=["GET", "POST"])
def add_comment():
    if request.method == "POST":
        id = request.form["post-id"]
        comment = request.form["comment"]
        if comment == "":
            print("comment empty")
            pass
        else:
            new_comment = Comment(
                post_id=id,
                comment=comment,
                commented_by=session['name']
            )
            db.session.add(new_comment)
            db.session.commit()
    return "", 204


@app.route("/view_comment/<int:id>")
def view_comments(id):
    comments = db.session.execute(db.select(Comment).filter_by(post_id=id)).scalars()
    post = db.session.execute(db.select(Post).filter_by(id=id)).scalar()
    return render_template("comments.html", comments=comments, post=post)


@app.route("/home")
def logout():
    session['name'] = None
    return render_template("index.html")



if __name__ == '__main__':
    app.run(port=8000, debug=True)
