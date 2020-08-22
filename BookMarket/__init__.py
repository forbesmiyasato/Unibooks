import os
import boto3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_mail import Mail
# from flask.ext.session import Session

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_DEBUG'] =
app.config['MAIL_USERNAME'] = 'pacificubooks@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PW')
app.config['MAIL_DEFAULT_SENDER'] = 'pacificubooks@gmail.com'
# app.config['MAIL_MAX_EMAILS'] =
# app.config['MAIL_SUPPRESS_SEND'] =
# app.config['MAIL_ASCII_ATTACHMENTS'] =
mail = Mail(app)

# Session(app)

# S3 configurations
S3_BUCKET = os.getenv('S3_STORAGE_BUCKET')
S3_KEY = os.getenv('AWS_ACCESS_KEY_ID')
S3_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET
)


if __name__ == '__main__':
    app.run(debug=True)

# load dotenv in the base root
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from . import route
