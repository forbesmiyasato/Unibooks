import os
import secrets
import boto3
import io
from PIL import Image, ImageOps
from .models import ItemImage
from . import db, S3_BUCKET, mail
# Utility functions
def save_images_to_db_and_s3(form_images, item_id):
    thumbnail = None
    for index, images in enumerate(form_images):
        if images:
            # print(images.filesize)
            print(images)
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(images.filename)
            picture_fn = random_hex + f_ext
            picture_fn = picture_fn[:100] #only get the first 100 chars, db limit for image_file is 100
            if (index == 0):
                thumbnail = picture_fn
            # picture_path = os.path.join(
            #     app.root_path, 'static/item_pics', picture_fn)
            image = Image.open(images)
            image_format = image.format
            print(image.size)
            if image.height > 600 or image.width > 600:
                output_size = (600, 600)
                image = image.resize(output_size, Image.ANTIALIAS)
            in_mem_file = io.BytesIO()
            image = ImageOps.exif_transpose(image)
            image.save(in_mem_file, optimize=True, format=image_format)
            # # output_resolution = (1000, 1000)
            # resizedImage = Image.open(images)
            # # resizedImage.thumbnail(output_resolution)
            s3_resource = boto3.resource('s3')
            my_bucket = s3_resource.Bucket(S3_BUCKET)
            print(images)
            my_bucket.Object(picture_fn).put(Body=in_mem_file.getvalue())
            image_name = images.filename[:30]
            # images.seek(0, os.SEEK_END)
            size = in_mem_file.tell()
            print(size)
            newImage = ItemImage(item_id=item_id, image_file=picture_fn, image_name=image_name, image_size=size)
            db.session.add(newImage)
            db.session.commit()
    return thumbnail
    # #remove use previous profile pic in file system so it doesn't get overloaded
    # if (current_user.image_file != 'default.jpg'):
    #     current_picture_path = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
    #     if os.path.exists(current_picture_path):
    #         os.remove(current_picture_path)


def delete_all_user_listings__images_from_s3_and_db(user):
    for item in user.items:
        delete_images_from_s3_and_db(item.id)
    db.session.commit()

def delete_images_from_s3_and_db(item_id):
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    images = ItemImage.query.filter_by(item_id=item_id).all()
    for image in images:
        print(image)
        print(image.image_file)
        db.session.delete(image)
        my_bucket.Object(image.image_file).delete()

def delete_non_remaining_images_from_s3_and_db(item_id, remains):
    print(remains)
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    images = ItemImage.query.filter_by(item_id=item_id).all()
    for image in images:
        print(image)
        print(image.image_file)
        if image.image_file not in remains:
            db.session.delete(image)
            my_bucket.Object(image.image_file).delete()



def send_message(app, message):
    with app.app_context():
        mail.send(message)


def insert_space_before_first_number(string):
    for i, char in enumerate(string):
        if char.isdigit():
            break
    return string[:i] + ' ' + string[i:]