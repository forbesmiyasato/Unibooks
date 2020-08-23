from flask import render_template, url_for, flash, request, redirect, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Message
from ..forms import RegistrationForm, LoginForm
from .. import app, db, bcrypt, mail
from ..models import Users

userAuth = Blueprint('userAuth', __name__,
                     static_folder="../static", template_folder="../template")
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
salt = "email_confirm"


@userAuth.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = Users(username=form.username.data,
                     email=email, password=hashed_password)

        token = serializer.dumps(email, salt=salt)  # salt is optional
        link = url_for('userAuth.confirm_email', token=token, _external=True)
        msg = Message('Confirm Email', sender="pacificubooks@gmail.com", recipients=[email],
                      html=render_template('confirmation_email.html', email=email, link=link))

        mail.send(msg)

        db.session.add(user)
        db.session.commit()
        flash(
            f'Hi {form.username.data}! Your account has been created, you can now login!', 'success')
        return redirect(url_for('userAuth.login'))
    return render_template('register.html', title='Register', form=form)


@userAuth.route('/confirm_email/send/')
@login_required
def send_confirm_email():
    email = current_user.email
    token = serializer.dumps(email, salt=salt)  # salt is optional
    link = url_for('userAuth.confirm_email', token=token, _external=True)
    msg = Message('Confirm Email', sender="pacificubooks@gmail.com", recipients=[email],
                  html=render_template('confirmation_email.html', email=email, link=link))
    mail.send(msg)
    flash(
        f'Confirmation email sent to {current_user.email}', 'success')
    return redirect(url_for('account'))


@userAuth.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt=salt, max_age=60)
        print(email)
    except SignatureExpired:
        return '<h1>The token is expired!<h1>'
    except BadTimeSignature:
        return '<h1>Invalid Token!<h1>'
    flash(f'Email confirmed! Welcome!', 'success')
    user = Users.query.filter_by(email=email).first()
    login_user(user)
    user.confirmed = True
    db.session.commit()
    return render_template('home.html')


@userAuth.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if (user and bcrypt.check_password_hash(user.password, form.password.data)):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'danger')
    return render_template('login.html', title='Login', form=form)


@userAuth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
