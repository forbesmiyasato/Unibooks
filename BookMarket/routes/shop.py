import re
from flask import render_template, request, Blueprint, jsonify, url_for
from flask_login import current_user
from flask_mail import Message
from ..models import Item, ItemClass, ItemDepartment, ItemImage
from ..forms import ItemForm, MessageForm
from .. import app, db, mail
from ..utility_funcs import delete_images_from_s3_and_db, save_images_to_db_and_s3, delete_non_remaining_images_from_s3_and_db

shop_api = Blueprint('shop_api', __name__,
                     static_folder="../static", template_folder="../template")


@shop_api.route("/shop")
def shop():
    # search_term = request.args.get('search')
    # sort_term = request.args.get('sort', 'newest')
    # if sort_term == "lowest":
    #     sort_term = "asc"
    #     sort_by = getattr(Item.price, sort_term)()
    # elif sort_term == "highest":
    #     sort_term = "desc"
    #     sort_by = getattr(Item.price, sort_term)()
    # elif sort_term == "oldest":
    #     print("!!!")
    #     sort_term = "asc"
    #     sort_by = getattr(Item.date_posted, sort_term)()
    # else:
    #     sort_term = "desc"
    #     sort_by = getattr(Item.date_posted, sort_term)()
    # page = request.args.get('page', 1, type=int)
    # per_page = request.args.get('per_page', 6, type=int)
    # print(sort_term)
    # # for department in departments:
    # #     # classObj = {}
    # #     classes = ItemClass.query.filter_by(department_id=department.id).all()
    # #     department['classes'] = classes

    # if search_term:
    #     search_term = '%{0}%'.format(search_term)
    #     posts = Item.query.filter(Item.name.ilike(search_term)).order_by(
    #         sort_by).paginate(page=page, per_page=per_page)
    # else:
    #     posts = Item.query.order_by(
    #         sort_by).paginate(page=page, per_page=per_page)
    departments = db.session.query(ItemDepartment).all()

    return render_template('shop.html', title='Shop', departments=departments)


@shop_api.route("/shop/data")
def getPosts():
    department_id = request.args.get('department')
    class_id = request.args.get('class')
    search_term = request.args.get('search')
    sort_term = request.args.get('sort', 'newest')
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
        search_term = '%{0}%'.format(search_term)
        posts = Item.query.filter(Item.name.ilike(search_term)).order_by(
            sort_by)
    elif class_id:
        posts = Item.query.filter_by(class_id=class_id).order_by(
            sort_by)
    elif department_id:
        posts = Item.query.filter_by(department_id=department_id).order_by(
            sort_by)
    else:
        posts = Item.query.order_by(
            sort_by)
    if low and high:
        low = int(low)
        high = int(high)
        posts = posts.filter(Item.price >= low).filter(Item.price <= high)
    per_page = 9
    if show_term == 'all':
        per_page = posts.count()
    posts = posts.paginate(page=page, per_page=per_page)
    return render_template("shop-main.html", posts=posts)


@shop_api.route("/shop/<int:item_id>", methods=['GET', 'POST'])
def item(item_id):
    item = Item.query.get_or_404(item_id)
    edit_form = ItemForm()
    message_form = MessageForm()
    if message_form.validate_on_submit and message_form.message_submit.data:
        print(item.owner.email)
        msg = Message("Message regarding " + "\"" + item.name + "\"",
                      sender="pacificubooks@gmail.com",
                      recipients=[item.owner.email], html=render_template("message_email.html", name=item.name, email=message_form.email.data, body=message_form.message.data))
        mail.send(msg)
    elif request.method == 'POST':
        remains = request.form.get('remaining_files')
        images = request.files.getlist("files[]")
        print(images)
        delete_non_remaining_images_from_s3_and_db(item_id, remains)
        if images:
            print(images)
            thumbnail = save_images_to_db_and_s3(images, item_id)
            if thumbnail:
                item.thumbnail = thumbnail
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        print(request.form.get('author'))
        item.isbn = request.form.get('isbn')
        item.author = request.form.get('author')
        item.user_id = current_user.id
        item.price = request.form.get('price')
        item.class_id = request.form.get('class_id')
        item.department_id = request.form.get('department_id')
        db.session.commit()
        print(item_id)
        result = {'url': url_for('shop_api.item', item_id=item_id)}
        return jsonify(result)
    images = ItemImage.query.filter_by(item_id=item_id).all()
    item_class = ItemClass.query.get(item.class_id)
    department = ItemDepartment.query.get(item.department_id)
    # for updating
    departments = db.session.query(ItemDepartment).all()
    edit_form.name.data = item.name
    edit_form.description.data = item.description
    edit_form.price.data = item.price
    edit_form.isbn.data = item.isbn
    edit_form.author.data = item.author
    edit_form.item_class.data = item_class
    edit_form.item_department.data = department
    # for messaging
    if current_user.is_authenticated:
        message_form.email.data = current_user.email
    return render_template('single_product.html', title=item.name, item=item, images=images,
                           item_class=item_class, department=department, form=edit_form, legend="Edit",
                           message_form=message_form, item_id=item_id, departments=departments)


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
    items = db.session.query(Item).all()
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
