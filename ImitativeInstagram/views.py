# -*- encoding: utf-8 -*-
from ImitativeInstagram import app, db
from ImitativeInstagram.models import User, Image, Comments
from flask import render_template, redirect, request, flash, get_flashed_messages, send_from_directory
import random, hashlib  # add salt for password
from flask_login import login_user, logout_user, current_user, login_required
import json, uuid, os
from qiniusdk import qiniu_upload_file

# AJAX index
@app.route("/index/images/<int:page>/<int:per_page>")
def index_images(page, per_page):
    paginate = Image.query.order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page, error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        comments = []
        for i in range(0, min(2, len(image.comments))):
            comment = image.comments[i]
            comments.append({'username': comment.user.username, 'user_id': comment.user.id, 'content':comment.content})

        imgvo = {'id': image.id,
                 'url': image.url,
                 'comment_count': len(image.comments),
                 'user_id': image.user_id,
                 'head_url': image.user.head_url,
                 'created_date': str(image.created_date),
                 'comments': comments
                 }
        images.append(imgvo)

    map['images'] = images
    return json.dumps(map)
# index
@app.route("/")
def index():
    images = Image.query.order_by(db.desc(Image.id)).limit(10).all()
    return render_template("index.html", images=images)


# click pic on index
@app.route("/image/<int:image_id>/")
def image(image_id):
    image = Image.query.get(image_id)
    if image == None:
        return redirect("/")
    comments = Comments.query.filter_by(image_id=image_id).order_by(db.desc(Comments.id)).limit(20).all()
    return render_template("pageDetail.html", image=image, comments=comments)


# click on touxiang
@app.route("/profile/<int:user_id>/")
@login_required
def user(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect("/")
    paginate = Image.query.filter_by(user_id=user_id).paginate(page=1, per_page=3, error_out=False)
    return render_template("profile.html", user=user, images=paginate.items, has_next=paginate.has_next)

# AJAX request
@app.route("/profile/images/<int:user_id>/<int:page>/<int:per_page>")
def user_image(user_id, page, per_page):
    paginate = Image.query.filter_by(user_id=user_id).order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page, error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id':image.id, 'url':image.url, 'comment': len(image.comments)}
        images.append(imgvo)
    map['images'] = images
    return json.dumps(map)


# login
@app.route("/reloginpage/")
def reloginpage():
    msg = ''
    for m in get_flashed_messages(with_categories=False, category_filter=['relogin']):
        msg += m

    return render_template("login.html", msg=msg, next=request.values.get('next'))


# redirect
def redirect_with_msg(target, msg, category):
    if msg != None:
        flash(msg, category=category)
    return redirect(target)


# login
@app.route("/login/", methods={"get", "post"})
def login():
    username = request.values.get("username").strip()
    password = request.values.get("password").strip()

    # username or password is ""
    if username == "" or password == "":
        return redirect_with_msg("/reloginpage", u"用户名或密码不能为空", "relogin")


    user = User.query.filter_by(username=username).first()
    # user not exists
    if user == None:
        return redirect_with_msg("/reloginpage", u"用户名不存在", "relogin")
    #check password
    m = hashlib.md5()
    m.update(password + user.salt)
    if m.hexdigest() != user.password:
        return redirect_with_msg("/reloginpage", u"密码错误", "relogin")

    login_user(user)

    next = request.values.get("next")
    if next != None and next.startswith("/"):
        return  redirect(next)

    return redirect("/")

# register
@app.route("/reg/", methods={"post", "get"})
def reg():
    username = request.values.get("username").strip()
    password = request.values.get("password").strip()
    user = User.query.filter_by(username=username).first()
    # username or password is ""
    if username == "" or password == "":
        return redirect_with_msg("/reloginpage", u"用户名或密码不能为空", "relogin")
    # user exists
    if user != None:
        return redirect_with_msg("/reloginpage", u"用户名已经存在", "relogin")

    '''
    insert into database
    '''
    salt = ".".join(random.sample("0123456789abcdefghijkABCDEFGHIJK", 10))
    m = hashlib.md5()
    m.update(password + salt)
    # now password is a hexical string
    password = m.hexdigest()
    user = User(username, password, salt)
    db.session.add(user)
    db.session.commit()

    login_user(user)

    next = request.values.get("next")
    if next != None and next.startswith("/"):
        return redirect(next)
    return redirect("/")

@app.route("/logout/")
def logout():
    logout_user()
    return redirect("/")

@app.route("/image/<image_name>")
def view_image(image_name):
    return send_from_directory(app.config["UPLOAD_DIR"], image_name)

@app.route('/addcomment/', methods={"post"})
@login_required
def add_comment():
    image_id = request.values['image_id']
    content = request.values['content']
    comment = Comments(image_id, content, current_user.id)
    db.session.add(comment)
    db.session.commit()
    return json.dumps({"code": 0, "id": comment.id,
                       "content": comment.content,
                       "user_name": comment.user.username,
                       "user_id": comment.user_id})

def save_to_qiniu(file, file_name):
    return qiniu_upload_file(file, file_name)

def save_to_local(file, file_name):
    save_dir = app.config["UPLOAD_DIR"]
    file.save(os.path.join(save_dir, file_name))
    # visit path
    return "/image/" + file_name


# upload pic
@app.route("/upload/",methods={"post"})
def upload():
    file = request.files['file']
    # whether a pic
    file_ext = ""
    if file.filename.find(".") > 0:
        file_ext = file.filename.rsplit(".", 1)[1].strip().lower()
    if file_ext in app.config["ALLOWD_EXT"]:
        #save the pic
        filename = str(uuid.uuid1()).replace("-", "") + "." + file_ext
        #url = save_to_local(file, filename)
        url = qiniu_upload_file(file, filename)
        if url != None:
            db.session.add(Image(url, current_user.id))
            db.session.commit()

    return redirect("/profile/%d" % current_user.id)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = Image.query.filter_by(user_id=user_id).order_by(db.desc(Image.id)).paginate(page=1, per_page=3, error_out=False)
    return render_template('profile.html', user=user, images=paginate.items, has_next=paginate.has_next)


