import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
# from sassutils.wsgi import SassMiddleware

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from BookMarket import routes
