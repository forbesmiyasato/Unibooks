import os
import atexit
import threading
from datetime import datetime, timedelta

# from PIL import Image
from flask import (render_template, url_for, flash, redirect, request, abort, jsonify, session,
                   Markup, make_response, current_app, make_response, copy_current_request_context)
from flask_login import current_user, login_required, logout_user
from flask_mail import Message
from .models import Users, Item, ItemClass, ItemDepartment, ItemImage, SaveForLater, School, ItemCategory, Inappropriate
from .forms import UpdateAccountForm, ItemForm, MessageForm
from . import app, db, mail
from .routes.userAuth import userAuth, login_html
from .routes.shop import shop_api, item_html
from .utility_funcs import (save_images_to_db_and_s3, delete_images_from_s3_and_db,
                            delete_non_remaining_images_from_s3_and_db, send_message, delete_all_user_listings__images_from_s3_and_db)
from apscheduler.schedulers.background import BackgroundScheduler
from .background import query_for_reminder
# from werkzeug.utils import secure_filename

app.register_blueprint(userAuth)
app.register_blueprint(shop_api)


# @app.before_request
# def beforeRequest():
#     print(request.url)
#     if not request.url.startswith('https') and request.url != "http://localhost:5000/":
#         return redirect(request.url.replace('http', 'https', 1))
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    try:
        """Generate sitemap.xml. Makes a list of urls and date modified."""
        pages = []
        ten_days_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        # static pages
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and len(rule.arguments) == 0:
                pages.append(
                    ["https://unibooks.io" +
                        str(rule.rule), ten_days_ago]
                )

        sitemap_xml = render_template('sitemap_template.xml', pages=pages)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"

        return response
    except Exception as e:
        return(str(e))


@app.route('/loaderio-d2cf780526acfac1fe150b2163a01707/')
def loaderio():
    return render_template('loaderio-d2cf780526acfac1fe150b2163a01707.txt')


@app.before_first_request
def init_scheduler():
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(query_for_reminder, 'interval',
                            kwargs={'app': app}, hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


@app.errorhandler(404)
def error404(error):
    flash("Page Not Found! Redirected back to home.", 'error')
    return redirect(url_for('home'))


@app.route('/')
@app.route('/home')
def home():
    standalone = request.args.get('standalone')
    return render_template('home.html', title="Home", standalone=standalone)


@app.route('/aboutus')
def about_us():
    standalone = request.args.get('standalone')
    print(standalone)
    # if standalone != "true":
    #     standalone = False
    return render_template('about_us.html', standalone=standalone, title="About Us")


@app.route('/help', methods=['GET', 'POST'])
def help():
    message_form = MessageForm()
    standalone = request.args.get('standalone', None)
    if request.method == 'POST':
        email = request.form.get('email', "None")
        standalone = "standalone"
        msg = Message("Feedback from user",
                      sender=("Unibooks", "do-not-reply@unibooks.io"),
                      recipients=["pacificubooks@gmail.com"], html=render_template("message_email.html", name="feedback from user",
                                                                                   email=email, body=request.form.get('message')))
        sender = threading.Thread(name="mail_sender", target=send_message, args=(
            current_app._get_current_object(), msg,))
        sender.start()
        return jsonify({'origin': 'contactus'})

    return render_template('FAQ.html', standalone=standalone, title="Help", message_form=message_form,
                           message_title="Need help?", optional="(optional)")


@app.route("/account", methods=['GET'])
@login_required
def account():
    standalone = request.args.get('standalone')
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
    return render_template('account.html', title='Account', standalone=standalone)


@app.route("/account/delete", methods=['POST'])
@login_required
def account_delete():
    user = current_user
    @copy_current_request_context
    def delete_user_data(user):
        delete_all_user_listings__images_from_s3_and_db(user)
        db.session.delete(user)
        db.session.commit()
    async_task = threading.Thread(name="delete_user", target=delete_user_data, args=(user,))
    async_task.start()
    logout_user()
    flash('Your account has been successfully deleted. Please register again to use our service.', 'success')
    return redirect(url_for('home'))


@app.route("/item/new", methods=['GET', 'POST'])
def new_item():
    standalone = request.args.get('standalone', None)
    if request.method == 'POST':
        # images = form.images.data  # without plugin
        images = request.files.getlist('files[]')
        print(images)
        print("POST SCHOOL", current_user.school)
        if not request.form.get('category_id'):
            post = Item(name=request.form.get('name'), description=request.form.get('description'), user_id=current_user.id,
                        price=request.form.get('price'), class_id=request.form.get('class_id'), department_id=request.form.get('department_id'),
                        isbn=request.form.get('isbn'), author=request.form.get('author'), school=current_user.school)
        else:
            post = Item(name=request.form.get('name'), description=request.form.get('description'), user_id=current_user.id,
                        price=request.form.get('price'), category_id=request.form.get('category_id'),
                        isbn=request.form.get('isbn'), author=request.form.get('author'), school=current_user.school)
        db.session.add(post)
        db.session.commit()
        db.session.refresh(post)
        newId = post.id
        item = Item.query.filter_by(id=newId).first()
        if images:
            print('before break 1')
            thumbnail = save_images_to_db_and_s3(images, newId)
            print('before break 2')
            if thumbnail:
                item.thumbnail = thumbnail
        current_user.listings = current_user.listings + 1
        db.session.commit()
        # flash('Your post has been created!', 'success')
        # return redirect(url_for('home'))
        # result = {'url': url_for('shop_api.item', item_id=post.id)}
        return jsonify({'html': (item_html(post.id, item, 'notfromnewitem')), 'url': url_for('shop_api.item', item_id=post.id)})
    if current_user.is_authenticated is False:
        if standalone:
            return jsonify({'state': "login-required"})
        else:
            flash("You must sign in before selling!", 'info')
            return redirect(url_for('userAuth.login'))
    if current_user.confirmed is False:
        if standalone:
            return jsonify({'state': "confirm-required"})
        else:
            flash("You must confirm your email address before selling!", 'info')
            return redirect(url_for('account', standalone=standalone))
    if current_user.listings >= 10:
        if standalone:
            return jsonify({'state': "max-listings"})
        else:
            print("!!!!!!!!!!!!")
            flash("There is a max of 10 listings at a time! Please wait or delete listings before selling.", 'error')
            return redirect(url_for('listings', standalone=standalone))
    form = ItemForm()
    # form.item_class.choices = class_list
    departments = ItemDepartment.query.filter_by(
        school=session['school']).all()
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    isBook = True  # default display is book item
    # department_list = [(i.id, i.department_name) for i in departments]
    return render_template('create_post.html', title='Sell', form=form, legend='New', item_id=0, departments=departments,
                           standalone=standalone, categories=categories, isBook=isBook)


@app.route('/class/<department>')
def item_class(department):
    classes = ItemClass.query.filter_by(department_id=department).all()
    classArray = []
    for item_class in classes:
        classObj = {}
        classObj['id'] = item_class.id
        classObj['department_id'] = item_class.department_id
        classObj['class_name'] = item_class.abbreviation
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
    item = request.args.get('item')
    added = False
    if current_user.is_authenticated is True:
        exist = SaveForLater.query.filter_by(
            item_id=item, user_id=current_user.id).first()
        if exist is None:
            new = SaveForLater(item_id=item, user_id=current_user.id)
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


@app.route('/saved', methods=['GET', 'POST'])
def saved_for_later():
    title = 'Saved'
    standalone = request.args.get('standalone')
    print(request.form.get('email'))
    if request.method == 'POST' and request.form.get('email'):
        item_id = request.args.get('item')
        print("ID", item_id)
        _item = Item.query.get_or_404(item_id)
        if current_user.last_buy_message_sent is None:
            current_user.last_buy_message_sent = datetime.utcnow()
            db.session.commit()
        else:
            time_difference = datetime.utcnow() - current_user.last_buy_message_sent
            minutes = divmod(time_difference.total_seconds(), 60)[0]
            print("TIME", minutes)
            if minutes >= 60.0:
                current_user.last_buy_message_sent = datetime.utcnow()
                current_user.num_buy_message_sent = 1
                db.session.commit()
            elif minutes < 60.0:
                if current_user.num_buy_message_sent >= 10:
                    return jsonify({'origin': 'wait'})
                else:
                    current_user.num_buy_message_sent += 1
                    db.session.commit()
        msg = Message("Message regarding " + "\"" + _item.name + "\"",
                      sender=("Unibooks", 'do-not-reply@unibooks.io'),
                      recipients=[_item.owner.email], html=render_template("message_email.html", name=_item.name,
                                                                           email=request.form.get('email'), body=request.form.get('message')))
        sender = threading.Thread(name="mail_sender", target=send_message, args=(
            current_app._get_current_object(), msg,))
        sender.start()
        return jsonify({'origin': 'single'})
    if 'cart' in request.args:
        title = 'Saved?cart'
    items_ids = None
    if current_user.is_authenticated:
        items_ids = db.session.query(SaveForLater.item_id).filter_by(
            user_id=current_user.id).order_by(SaveForLater.id.desc()).all()
    else:
        if "saved" in session:
            items_ids = session["saved"]
    items = []
    if items_ids is not None:
        for id in items_ids:
            item = Item.query.get(id)
            if item:
                items.append(item)
    return render_template('saved_for_later.html', title=title, posts=items, standalone=standalone)


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
    standalone = request.form['standalone']
    # standalone = "standlone"
    print(standalone)
    deleting_item = Item.query.get_or_404(item)
    delete_images_from_s3_and_db(item)
    item_name = deleting_item.name
    current_user.listings = current_user.listings - 1
    db.session.delete(deleting_item)
    db.session.commit()
    # flash(f'Post "{item_name}" has been deleted', 'success')
    if standalone == "listings":
        print(standalone)
        return jsonify(html=listings_html(standalone))
    return jsonify({'result': 'deleted'})


def listings_html(standalone=None):
    _listings = Item.query.filter_by(user_id=current_user.id).order_by(
        Item.date_posted.asc()).all()
    form = ItemForm()
    return render_template('user_listings.html', title="Listings", listings=_listings,
                           legend='Edit', form=form, item_id=1, item=None, standalone=standalone)


@app.route('/listings')
@login_required
def listings():
    standalone = request.args.get('standalone')
    return listings_html(standalone)

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


@app.route("/messagebuyerform")
def message_buyer_form():
    message_form = MessageForm()
    return render_template('message_form.html', message_form=message_form, message_title="Contact Seller", need_customization=True)


@app.route("/editform/<int:item_id>")
def get_edit_form(item_id=None):
    _item = Item.query.get_or_404(item_id)
    edit_form = ItemForm()
    # It's never actually posting here, just left it incase we need to
    if request.method == 'POST':
        remains = request.form.get('remaining_files')
        images = request.files.getlist("files[]")
        delete_non_remaining_images_from_s3_and_db(item_id, remains)
        if not _item.images:
            _item.thumbnail = "No_picture_available.png"
        if images:
            prevImageCount = _item.images
            thumbnail = save_images_to_db_and_s3(images, item_id)
            if thumbnail and not prevImageCount:
                _item.thumbnail = thumbnail
        _item.name = request.form.get('name')
        _item.description = request.form.get('description')
        _item.isbn = request.form.get('isbn')
        _item.author = request.form.get('author')
        _item.user_id = current_user.id
        _item.price = request.form.get('price')
        _item.class_id = request.form.get('class_id')
        _item.department_id = request.form.get('department_id')
        db.session.commit()
        print(item_id)
        # result = {'url': url_for('shop_api.item', item_id=item_id)}
    images = ItemImage.query.filter_by(item_id=item_id).all()
    item_class = ItemClass.query.get(_item.class_id)
    department = ItemDepartment.query.get(_item.department_id)
    # for updating
    departments = db.session.query(ItemDepartment).all()
    edit_form.name.data = _item.name
    edit_form.description.data = _item.description
    edit_form.price.data = _item.price
    edit_form.isbn.data = _item.isbn
    edit_form.author.data = _item.author
    if _item.category_id is not None:
        print(_item.category_id)
        edit_form.item_category.data = _item.category_id
    else:
        edit_form.item_class.data = item_class
        edit_form.item_department.data = department
    isBook = True if _item.category_id is None else False
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    category = ItemCategory.query.get(_item.category_id)    # for messaging
    return render_template('post_form.html', title=_item.name, item=_item, images=images,
                           item_class=item_class, department=department, form=edit_form, legend="Edit",
                           item_id=item_id, departments=departments, isBook=isBook, categories=categories, category=category)


@app.context_processor
def inject_schools():
    schools = db.session.query(School).all()
    return {'schools': schools}


@app.route('/setschool/<int:school>')
def set_school_in_session(school):
    state = request.args.get('state', None)
    if state == "loggout":
        logout_user()
    elif state == 'emptycart':
        session.pop('saved')
    session['school'] = school
    return ('', 204)


@app.route('/contactus', methods=['GET', 'POST'])
def leave_a_message():
    message_form = MessageForm()
    standalone = request.args.get('standalone', None)

    if request.method == 'POST':
        email = request.form.get('email', "None")
        standalone = "standalone"
        msg = Message("Feedback from user",
                      sender=("Unibooks", "do-not-reply@unibooks.io"),
                      recipients=["pacificubooks@gmail.com"], html=render_template("message_email.html", name="feedback from user",
                                                                                   email=email, body=request.form.get('message')))
        sender = threading.Thread(name="mail_sender", target=send_message, args=(
            current_app._get_current_object(), msg,))
        sender.start()
        return jsonify(origin='contactus')
    return render_template('message_page.html', title="Contact Us", message_form=message_form, standalone=standalone,
                           message_title="Contact Us", optional="(optional)")


@app.route('/report/<int:item_id>')
def report_item(item_id):
    item = Inappropriate.query.filter_by(id=item_id).first()
    if item is None:
        new = Inappropriate(id=item_id, count=1)
        db.session.add(new)
        db.session.commit()
    else:
        item.count += 1
        db.session.commit()

    return 'added'
