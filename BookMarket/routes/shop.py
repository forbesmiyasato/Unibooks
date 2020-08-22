from flask import render_template, request, Blueprint
from flask_login import current_user
from ..models import Item, ItemClass, ItemDepartment, ItemImage
from ..forms import EditForm, MessageForm
from .. import app, db, mail

shop_api = Blueprint('shop_api', __name__, static_folder="../static", template_folder="../template")

@shop_api.route("/shop")
def shop():
    search_term = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    order = request.args.get('order', 'desc')
    date_sorted = getattr(Item.date_posted, order)()
    departments = db.session.query(ItemDepartment).all()
    # for department in departments:
    #     # classObj = {}
    #     classes = ItemClass.query.filter_by(department_id=department.id).all()
    #     department['classes'] = classes

    if search_term:
        search_term = '%{0}%'.format(search_term)
        posts = Item.query.filter(Item.name.ilike(search_term)).order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    else:
        posts = Item.query.order_by(
            date_sorted).paginate(page=page, per_page=per_page)
    return render_template('shop.html', title='Shop', posts=posts, departments=departments)


@shop_api.route("/shop/<int:item_id>", methods=['GET', 'POST'])
def item(item_id):
    item = Item.query.get_or_404(item_id)
    edit_form = EditForm()
    message_form = MessageForm()
    if message_form.validate_on_submit and message_form.message_submit.data:
        print(item.owner.email)
        msg = Message("Message regarding " + "\"" + item.name + "\"",
                      sender="pacificubooks@gmail.com",
                      recipients=[item.owner.email], html=render_template("email.html", name=item.name, email=message_form.email.data, body=message_form.message.data))
        mail.send(msg)
    elif request.method == 'POST':
        item.name = edit_form.name.data
        item.description = edit_form.description.data
        item.user_id = current_user.id
        item.price = edit_form.price.data
        item.class_id = edit_form.item_class.data
        item.department_id = edit_form.item_department.data
        db.session.commit()
    images = ItemImage.query.filter_by(item_id=item_id).all()
    item_class = ItemClass.query.get(item.class_id)
    department = ItemDepartment.query.get(item.department_id)
    # for updating
    departments = db.session.query(ItemDepartment).all()
    department_list = [(i.id, i.department_name) for i in departments]
    edit_form.item_department.choices = department_list
    edit_form.name.data = item.name
    edit_form.description.data = item.description
    edit_form.price.data = item.price
    # for messaging
    if current_user.is_authenticated:
        message_form.email.data = current_user.email
    return render_template('single_product.html', title=item.name, item=item, images=images,
                           item_class=item_class, department=department, form=edit_form, legend="Edit",
                           message_form=message_form)


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