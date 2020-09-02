import os
import secrets
import boto3
from .models import ItemImage
from . import db, S3_BUCKET
# Utility functions
def save_images_to_db_and_s3(form_images, item_id):
    thumbnail = None
    for index, images in enumerate(form_images):
        if images:
            # print(images.filesize)
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(images.filename)
            picture_fn = random_hex + f_ext
            picture_fn = picture_fn[:100] #only get the first 100 chars, db limit for image_file is 100
            if (index == 0):
                thumbnail = picture_fn
            # picture_path = os.path.join(
            #     app.root_path, 'static/item_pics', picture_fn)
            # output_size = (183, 195)
            # # output_resolution = (1000, 1000)
            # resizedImage = Image.open(images)
            # # resizedImage.thumbnail(output_resolution)
            # resizedImage = resizedImage.resize(output_size, Image.ANTIALIAS)
            # resizedImage.save(picture_path)
            s3_resource = boto3.resource('s3')
            my_bucket = s3_resource.Bucket(S3_BUCKET)
            my_bucket.Object(picture_fn).put(Body=images)
            image_name = images.filename[:30]
            images.seek(0, os.SEEK_END)
            size = images.tell()
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