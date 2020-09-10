from . import db, login_manager
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), unique=True, nullable=False)
    image_file = db.Column(db.String(50), nullable=False,
                           default='default.jpg')
    password = db.Column(db.String(100), nullable=False)
    items = db.relationship('Item', backref='owner', lazy=True)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    listings = db.Column(db.Integer, default=0)
    school = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    last_confirm_email_sent = db.Column(db.DateTime, nullable=True,
                                        default=datetime.utcnow)

    def __repr__(self):
        return f"Users('{self.username}', '{self.email}', '{self.image_file}')"


class ItemClass(db.Model):
    __tablename__ = 'itemclass'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey(
        'itemdepartment.id'), nullable=False)

class ItemCategory(db.Model):
    __tablename__ = 'itemcategory'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(20), nullable=True)
    school = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
class ItemDepartment(db.Model):
    __tablename__ = 'itemdepartment'
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(20), nullable=True)
    classes = db.relationship('ItemClass', backref='parent', lazy=True)
    school = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    thumbnail = db.Column(db.String, nullable=False,
                          default='No_picture_available.png')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey(
        'itemclass.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey(
        'itemdepartment.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey(
        'itemcategory.id'), nullable=True)
    images = db.relationship(
        'ItemImage', cascade="all,delete", backref='owner', lazy=True)
    saved_by = db.relationship(
        'SaveForLater', cascade="all, delete", passive_deletes=True)
    isbn = db.Column(db.String(15), nullable=True)
    author = db.Column(db.String(30), nullable=True)
    school = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.name}', '{self.date_posted}')"


class ItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    image_name = db.Column(db.String(30), nullable=True)
    image_size = db.Column(db.String(20), nullable=True)


class SaveForLater(db.Model):
    __tablename__ = 'saveforlater'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey(
        'item.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    departments = db.relationship(
        'ItemDepartment', backref='parent', lazy=True)
    items = db.relationship('Item', backref='parent', lazy=True)
    users = db.relationship('Users', backref='parent', lazy=True)
    email_pattern = db.Column(db.String(150), nullable=True)


# class PastItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False,
#                             default=datetime.utcnow)
#     description = db.Column(db.Text, nullable=False)
#     price = db.Column(db.DECIMAL(10, 2), nullable=False)
#     thumbnail = db.Column(db.String, nullable=False,
#                           default='No_picture_available.png')
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     class_id = db.Column(db.Integer, db.ForeignKey('itemclass.id'), nullable=False)
#     department_id = db.Column(db.Integer, db.ForeignKey('itemdepartment.id'), nullable=False)
#     images = db.relationship('ItemImage', cascade="all,delete", backref='owner', lazy=True)
#     saved_by = db.relationship('SaveForLater', cascade="all, delete", passive_deletes=True)

#     def __repr__(self):
#         return f"Post('{self.name}', '{self.date_posted}')"
