import werkzeug.security
from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from flask_session import Session


app = Flask(__name__)
post_id = 0

#SESSION
app.config.from_object(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#DATABASE
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

#INITIATE DB
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
        users=[]
        for user in users_db:
            users.append(user.username)
        all_post = db.session.execute(db.select(Post).order_by(desc(Post.id))).scalars()
        likes = db.session.execute(db.select(Likes).filter_by(post_liker=session['name'])).scalars()
        l_like = [like.post_id for like in likes]
        return render_template("homepage.html", session=session, all_post=all_post, users=users, likes=likes, l_like=l_like)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create_user", methods=["GET","POST"])
def create_user():
    if request.method == "POST":
        new_username = request.form["Username"]
        dbuser = db.session.execute(db.select(User).filter_by(username=new_username)).scalar()
        password = request.form["Password"]
        hash = werkzeug.security.generate_password_hash(password,method='pbkdf2:sha256', salt_length=8)
        try:
            if new_username == dbuser.username:
                return render_template("register.html", msg="Username is already taken. Please use another username.")
        except AttributeError:
            user = User(
                name= request.form["Name"],
                lastName= request.form["LastName"],
                username= request.form["Username"],
                email= request.form["Email"],
                password= hash
            )
            db.session.add(user)
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        dbuser = db.session.execute(db.select(User).filter_by(username=username)).scalar()
        dbpassword = db.session.execute(db.select(User).filter_by(username=username, password=password)).scalar()
        try:
            if dbuser.username == username and werkzeug.security.check_password_hash(dbuser.password, password):
                session['name'] = dbuser.username
                print(session["name"])
                return redirect("/")
        except AttributeError:
            return render_template("index.html", msg="Wrong Username or Password")
    return render_template("index.html")


@app.route("/search", methods=["GET","POST"])
def search():
    if request.method == "POST":
        username = request.form["search"]
        print(username)
        try:
            search_user = db.session.execute(db.select(User).filter_by(username=username)).scalar()
            all_post = db.session.execute(db.select(Post).filter_by(owner_name=username)).scalars()
            if search_user.username == username:
                return render_template("profile.html", user=search_user, all_post=all_post)
        except AttributeError:
            return redirect("/")
    return render_template("homepage.html")

@app.route("/homepage", methods=["GET","POST"])
def new_post():
    if request.method == "POST":
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
        return redirect("/")
    else:
        db.session.delete(check_db)
        get_post.likes -= 1
        db.session.commit()
        print("like removed")
        return redirect("/")

@app.route("/add_comment", methods=["GET", "POST"])
def add_comment():
    if request.method == "POST":
        id = request.form["post-id"]
        comment = request.form["comment"]
        new_comment = Comment(
            post_id=id,
            comment=comment,
            commented_by=session['name']
        )
        db.session.add(new_comment)
        db.session.commit()
    return redirect("/")

@app.route("/view_comment/<int:id>")
def view_comments(id):
    comments = db.session.execute(db.select(Comment).filter_by(post_id=id)).scalars()
    post = db.session.execute(db.select(Post).filter_by(id=id)).scalar()
    return render_template("comments.html", comments=comments, post=post)

@app.route("/home")
def logout():
    session['name'] = None
    return render_template("index.html")


@app.route("/test")
def test():
    all_post = db.session.execute(db.select(Post)).scalars()
    your_likes = db.session.execute(db.select(Likes).filter_by(post_liker=session["name"])).scalars()
    m = [like.post_id for like in your_likes]
    return render_template("test.html", all_post=all_post, your_likes=your_likes, m=m)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
