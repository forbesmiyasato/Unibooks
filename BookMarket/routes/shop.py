import re
import threading
from flask import render_template, request, Blueprint, jsonify, url_for, flash, session, redirect, current_app
from flask_login import current_user
from flask_mail import Message
from ..models import Item, ItemClass, ItemDepartment, ItemImage, School, ItemCategory
from ..forms import ItemForm, MessageForm
from .. import app, db, mail
from ..utility_funcs import delete_images_from_s3_and_db, save_images_to_db_and_s3, delete_non_remaining_images_from_s3_and_db, send_message

shop_api = Blueprint('shop_api', __name__,
                     static_folder="../static", template_folder="../template")


@shop_api.route("/shop")
def shop():
    standalone = request.args.get('standalone')
    if session.get('school') is None:
        flash("School Session Needed", 'error')
        return redirect(url_for('home'))
        # return jsonify(state="no school in session")
    school = session['school']
    departments = ItemDepartment.query.filter_by(school=school).all()
    categories = ItemCategory.query.filter_by(school=session['school']).all()

    return render_template('shop.html', title='Shop', departments=departments, standalone=standalone, categories=categories)


@shop_api.route("/shop/data")
def getPosts():
    num_results = 0
    department_id = request.args.get('department')
    category = request.args.get('nonbook')
    print(category)
    department = None
    class_id = request.args.get('class')
    course = None
    search_term = request.args.get('search', None)
    sort_term = request.args.get('sort', 'none')
    search = None
    filter_term = request.args.get('filter', '0+99999')
    show_term = request.args.get('show', None)
    low = None
    high = None
    print(filter_term)
    if filter_term and re.match("(^0\\+25$|^25\\+50$|^50\\+100$|^100\\+150$|^150\\+99999$)", filter_term):
        print("matched")
        split = filter_term.split('+')
        low = split[0]
        high = split[1]

    original_sort_term = sort_term
    print(session.get('school') is None)
    if session.get('school') is None:
        return jsonify(error='no school in session')
    posts = Item.query.filter_by(school=session['school'])
    print(posts)
    if sort_term == "lowest":
        sort_term = "asc"
        sort_by = getattr(Item.price, sort_term)()
    elif sort_term == "highest":
        sort_term = "desc"
        sort_by = getattr(Item.price, sort_term)()
    elif sort_term == "oldest":
        sort_term = "asc"
        sort_by = getattr(Item.date_posted, sort_term)()
    else:
        sort_term = "desc"
        sort_by = getattr(Item.date_posted, sort_term)()
    page = request.args.get('page', 1, type=int)
    if search_term:
        search = search_term
        search_term = '%{0}%'.format(search_term)
        posts = posts.filter(Item.name.ilike(search_term)).order_by(
            sort_by)
        num_results = posts.count()
    elif class_id:
        posts = posts.filter_by(class_id=class_id).order_by(
            sort_by)
        course = ItemClass.query.filter_by(id=class_id).first()
        department = ItemDepartment.query.filter_by(
            id=course.department_id).first()
        course = {"name": course.class_name, "id": course.id}
        department = {"name": department.department_name, "id": department.id}
    elif department_id:
        posts = posts.filter_by(department_id=department_id).order_by(
            sort_by)
        department = ItemDepartment.query.filter_by(id=department_id).first()
        department = {"name": department.department_name, "id": department.id}
    elif category:
        if category == "all":
            posts = posts.filter(Item.category_id != None).order_by(
                sort_by)
        else:
            posts = posts.filter_by(category_id=category).order_by(
            sort_by)
    else:
        posts = posts.order_by(
            sort_by)
    if low and high:
        low = int(low)
        high = int(high)
        posts = posts.filter(Item.price >= low).filter(Item.price <= high)
    per_page = 12
    if show_term == 'all':
        per_page = posts.count()
    posts = posts.paginate(page=page, per_page=per_page)
    return jsonify(html=render_template("shop-main.html", posts=posts),
                   department=department, course=course, sort=original_sort_term, filter=filter_term, show=show_term,
                   search=search, numResults=num_results)


def item_html(item_id, standalone=None):
    _item = Item.query.get_or_404(item_id)
    edit_form = ItemForm()
    message_form = MessageForm()
    print(request.form.get('email'))
    if request.method == 'POST' and request.form.get('email'):
        print(_item.owner.email)
        standalone = "standalone"
        msg = Message("Message regarding " + "\"" + _item.name + "\"",
                      sender=("Unibooks", 'unibooks@unibooks.io'),
                      recipients=[_item.owner.email], html=render_template("message_email.html", name=_item.name,
                                                                           email=request.form.get('email'), body=request.form.get('message')))
        sender = threading.Thread(name="mail_sender", target=send_message, args=(current_app._get_current_object(), msg,))
        sender.start()
        # flash(
        # f'Message sent! The seller will contact you soon.', 'success')
    elif request.method == 'POST' and standalone != 'notfromnewitem':
        standalone = "standalone"
        remains = request.form.get('remaining_files')
        images = request.files.getlist("files[]")
        print(images)
        print(remains)
        delete_non_remaining_images_from_s3_and_db(item_id, remains)
        print("11111", _item.images)
        print("2222", _item.thumbnail)
        if not _item.images:
            _item.thumbnail = "No_picture_available.png"
        if images:
            prevImageCount = _item.images
            print(images)
            thumbnail = save_images_to_db_and_s3(images, item_id)
            if thumbnail and not prevImageCount:
                _item.thumbnail = thumbnail
        _item.name = request.form.get('name')
        _item.description = request.form.get('description')
        print(request.form.get('author'))
        _item.isbn = request.form.get('isbn')
        _item.author = request.form.get('author')
        _item.user_id = current_user.id
        _item.price = request.form.get('price')
        _item.class_id = request.form.get('class_id')
        _item.category_id = request.form.get('category_id')
        _item.department_id = request.form.get('department_id')
        db.session.commit()
        print(item_id)
        # result = {'url': url_for('shop_api.item', item_id=item_id)}
    images = ItemImage.query.filter_by(item_id=item_id).all()
    item_class = ItemClass.query.get(_item.class_id)
    department = ItemDepartment.query.get(_item.department_id)
    # for updating
    departments = ItemDepartment.query.filter_by(school=session['school']).all()
    edit_form.name.data = _item.name
    edit_form.description.data = _item.description
    edit_form.price.data = _item.price
    edit_form.isbn.data = _item.isbn
    edit_form.author.data = _item.author
    edit_form.item_class.data = item_class
    edit_form.item_department.data = department
    print("1", item_class)
    print("2", department)
    print("3", _item.category_id)
    isBook = True if _item.category_id is None else False
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    category = ItemCategory.query.get(_item.category_id)
    print(isBook)
    # for messaging
    if current_user.is_authenticated:
        message_form.email.data = current_user.email
    return render_template('single_product.html', title=_item.name, item=_item, images=images,
                           item_class=item_class, department=department, form=edit_form, legend="Edit",
                           message_form=message_form, item_id=item_id, departments=departments, standalone=standalone,
                           message_title="Message Seller", isBook=isBook, categories=categories, category=category)


@shop_api.route("/shop/<int:item_id>", methods=['GET', 'POST'])
def item(item_id):
    standalone = request.args.get('standalone', None)
    if request.method == 'POST':
        print("YES!")
        return jsonify({'html': (item_html(item_id, standalone)), 'url': url_for('shop_api.item', item_id=item_id), 'origin': 'single'})
    return item_html(item_id, standalone)


@shop_api.route("/shop/class/<int:class_id>")
def items_for_class(class_id):
    search_term = request.args.get('search')
    per_page = request.args.get('per_page', 6, type=int)
    page = request.args.get('page', 1, type=int)
    departments = db.session.query(ItemDepartment).all()
    order = request.args.get('order', 'desc')
    date_sorted = getattr(Item.date_posted, order)()
    item_class = ItemClass.query.get_or_404(class_id)
    if search_term:
        search_term = '%{0}%'.format(search_term)
        posts = Item.query.filter(Item.name.ilike(search_term)).filter_by(class_id=class_id).order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    else:
        posts = Item.query.filter_by(class_id=class_id).order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    return render_template('shop_class.html', title='Shop', posts=posts, departments=departments, class1=item_class)


@shop_api.route("/shop/department/<int:department_id>")
def items_for_department(department_id):
    search_term = request.args.get('search')
    per_page = request.args.get('per_page', 6, type=int)
    page = request.args.get('page', 1, type=int)
    departments = db.session.query(ItemDepartment).all()
    order = request.args.get('order', 'desc')
    date_sorted = getattr(Item.date_posted, order)()
    department = ItemDepartment.query.get_or_404(department_id)
    if search_term:
        search_term = '%{0}%'.format(search_term)
        posts = Item.query.filter(Item.name.ilike(search_term)).filter_by(department_id=department_id).order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    else:
        posts = Item.query.filter_by(department_id=department_id).order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    return render_template('shop_department.html', title='Shop', posts=posts, departments=departments, department=department)


@shop_api.context_processor
def get_totals_depts():
    items = db.session.query(Item).filter(Item.school==session['school']).all()
    depObj = {}
    classObj = {}

    if items:
        for item in items:
            if item.department_id not in depObj:
                depObj[item.department_id] = 1
            else:
                depObj[item.department_id] += 1
            if item.class_id not in classObj:
                classObj[item.class_id] = 1
            else:
                classObj[item.class_id] += 1

    return {'depObj': depObj, 'classObj': classObj, 'items': items}
