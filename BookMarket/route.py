import os
import atexit
# from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, session, Markup
from flask_login import current_user, login_required
from .models import Users, Item, ItemClass, ItemDepartment, ItemImage, SaveForLater
from .forms import UpdateAccountForm, PostForm
from . import app, db
from .routes.userAuth import userAuth
from .routes.shop import shop_api
from .utility_funcs import save_images_to_db_and_s3, delete_images_from_s3_and_db
from apscheduler.schedulers.background import BackgroundScheduler
from .background import query_for_reminder
# from werkzeug.utils import secure_filename

app.register_blueprint(userAuth)
app.register_blueprint(shop_api)

@app.before_first_request
def init_scheduler():
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(query_for_reminder, 'interval', kwargs={'app':app}, hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


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


# @app.route("/files/<int:userid>", methods=['POST'])
# def post_item_files(userid):
#     if request.method == "POST":
#         images = request.files
#         print(images)
#         if images:
#             thumbnail = save_images_to_db_and_s3(images, newId)
#             if thumbnail:
#                 item = Item.query.filter_by(id=newId).first()
#                 item.thumbnail = thumbnail
#     return jsonify({'added': 'added'})

@app.route("/item/new", methods=['GET', 'POST'])
@login_required
def new_item():
    if request.method == 'POST':
        # images = form.images.data  # without plugin
        images = request.files.getlist('files[]')
        print(images)
        post = Item(name=request.form.get('name'), description=request.form.get('description'), user_id=current_user.id,
                    price=request.form.get('price'), class_id=request.form.get('class_id'), department_id=request.form.get('department_id'))
        db.session.add(post)
        db.session.commit()
        db.session.refresh(post)
        newId = post.id
        if images:
            thumbnail = save_images_to_db_and_s3(images, newId)
            if thumbnail:
                item = Item.query.filter_by(id=newId).first()
                item.thumbnail = thumbnail
        db.session.commit()
        # flash('Your post has been created!', 'success')
        # return redirect(url_for('home'))
        result = {'url': url_for('shop_api.item', item_id=post.id)}
        return jsonify(result)
    if current_user.confirmed is False:
        flash("You must confirm your email address before selling!", 'info')
        return redirect(url_for('account'))
    form = PostForm()
    # form.item_class.choices = class_list
    departments = db.session.query(ItemDepartment).all()
    # department_list = [(i.id, i.department_name) for i in departments]
    print(departments)
    return render_template('create_post.html', title='Sell', form=form, legend='New', item_id=0, departments=departments)


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
    delete_images_from_s3_and_db(item)
    item_name = deleting_item.name
    db.session.delete(deleting_item)
    db.session.commit()
    flash(f'Post "{item_name}" has been deleted', 'success')
    return redirect(url_for('shop_api.shop'))


@app.route('/listings')
@login_required
def listings():
    listings = Item.query.filter_by(user_id=current_user.id).all()
    print(listings)
    return render_template('user_listings.html', listings=listings)

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
    if current_user:
        if (current_user.is_authenticated):
            return {'numItems': db.session.query(SaveForLater.item_id).filter_by(
                user_id=current_user.id).order_by(SaveForLater.id.desc()).all()}
        elif session.get('saved'):
            return {'numItems': session["saved"]}
        else:
            return {'numItems': []}
    else:
        return {'numItems': []}
