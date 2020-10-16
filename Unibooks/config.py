import os


class Config:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    ACL = 'public-read'
    S3_BUCKET = os.environ.get('S3_STORAGE_BUCKET')
    FLASKS3_REGION = os.environ.get('FLASKS3_REGION')
