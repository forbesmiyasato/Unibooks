import re
import threading
import concurrent.futures
import time
from datetime import datetime
from flask import render_template, request, Blueprint, jsonify, url_for, flash, session, redirect, current_app
from flask_login import current_user
from flask_mail import Message
from ..models import Item, ItemClass, ItemDepartment, ItemImage, School, ItemCategory, Statistics
from ..forms import ItemForm, MessageForm
from .. import app, db, mail
from ..utility_funcs import (delete_images_from_s3_and_db, save_images_to_db_and_s3, 
delete_non_remaining_images_from_s3_and_db, send_message, insert_space_before_first_number)

shop_api = Blueprint('shop_api', __name__,
                     static_folder="../static", template_folder="../template")


@shop_api.route("/shop")
def shop():
    standalone = request.args.get('standalone')
    if session.get('school') is None:
        flash("School Session Needed", 'error')
        return redirect(url_for('home'))
    school = session['school']
    departments = ItemDepartment.query.filter_by(school=school).order_by(
            ItemDepartment.abbreviation).all()
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    stats = Statistics.query.first()
    current_listings = stats.current_listings
    total_category = stats.non_textbooks
    return render_template('shop.html', title='Shop', departments=departments, standalone=standalone,
    categories=categories, all=current_listings, totalCategory=total_category)


def findMatchingCourse(courseSearch):
    return ItemClass.query.filter_by(school=session['school']).filter(ItemClass.abbreviation.ilike(courseSearch)).first()

def findMatchingDepartment(search_term):
    return ItemDepartment.query.filter_by(school=session['school']).filter((ItemDepartment.department_name.ilike(search_term) | (ItemDepartment.abbreviation.ilike(search_term)))).first()

def findMatchingCategory(search_term):
    return ItemCategory.query.filter_by(school=session['school']).filter((ItemCategory.category_name.ilike(search_term))).first()

@shop_api.route("/shop/data")
def getPosts():
    num_results = 0
    department_id = request.args.get('department')
    category = request.args.get('nonbook')
    department = None
    class_id = request.args.get('class')
    course = None
    search_term = request.args.get('search', None)
    sort_term = request.args.get('sort', 'none')
    search = None
    filter_term = request.args.get('filter', '0+99999')
    show_term = request.args.get('show', None)
    matchCourse = None
    matchDepartment = None
    match_category = None
    low = None
    high = None
    if filter_term and re.match("(^0\\+25$|^25\\+50$|^50\\+100$|^100\\+150$|^150\\+99999$)", filter_term):
        split = filter_term.split('+')
        low = split[0]
        high = split[1]

    original_sort_term = sort_term
    if session.get('school') is None:
        return jsonify(error='no school in session')
    posts = Item.query.filter_by(school=session['school'])
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
        matchDepartment = findMatchingDepartment(search_term) #want to match exact whole word for deparments
        search_term = '%{0}%'.format(search_term)
        posts = posts.filter(Item.name.ilike(search_term)).order_by(
            sort_by)
        courseSearch = insert_space_before_first_number(search_term)
        matchCourse = findMatchingCourse(courseSearch)
        match_category = findMatchingCategory(search_term)
        num_results = posts.count()
    elif class_id:
        posts = posts.filter_by(class_id=class_id).order_by(
            sort_by)
        course = ItemClass.query.filter_by(id=class_id).first()
        department = ItemDepartment.query.filter_by(
            id=course.department_id).first()
        course = {"short": course.abbreviation, "id": course.id, "long": course.class_name}
        department = {"short": department.abbreviation, "id": department.id}
    elif department_id:
        posts = posts.filter_by(department_id=department_id).order_by(
            sort_by)
        department = ItemDepartment.query.filter_by(id=department_id).first()
        department = {"short": department.abbreviation, "id": department.id, "long": department.department_name}
    elif category:
        if category == "all":
            posts = posts.filter(Item.category_id != None).order_by(
                sort_by)
            category = {"short": "Non-Textbooks", "long": "All Non-Textbooks"}
        else:
            posts = posts.filter_by(category_id=category).order_by(
            sort_by)
            category = ItemCategory.query.filter_by(id=category).first()
            category = {"short": category.abbreviation, "id": category.id, "long": category.category_name}
    else:
        posts = posts.order_by(
            sort_by)
    if low and high:
        low = int(low)
        high = int(high)
        posts = posts.filter(Item.price >= low).filter(Item.price <= high)
    per_page = 9
    if show_term == 'all':
        per_page = posts.count()
    posts = posts.paginate(page=page, per_page=per_page)
    return jsonify(html=render_template("shop-main.html", posts=posts, foundCourse=matchCourse, foundDepartment=matchDepartment, foundCategory=match_category),
                   department=department, course=course, sort=original_sort_term, filter=filter_term, show=show_term,
                   search=search, numResults=num_results, category=category)


def item_html(item_id, _item, standalone=None):
    edit_form = ItemForm()
    message_form = MessageForm()
    if request.method == 'POST' and standalone != 'notfromnewitem':
        standalone = "standalone"
        old_course = _item.class_id
        old_department = _item.department_id
        old_category = _item.category_id
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
        _item.category_id = request.form.get('category_id')
        _item.department_id = request.form.get('department_id')
        if not _item.category_id:
            course = ItemClass.query.filter_by(id=_item.class_id).first()
            course.count += 1
            department = ItemDepartment.query.filter_by(
                id=_item.department_id).first()
            department.count += 1
            prev_course = ItemClass.query.filter_by(id=old_course).first()
            prev_course.count -= 1
            prev_department = ItemDepartment.query.filter_by(id=old_department).first()
            prev_department.count -= 1
        else:
            category = ItemCategory.query.filter_by(id=_item.category_id).first()
            category.count += 1
            prev_category = ItemCategory.query.filter_by(id=old_category).first()
            prev_category.count -= 1
        db.session.commit()
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
    isBook = True if _item.category_id is None else False
    categories = ItemCategory.query.filter_by(school=session['school']).all()
    category = ItemCategory.query.get(_item.category_id)
    # for messaging
    if current_user.is_authenticated:
        message_form.email.data = current_user.email
    return render_template('single_product.html', title=_item.name, item=_item, images=images,
                           item_class=item_class, department=department, form=edit_form, legend="Edit",
                           message_form=message_form, item_id=item_id, departments=departments, standalone=standalone,
                           message_title="Message Seller", isBook=isBook, categories=categories, category=category)


@shop_api.route("/shop/<int:item_id>", methods=['GET', 'POST'])
def item(item_id):
    _item = Item.query.get_or_404(item_id)
    standalone = request.args.get('standalone', None)
    if request.method == 'POST':
        if request.method == 'POST' and request.form.get('email'):
            standalone = "standalone"
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
            sender = threading.Thread(name="mail_sender", target=send_message, args=(current_app._get_current_object(), msg,))
            sender.start()
            return jsonify({'origin': 'single'})
        else:    
            return jsonify({'html': (item_html(item_id, _item, standalone)), 'url': url_for('shop_api.item', item_id=item_id)})
    return item_html(item_id, _item, standalone)


# @shop_api.context_processor
# def get_totals_depts():
#     items = db.session.query(Item).filter(Item.school==session['school']).all()
#     depObj = {}
#     classObj = {}
#     categoryObj = {}
#     total_category = 0
#     if items:
#         for item in items:
#             if item.category_id == None:
#                 if item.department_id not in depObj:
#                     depObj[item.department_id] = 1
#                 else:
#                     depObj[item.department_id] += 1
#                 if item.class_id not in classObj:
#                     classObj[item.class_id] = 1
#                 else:
#                     classObj[item.class_id] += 1
#             else:
#                 if item.category_id not in categoryObj:
#                     categoryObj[item.category_id] = 1
#                     total_category += 1
#                 else:
#                     categoryObj[item.category_id] += 1
#                     total_category += 1

#     return {'depObj': depObj, 'classObj': classObj, 'items': items, 'categoryObj': categoryObj, 'totalCategory': total_category}
