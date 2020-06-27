from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
from werkzeug.utils import secure_filename
import json
from flask_mail import Mail
import os
import math


local_server = True
with open("config.json", "r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_loc']
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pwd']
)

mail = Mail(app)


if local_server == True:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]


db = SQLAlchemy(app)

'''
srno, name,email,phone_num,mes
'''

class Contacts(db.Model):

    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    mes = db.Column(db.String(1500), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    tagline = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(45), nullable=False)
    img_file = db.Column(db.String(45), nullable=False)


@app.route("/")
def home():
    # Pagination Logic
    posts = Posts.query.order_by(Posts.sno.desc()).all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_post']): (page-1)* int(params['no_of_post'])+ int(params['no_of_post'])]
    if(page == 1):
        prev = '#'
        next = "/?page=" + str(page+1)

    elif(page == last):
        prev = "/?page=" + str(page-1)
        next = '#'
    else:
        next = "/?page=" + str(page+1)
        prev = "/?page=" + str(page-1)


    return render_template("index.html", params=params, posts=posts, next=next, prev=prev)


@app.route("/admin", methods=['GET', 'POST'])
def admin_dsp():
    if ('user' in session and session['user'] == params['admin_email']):
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == params['admin_email'] and password == params['admin_pwd']:
            # will create session..
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            raise ("Please check id and password..")
    else:
        return render_template("login.html", params=params)



@app.route("/delete/<string:sno>", methods=['GET'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_email']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/admin")



@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_email']:
        if request.method == 'POST':
            frm_title = request.form.get('title')
            frm_tagline = request.form.get('tagline')
            frm_slug = request.form.get('slug')
            frm_content = request.form.get('content')
            frm_author = request.form.get('author')
            frm_img = request.form.get('img_file')
            frm_date = datetime.now()

            if sno == '0':
                db.session.add(post)
                post = Posts(title=frm_title, slug=frm_slug, content=frm_content, author=frm_author, tagline=frm_tagline, img_file=frm_img, date=frm_date )
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = frm_title
                post.slug = frm_slug
                post.content = frm_content
                post.author = frm_author
                post.tagline = frm_tagline
                post.img_file = frm_img
                post.date = frm_date
                db.session.commit()
                return redirect("/edit/"+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    print(post.author)

    return render_template("post.html", params=params, post=post)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/admin")


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add Entry to the database '''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        msg = request.form.get('mes')

        entry = Contacts(name=name, email=email, phone_num=phone_num, mes=msg)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message from Trobleshooters: " + name, sender=email, recipients=[params['gmail-user']], body=msg + '\n' + email + '\n' + phone_num )

    return render_template("contact.html",params=params)


@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_email']:
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully.."


app.run(debug=True)
