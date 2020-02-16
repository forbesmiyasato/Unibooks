import os
import secrets
import logging
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from BookMarket.models import User, Item, ItemClass, ItemDepartment
from BookMarket.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from BookMarket import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html', title="about")


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(
            f'Hi {form.username.data}! Your account has been created, you can now login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if (user and bcrypt.check_password_hash(user.password, form.password.data)):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/item/new", methods=['GET', 'POST'])
@login_required
def new_item():
    classes = db.session.query(ItemClass).all()
    class_list = [(i.id, i.class_name) for i in classes]
    form = PostForm()
    form.item_class.choices = class_list
    departments = db.session.query(ItemDepartment).all()
    department_list = [(i.id, i.department_name) for i in departments]
    form.item_department.choices = department_list
    if form.validate_on_submit():
        images = form.images.data
        if images:
            logging.error('in if')
            save_picture(images)
        post = Item(name=form.name.data, description=form.description.data, user_id=current_user.id,
                    price=form.price.data, class_id=form.item_class.data, department_id=form.item_department.data)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Item', form=form, legend='New')


@app.route("/shop")
def shop():
    page = request.args.get('page', 1, type=int)
    posts = Item.query.order_by(Item.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('shop.html', title='Shop', posts=posts)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Item.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Item.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Item', form=form, legend='Update')


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Item.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted', 'success')
    return redirect(url_for('home'))


@app.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Item.query.order_by(Item.date_posted.desc()).filter_by(author=user).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


# Utility functions

def save_picture(form_images):
    for images in form_images:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(images.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(app.root_path, 'static/item_pics', picture_fn)
        output_size = (500, 500)
        resizedImage = Image.open(images)
        resizedImage.thumbnail(output_size)
        resizedImage.save(picture_path)
        logging.error('%s picture path', images.filename)

    # #remove use previous profile pic in file system so it doesn't get overloaded
    # if (current_user.image_file != 'default.jpg'):
    #     current_picture_path = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
    #     if os.path.exists(current_picture_path):
    #         os.remove(current_picture_path)
    return picture_fn
