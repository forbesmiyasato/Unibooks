from . import db, login_manager
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False,
                           default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    items = db.relationship('Item', backref='owner', lazy=True)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    def __repr__(self):
        return f"Users('{self.username}', '{self.email}', '{self.image_file}')"


class ItemClass(db.Model):
    __tablename__ = 'itemclass'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('itemdepartment.id'), nullable=False)


class ItemDepartment(db.Model):
    __tablename__ = 'itemdepartment'
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)
    classes = db.relationship('ItemClass', backref='parent', lazy=True)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    thumbnail = db.Column(db.String, nullable=False,
                          default='No_picture_available.png')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('itemclass.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('itemdepartment.id'), nullable=False)
    images = db.relationship('ItemImage', cascade="all,delete", backref='owner', lazy=True)
    saved_by = db.relationship('SaveForLater', cascade="all, delete", passive_deletes=True)

    def __repr__(self):
        return f"Post('{self.name}', '{self.date_posted}')"


class ItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(40), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    # item_name = db.Column(db.String(100), nullable=False)


class SaveForLater(db.Model):
    __tablename__ = 'saveforlater'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


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
