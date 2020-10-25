import os
import atexit
import threading
from datetime import datetime, timedelta, timezone

# from PIL import Image
from flask import (render_template, url_for, flash, redirect, request, abort, jsonify, session,
                   Markup, make_response, current_app, make_response, copy_current_request_context)
from flask_login import current_user, login_required, logout_user
from flask_mail import Message
from .models import Users, Item, ItemClass, ItemDepartment, ItemImage, SaveForLater, School, ItemCategory, Inappropriate, Statistics
from .forms import UpdateAccountForm, ItemForm, MessageForm
from . import app, db, mail
from .routes.userAuth import userAuth, login_html
from .routes.shop import shop_api, item_html
from .utility_funcs import (save_images_to_db_and_s3, delete_images_from_s3_and_db,
                            delete_non_remaining_images_from_s3_and_db, send_message, delete_all_user_listings__images_from_s3_and_db)
# from apscheduler.schedulers.background import BackgroundScheduler
# from .background import query_for_reminder
# from werkzeug.utils import secure_filename

app.register_blueprint(userAuth)
app.register_blueprint(shop_api)


@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    """
    Generate sitemap.xml. Makes a list of urls and date modified.
    ---
    get:
        parameters:
            None
        responses:
            200:
                The website's sitemap
    """
    try:
        pages = []
        ten_days_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        # static pages
        for rule in app.url_map.iter_rules():
            if ("GET" in rule.methods and len(rule.arguments) == 0 and "loader" not in rule.rule
                    and "sitemap" not in rule.rule and "logout" not in rule.rule
                    and "messagebuyerform" not in rule.rule and "item/new" not in rule.rule
                    and "listings" not in rule.rule and "account" not in rule.rule
                    and "shop/data" not in rule.rule):
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


@app.before_request
def before_request():
    """
    Handle if request is standalone and doesn't have school in session
    ---
    parameters:
        None
    responses:
        200:
            If request is standalone and doesn't have school session, it'll
            respond with a json object with missing-session and request path
            key value pair
    """
    standalone = request.args.get('standalone')
    if standalone and session.get('school') is None:
        path = request.path
        # if path == '/item/new':
        #     flash('School Session Needed!', 'error')
        #     return redirect(url_for('home'))
        flash('School Session Needed!', 'error')
        return jsonify({'missing-session': path})


@app.route('/loaderio-d2cf780526acfac1fe150b2163a01707/')
def loaderio():
    """
    Validation for loader.io load testing
    ---
    parameters:
        None
    responses:
        200:
            Renders the loader.io validation text file
    """
    return render_template('loaderio-d2cf780526acfac1fe150b2163a01707.txt')


# @app.before_first_request
# def init_scheduler():
#     """
#     Background task that warns users via email that their post is about to expire
#     and delete posts that expired
#     ---
#     parameters:
#         None
#     responses:
#         None
#     """
#     scheduler = BackgroundScheduler()
#     job = scheduler.add_job(query_for_reminder, 'interval',
#                             kwargs={'app': app}, hours=24)
#     scheduler.start()
#     atexit.register(lambda: scheduler.shutdown())


@app.errorhandler(404)
def error404(error):
    """
    Handles 404 errors
    ---
    get:
        parameters:
            error: the error
        responses:
            301:
                Redirects to home
    """
    flash("Page Not Found! Redirected back to home.", 'error')
    return redirect(url_for('home'))


@app.route('/')
@app.route('/home')
def home():
    """
    The home page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The home page
    """
    standalone = request.args.get('standalone')
    return render_template('home.html', title="Home", standalone=standalone)


@app.route('/aboutus')
def about_us():
    """
    The about us page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The about us page
    """
    standalone = request.args.get('standalone')
    # if standalone != "true":
    #     standalone = False
    return render_template('about_us.html', standalone=standalone, title="About Us")


@app.route('/help', methods=['GET', 'POST'])
def help():
    """
    The help page endpoint
    ---
    get:
        parameters:
            None
        responses:
            200:
                The help page
    post:
        parameters:
            None
        responses:
            200:
                The bug report or contact us email is successfully sent
            400:
                Missing csrf token
    """
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
    """
    The account page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The account page
    """
    standalone = request.args.get('standalone')
    return render_template('account.html', title='Account', standalone=standalone)


@app.route("/account/delete", methods=['POST'])
@login_required
def account_delete():
    """
    Deletes the current user's account and logs them out concurrently 
    ---
    post:
        parameters:
            None
        responses:
            301:
                Redirects to home page after operation is done
    """
    user = current_user
    @copy_current_request_context
    def delete_user_data(user):
        delete_all_user_listings__images_from_s3_and_db(user)
        db.session.delete(user)
        db.session.commit()
    async_task = threading.Thread(
        name="delete_user", target=delete_user_data, args=(user,))
    async_task.start()
    logout_user()
    flash('Your account has been successfully deleted. Please register again to use our service.', 'success')
    return redirect(url_for('home'))


@app.route("/item/new", methods=['GET', 'POST'])
def new_item():
    """
    Handles the user reaching the sell page endpoint
    ---
    get:
        parameters:
            None
        responses:
            200:
                The sell page
            301:
                Redirects due to missing school session, unauthenticated,
                unconfirmed or reached max listings
    post:
        parameters:
            None
        Responses:
            200:
                Post successful, returns json with html and product detail page url
            400:
                Missing csrf token
    """
    if session.get('school') is None:
        flash('School Session Needed!', 'error')
        return redirect(url_for('home'))
    standalone = request.args.get('standalone', None)
    if request.method == 'POST':
        # images = form.images.data  # without plugin
        images = request.files.getlist('files[]')
        department_id = None
        course_id = None
        category_id = None
        if not request.form.get('category_id'):
            department_id = request.form.get('department_id')
            course_id = request.form.get('class_id')
            post = Item(name=request.form.get('name'), description=request.form.get('description'), user_id=current_user.id,
                        price=request.form.get('price'), class_id=course_id, department_id=department_id,
                        isbn=request.form.get('isbn'), author=request.form.get('author'), school=current_user.school)
        else:
            category_id = request.form.get('category_id')
            post = Item(name=request.form.get('name'), description=request.form.get('description'), user_id=current_user.id,
                        price=request.form.get('price'), category_id=category_id,
                        isbn=request.form.get('isbn'), author=request.form.get('author'), school=current_user.school)

        nonbook = 0
        stats = Statistics.query.filter_by(school=session['school']).first()
        if not category_id:
            course = ItemClass.query.filter_by(id=course_id).first()
            course.count += 1
            department = ItemDepartment.query.filter_by(
                id=department_id).first()
            department.count += 1
        else:
            nonbook = 1
            category = ItemCategory.query.filter_by(id=category_id).first()
            category.count += 1
        if stats is None:
            new_stats = Statistics(
                total_listings=1, current_listings=1, non_textbooks=nonbook, school=session['school'])
            db.session.add(new_stats)
        else:
            stats.total_listings += 1
            stats.current_listings += 1
            stats.non_textbooks += nonbook
        # add_count_async = threading.Thread(name="add counts", target=add_counts, args=(
        #     department_id, course_id, category_id,))
        # add_count_async.start()
        current_user.listings = current_user.listings + 1
        current_user.total_listings += 1
        db.session.add(post)
        db.session.commit()
        db.session.refresh(post)
        newId = post.id
        item = Item.query.filter_by(id=newId).first()
        if images:
            try:
                thumbnail = save_images_to_db_and_s3(images, newId)
            except ValueError:
                return ('', 400)
            if thumbnail:
                item.thumbnail = thumbnail
        db.session.commit()
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
            flash("There is a max of 10 listings at a time! Please wait or delete listings before selling.", 'error')
            return redirect(url_for('listings', standalone=standalone))
    form = ItemForm()
    departments = ItemDepartment.query.filter_by(
        school=session['school']).order_by(ItemDepartment.abbreviation).all()
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    isBook = True  # default display is book item
    return render_template('create_post.html', title='Sell', form=form, legend='New', item_id=0, departments=departments,
                           standalone=standalone, categories=categories, isBook=isBook)


@app.route('/class/<department>')
def item_class(department):
    """
    Gets all the courses within a department
    ---
    get:
        parameters:
            department: department's ID
        responses:
            200:
                A list of courses in the department in JSON
    """
    classes = ItemClass.query.filter_by(department_id=department).order_by(
        ItemClass.abbreviation).all()
    classArray = []
    for item_class in classes:
        classObj = {}
        classObj['id'] = item_class.id
        classObj['department_id'] = item_class.department_id
        classObj['class_name'] = item_class.abbreviation
        classObj['class_full_name'] = item_class.class_name
        classObj['count'] = item_class.count
        classArray.append(classObj)
    return jsonify({'classes': classArray})


@app.route('/add-to-bag', methods=['POST'])
def add_to_bag():
    """
    Adds the item to the users shopping bag (saved list)
    ---
    post:
        parameters:
            None
        Responses:
            200:
                Added successfully, returns json with added being true
            400:
                Missing csrf token
    """
    item = request.form.get('item_id')
    added = False
    if current_user.is_authenticated is True:
        exist = SaveForLater.query.filter_by(
            item_id=item, user_id=current_user.id).first()
        if exist is None:
            new = SaveForLater(item_id=item, user_id=current_user.id)
            db.session.add(new)
            db.session.commit()
            added = True
    else:
        if session.get('saved') is None:
            session["saved"] = []
        saved_items = session["saved"]
        if item not in saved_items:
            saved_items.append(item)
            session["saved"] = saved_items
            session.modified = True
            added = True
    return jsonify({'added': added})


@app.route('/saved', methods=['GET', 'POST'])
def saved_for_later():
    """
    Saved page endpoint and handles user messaging seller
    ---
    get:
        parameters:
            None
        responses:
            200:
                The saved page
    post:
        parameters:
            None
        Responses:
            200:
                Messaged the seller successfully
            400:
                Missing csrf token
    """
    standalone = request.args.get('standalone')
    if request.method == 'POST' and request.form.get('email'):
        item_id = request.args.get('item')
        _item = Item.query.get_or_404(item_id)
        if current_user.last_buy_message_sent is None:
            current_user.last_buy_message_sent = datetime.utcnow()
            db.session.commit()
        else:
            time_difference = datetime.utcnow() - current_user.last_buy_message_sent
            minutes = divmod(time_difference.total_seconds(), 60)[0]
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
        savedRelationship = SaveForLater.query.filter_by(user_id=current_user.id, item_id=item_id).first()
        savedRelationship.messaged_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'origin': 'single', "messaged_date": datetime.utcnow()})
    saved_items = None
    if current_user.is_authenticated:
        saved_items = db.session.query(SaveForLater.item_id, SaveForLater.messaged_date).filter_by(
            user_id=current_user.id).order_by(SaveForLater.id.desc()).all()
    else:
        if "saved" in session:
            saved_items = session["saved"]
    items = []
    if saved_items is not None:
        for saved_item in saved_items:
            item = Item.query.get(saved_item.item_id)
            if item:
                if saved_item.messaged_date:
                    item.messaged_date = saved_item.messaged_date.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%m/%d/%Y, %H:%M:%S")
                items.append(item)
    return render_template('saved_for_later.html', title="Shopping Cart", posts=items, standalone=standalone)


@app.route('/saved/delete', methods=['POST'])
def delete_saved():
    """
    Deletes item in shopping bag
    ---
    post:
        parameters:
            None
        Responses:
            200:
                deleted successfully
            400:
                Missing csrf token
    """
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
    # flash(Markup(
    #     f'<a href="/shop/{item}">{item_name}</a> has been removed from your bag'), 'success')
    return jsonify({'saved': 'deleted'})


@app.route('/post/delete', methods=['POST'])
@login_required
def delete_item():
    """
    Deletes the users post
    ---
    post:
        parameters:
            None
        Responses:
            200:
                Post deleted successfully
            400:
                Missing csrf token
    """
    item = request.args.get('item_id')
    standalone = request.form['standalone']
    deleting_item = Item.query.get_or_404(item)
    @copy_current_request_context
    def decrement_counts(department_id, course_id, category_id):
        stats = Statistics.query.filter_by(school=session['school']).first()
        stats.current_listings -= 1
        if not category_id:
            course = ItemClass.query.filter_by(id=course_id).first()
            course.count -= 1
            department = ItemDepartment.query.filter_by(
                id=department_id).first()
            department.count -= 1
        else:
            category = ItemCategory.query.filter_by(id=category_id).first()
            category.count -= 1
            stats.non_textbooks -= 1
        db.session.commit()
    decrement_count_async = threading.Thread(name="decrement counts",
                                             target=decrement_counts,
                                             args=(deleting_item.department_id, deleting_item.class_id, deleting_item.category_id,))
    decrement_count_async.start()
    # standalone = "standlone"
    delete_images_from_s3_and_db(item)
    item_name = deleting_item.name
    current_user.listings = current_user.listings - 1
    db.session.delete(deleting_item)
    db.session.commit()
    # flash(f'Post "{item_name}" has been deleted', 'success')
    if standalone == "listings":
        return jsonify(html=listings_html(standalone))
    return jsonify({'result': 'deleted'})


def listings_html(standalone=None):
    """
    Generates html for listing page based on whether it's a standalone page or not
    ---
    parameters:
        standalone - If the page is standalone or not (if is standalone, then it doesn't
        need to request all the resources again)
    Responses:
        The html for listing page
    """
    _listings = Item.query.filter_by(user_id=current_user.id).order_by(
        Item.date_posted.asc()).all()
    form = ItemForm()
    return render_template('user_listings.html', title="Listings", listings=_listings,
                           legend='Edit', form=form, item_id=1, item=None, standalone=standalone)


@app.route('/listings')
@login_required
def listings():
    """
    The listing page endpoint
    ---
    get:
        parameters:
            None
        responses:
            200:
                The listing page
    """
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
    """
    Injects the users shopping bag item count to every request
    ---
    parameters:
        None
    Responses:
        The number of items in the users shopping bag
    """
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
    """
    Gets the html for the message buyer form
    ---
    get:
        parameters:
            None
        responses:
            200:
                The message buyer form
    """
    message_form = MessageForm()
    return render_template('message_form.html', message_form=message_form, message_title="Contact Seller", need_customization=True)


@app.route("/editform/<int:item_id>")
def get_edit_form(item_id=None):
    """
    Gets the edit form for a specific item
    ---
    parameters:
        item_id: the id of the item that we want the edit form
    responses:
        200:
            The edit form for the specific item
    """
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
    """
    Injects the list of schools to the request
    ---
    parameters:
        None
    Responses:
        200:
            The list of schools in the database
    """
    schools = db.session.query(School).all()
    return {'schools': schools}


@app.route('/setschool', methods=['POST'])
def set_school_in_session():
    """
    Sets the user's school in session
    ---
    post:
        parameters:
            None
        Responses:
            200:
                School successfully added in session
            400:
                Missing csrf token or the school is not found
    """
    state = request.form.get('state', None)
    if state == "loggout":
        logout_user()
    school = request.form.get('school', None)
    if school is None:
        flash('Invalid Behavior! No school session found.')
        return ('', 400)
    session['school'] = school
    return ('', 204)


@app.route('/contactus', methods=['GET', 'POST'])
def leave_a_message():
    """
    The contact us page endpoint, also handles users sending contact us emails
    ---
    get:
        parameters:
            None
        responses:
            200:
                The contact us page
    post:
        parameters:
            None
        Responses:
            200: 
                Message successfully sent
            400:
                Missing csrf token
    """
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


@app.route('/report', methods=['POST'])
def report_item():
    """
    Handles the user reporting a specific post as inappropriate
    ---
    post:
        parameters:
            None
        Responses:
            200: 
                Reported successfully
            400:
                Missing csrf token
    """
    item_id = request.form.get('item_id')
    item = Inappropriate.query.filter_by(id=item_id).first()
    current_user.num_reports += 1
    if item is None:
        new = Inappropriate(id=item_id, count=1)
        db.session.add(new)
        db.session.commit()
    else:
        item.count += 1
        db.session.commit()
    return 'reported'


@app.route('/unreport', methods=['POST'])
def unreport_item():
    """
    Unreports a specific post
    ---
    post:
        parameters:
            None
        Responses:
            200: 
                Unreports successfully
            400:
                Missing csrf token
    """
    item_id = request.form.get('item_id')
    item = Inappropriate.query.filter_by(id=item_id).first()
    if item is not None:
        item.count -= 1
        db.session.commit()

    return 'unreported'


@app.route('/privacy')
def private_policy():
    """
    Privacy policy page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The privacy policy page
    """
    standalone = request.args.get('standalone', None)
    return render_template('private_policy.html', standalone=standalone, title="Private Policy")


@app.route('/legal')
def terms_of_service():
    """
    Terms of service page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The TOS page
    """
    standalone = request.args.get('standalone', None)
    return render_template('terms_of_service.html', standalone=standalone, title="Terms of Service")

@app.route('/donate')
def donate():
    """
    Donate page endpoint
    ---
    parameters:
        None
    responses:
        200:
            The donate page
    """
    standalone = request.args.get('standalone', None)
    return render_template('donate.html', standalone=standalone, title="Donate")