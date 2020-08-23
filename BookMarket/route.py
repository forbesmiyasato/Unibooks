import os
import secrets
import boto3
# from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, session, Markup
from flask_login import current_user, login_required
from .models import Users, Item, ItemClass, ItemDepartment, ItemImage, SaveForLater
from .forms import UpdateAccountForm, PostForm
from . import app, db, S3_BUCKET
from .routes.userAuth import userAuth
from .routes.shop import shop_api
# from werkzeug.utils import secure_filename

app.register_blueprint(userAuth)
app.register_blueprint(shop_api)

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title="Home")


@app.route('/about')
def about():
    return render_template('about.html', title="about")


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    # form = UpdateAccountForm()
    # if form.validate_on_submit():
    #     if form.picture.data:
    #         picture_file = save_picture(form.picture.data)
    #         current_user.image_file = picture_file
    #     current_user.username = form.username.data
    #     current_user.email = form.email.data
    #     db.session.commit()
    #     flash('Your account has been updated!', 'success')
    #     return redirect(url_for('account'))
    # elif request.method == 'GET':
    #     form.username.data = current_user.username
    #     form.email.data = current_user.email
    # image_file = url_for(
    #     'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', confirmed=current_user.confirmed)


@app.route("/item/new", methods=['GET', 'POST'])
@login_required
def new_item():
    if current_user.confirmed is False:
        flash("You must confirm your email address before selling!", 'info')
        return redirect(url_for('account'))
    form = PostForm()
    # form.item_class.choices = class_list
    departments = db.session.query(ItemDepartment).all()
    department_list = [(i.id, i.department_name) for i in departments]
    form.item_department.choices = department_list
    if request.method == 'POST':
        # images = form.images.data  # without plugin
        images = request.files.getlist("images[]")
        post = Item(name=form.name.data, description=form.description.data, user_id=current_user.id,
                    price=form.price.data, class_id=form.item_class.data, department_id=form.item_department.data)
        db.session.add(post)
        db.session.commit()
        db.session.refresh(post)
        newId = post.id
        if images:
            thumbnail = save_picture(images, newId)
            if thumbnail:
                item = Item.query.filter_by(id=newId).first()
                item.thumbnail = thumbnail
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='Sell', form=form, legend='New')


@app.route('/class/<department>')
def item_class(department):
    classes = ItemClass.query.filter_by(department_id=department).all()
    classArray = []
    for item_class in classes:
        classObj = {}
        classObj['id'] = item_class.id
        classObj['department_id'] = item_class.department_id
        classObj['class_name'] = item_class.class_name
        classArray.append(classObj)
    return jsonify({'classes': classArray})


@app.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Item.query.order_by(Item.date_posted.desc()).filter_by(
        author=user).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@app.route('/add-to-bag', methods=['POST'])
def add_to_bag():
    user = request.args.get('user')
    item = request.args.get('item')
    added = False
    if current_user.is_authenticated is True:
        exist = SaveForLater.query.filter_by(
            item_id=item, user_id=user).first()
        if exist is None:
            new = SaveForLater(item_id=item, user_id=user)
            db.session.add(new)
            db.session.commit()
            added = True
        # user_saved_items = SaveForLater.query.filter_by(user_id=user).count()
    else:
        # user_saved_items = 1
        print(session.get('saved'))
        if session.get('saved') is None:
            session["saved"] = []
        print(session["saved"])
        saved_items = session["saved"]
        if item not in saved_items:
            saved_items.append(item)
            session["saved"] = saved_items
            session.modified = True
            added = True
    # return jsonify({'num_saved': user_saved_items})
    return jsonify({'added': added})


@app.route('/saved')
# @login_required
def saved_for_later():
    items_ids = None
    if current_user.is_authenticated:
        items_ids = db.session.query(SaveForLater.item_id).filter_by(
            user_id=current_user.id).order_by(SaveForLater.id.desc()).all()
    else:
        if "saved" in session:
            print(session["saved"])
            items_ids = session["saved"]
            print(items_ids)
    items = []
    if items_ids is not None:
        for id in items_ids:
            item = Item.query.get(id)
            print(item)
            if item:
                items.append(item)
    print(items)
    return render_template('saved_for_later.html', title='Saved', posts=items)


@app.route('/saved/delete', methods=['POST'])
# @login_required
def delete_saved():
    item = request.args.get('item_id')
    item_name = request.args.get('item_name')
    if current_user.is_authenticated:
        user = request.args.get('user_id')
        deleting_item = SaveForLater.query.filter_by(
            item_id=item, user_id=user).first()
        if deleting_item.user_id != current_user.id:
            abort(403)
        db.session.delete(deleting_item)
        db.session.commit()
    else:
        saved_items = session["saved"]
        if item in saved_items:
            saved_items.remove(item)
            session["saved"] = saved_items
            session.modified = True
    flash(Markup(
        f'<a href="/shop/{item}">{item_name}</a> has been removed from your bag'), 'success')
    return redirect(url_for('saved_for_later'))


@app.route('/post/delete', methods=['POST'])
@login_required
def delete_item():
    item = request.args.get('item_id')
    deleting_item = Item.query.get_or_404(item)
    delete_images_s3(item)
    item_name = deleting_item.name
    db.session.delete(deleting_item)
    db.session.commit()
    flash(f'Post "{item_name}" has been deleted', 'success')
    return redirect(request.referrer)


@app.route('/listings')
@login_required
def listings():
    listings = Item.query.filter_by(user_id=current_user.id).all()
    print(listings)
    return render_template('user_listings.html', listings=listings)


# Utility functions
def save_picture(form_images, item_id):
    thumbnail = None
    for index, images in enumerate(form_images):
        if images:
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(images.filename)
            picture_fn = random_hex + f_ext
            if (index == 0):
                thumbnail = picture_fn
            # picture_path = os.path.join(
            #     app.root_path, 'static/item_pics', picture_fn)
            # output_size = (183, 195)
            # # output_resolution = (1000, 1000)
            # resizedImage = Image.open(images)
            # # resizedImage.thumbnail(output_resolution)
            # resizedImage = resizedImage.resize(output_size, Image.ANTIALIAS)
            # resizedImage.save(picture_path)
            s3_resource = boto3.resource('s3')
            my_bucket = s3_resource.Bucket(S3_BUCKET)
            my_bucket.Object(picture_fn).put(Body=images)
            newImage = ItemImage(item_id=item_id, image_file=picture_fn)
            db.session.add(newImage)
            db.session.commit()
    return thumbnail
    # #remove use previous profile pic in file system so it doesn't get overloaded
    # if (current_user.image_file != 'default.jpg'):
    #     current_picture_path = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
    #     if os.path.exists(current_picture_path):
    #         os.remove(current_picture_path)


def delete_images_s3(item_id):
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    images = ItemImage.query.filter_by(item_id=item_id).all()
    for image in images:
        my_bucket.Object(image.image_file).delete()
# def download_file(file_name):
#     """
#     Function to download a given file from an S3 bucket
#     """
#     s3 = boto3.resource('s3')
#     output = f"downloads/{file_name}"
#     s3.Bucket(S3_BUCKET).download_file(file_name, output)

#     return output


@app.context_processor
def inject_num_items():
    if (current_user.is_authenticated):
        return {'numItems': db.session.query(SaveForLater.item_id).filter_by(
            user_id=current_user.id).order_by(SaveForLater.id.desc()).all()}
    elif session.get('saved'):
        return {'numItems': session["saved"]}
    else:
        return {'numItems': []}
