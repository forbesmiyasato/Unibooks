# from datetime import date, timedelta
# from sqlalchemy import extract
# from flask_mail import Message
# from flask.templating import render_template
# from flask.helpers import url_for

# def query_for_reminder(app):
#     from . import db, mail
#     from .models import Users, Item
#     print("Running reminder job...")
#     with app.app_context():
#         #Set date from initial posting date to send reminder email
#         expire_date = date.today() - timedelta(days=180)
    
#         #Query for all item owners whose posts are older than expire_date (force correct datetime conversion)
#         expiring_item_ids = db.session.query(Item.id).filter(
#             extract('year',Item.date_posted)<=expire_date.year).filter(
#                 extract('month', Item.date_posted)<=expire_date.month).filter(
#                     extract('day', Item.date_posted)<=expire_date.day).all()

#         print(expiring_item_ids)
#         #Loop through each user with an expiring post and send an email reminder
#         if expiring_item_ids:
#             for item_id in expiring_item_ids:
#                 item = Item.query.get_or_404(item_id)
#                 msg = Message("Post Will Expire Soon", sender=("Unibooks", "do-not-reply@unibooks.io"), recipients=[item.owner.email], html=render_template("message_email.html", name=item.name, email="do-not-reply@unibooks.io", 
#                     body="You have an item for sale that will expire soon."))
#                 mail.send(msg)