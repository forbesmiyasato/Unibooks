import threading
import re
from datetime import datetime
from flask import render_template, url_for, flash, request, redirect, Blueprint, jsonify, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Message
from ..forms import RegistrationForm, LoginForm, PasswordResetForm
from .. import app, db, bcrypt, mail
from ..models import Users, School
from ..utility_funcs import send_message

userAuth = Blueprint('userAuth', __name__,
                     static_folder="../static", template_folder="../template")
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
salt = "email_confirm"


@userAuth.route("/register", methods=['GET', 'POST'])
def register():
    """
    The register page endpoint
    ---
    get:
        parameters:
            None
        responses:
            200:
                The register page html
    post:
        parameters:
            None
        responses:
            301: redirects to login if registered successfully
            and refreshes page if registering with invalid email domain
    """
    standalone = request.args.get('standalone')
    form = RegistrationForm()
    if session.get('school') is None:
        return render_template('register.html', title='Register', form=form)
    school = School.query.filter_by(id=session['school']).first()
    pattern = school.email_pattern
    placeholder = "Your " + school.name + " email address"
    error_message = "Must be a " + school.name + " email address!"
    if form.validate_on_submit():
        email = form.email.data
        if re.match(pattern, email) is None:
            flash('Invalid Email Domain', 'Error')
            return redirect(url_for('userAuth.register'))
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        school = request.form.get('school')
        user = Users(email=email, password=hashed_password, school=school)

        token = serializer.dumps(email, salt=salt)  # salt is optional
        link = url_for('userAuth.confirm_email', token=token, _external=True)
        msg = Message('Confirm Email', sender=("Unibooks", "do-not-reply@unibooks.io"), recipients=[email],
                      html=render_template('confirmation_email.html', email=email, link=link))
        sender = threading.Thread(name="mail_sender", target=send_message, args=(
            current_app._get_current_object(), msg,))
        sender.start()
        db.session.add(user)
        db.session.commit()
        flash(
            f'Your account has been created! please check your inbox to confirm your account.', 'success')
        return redirect(url_for('userAuth.login'))
    return render_template('register.html', title='Register', form=form, standalone=standalone,
                           pattern=pattern, errorMessage=error_message, placeholder=placeholder)


@userAuth.route('/confirm_email/send/', methods=['POST'])
def send_confirm_email():
    """
    End point which sends the confirmation email
    ---
    post:
        parameters:
            None
        responses:
            200:
                JSON indicating sending confirmation email too frequently or sent successfully
            301: 
                Redirects to home if user is not logged in or account isn't confirmed
    """
    if current_user.last_confirm_email_sent:
        time_difference = datetime.utcnow() - current_user.last_confirm_email_sent
        minutes = divmod(time_difference.total_seconds(), 60)[0]
        print("TIME", minutes)
        if minutes < 60.0:
            return jsonify({"result": "failure-too-soon"})
    if current_user.is_authenticated is False:
        flash('Your must be logged in to send confirmation emails', 'error')
        return redirect(url_for('home'))
    if current_user.confirmed:
        flash('Your account is already confirmed.', 'info')
        return redirect(url_for('home'))
    email = current_user.email
    token = serializer.dumps(email, salt=salt)  # salt is optional
    link = url_for('userAuth.confirm_email', token=token, _external=True)
    msg = Message('Confirm Email', sender=("Unibooks", "do-not-reply@unibooks.io"), recipients=[email],
                  html=render_template('confirmation_email.html', email=email, link=link))
    sender = threading.Thread(name="mail_sender", target=send_message, args=(
        current_app._get_current_object(), msg,))
    sender.start()
    current_user.last_confirm_email_sent = datetime.utcnow()
    db.session.commit()
    # flash(
    #     f'Confirmation email sent to {current_user.email}', 'success')
    return jsonify({"result": "success"})


@userAuth.route('/password_reset', methods=['POST'])
def send_password_reset():
    """
    End point which sends password reset email
    ---
    post:
        parameters:
            None
        responses:
            200:
                JSON indicating current user doesn't exist or reset email sent successfully
            301: 
                Redirects to home if user if user is already authenticated
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    email = request.form.get('email')
    user = Users.query.filter_by(email=email).first()
    if user is None:
        return jsonify({'result': 'nouser'})
    token = serializer.dumps(email, salt=salt)  # salt is optional
    link = url_for('userAuth.reset_password', token=token, _external=True)
    msg = Message('Password Reset', sender=("Unibooks", "do-not-reply@unibooks.io"), recipients=[email],
                  html=render_template('password_email.html', link=link))
    sender = threading.Thread(name="mail_sender", target=send_message, args=(
        current_app._get_current_object(), msg,))
    sender.start()
    # flash(
    #     f'Confirmation email sent to {current_user.email}', 'success')
    return jsonify({'result': 'success'})


@userAuth.route('/password_reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    End point which handles the password resetting
    ---
    get:
        parameters:
            token: the secret token sent for validation
        responses:
            200:
                The password reset page/form
            301: 
                Redirects to home if token is invalid or expired
    post:
        parameters:
            None
        responses:
            301: 
                Redirects to home after user submits new password
    """
    try:
        email = serializer.loads(token, salt=salt, max_age=3600)
    except SignatureExpired:
        flash("The token is expired! Click \"Forgot password\" below to send another one.", 'error')
        return redirect(url_for('userAuth.login'))
    except BadTimeSignature:
        flash("Invalid Token!", 'error')
        return redirect(url_for('home'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=email).first()
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Password reset! You can now sign in with your new password', 'success')
        return redirect(url_for('userAuth.login'))
    return render_template('password_reset.html', form=form)


@userAuth.route('/confirm_email/<token>')
def confirm_email(token):
    """
    End point which handles the user account confirming
    ---
    get:
        parameters:
            token: the secret token sent for validation
        responses:
            301: 
                Redirects to home regardless
    """
    try:
        email = serializer.loads(token, salt=salt, max_age=3600)
    except SignatureExpired:
        # return '<h1>The token is expired!<h1>'
        flash(
            "The token is expired! Login and go to accounts to send another one.", 'error')
        return redirect(url_for('userAuth.login'))
    except BadTimeSignature:
        flash("Invalid Token!", 'error')
        return redirect(url_for('home'))
    flash(f'Email confirmed! Welcome!', 'success')
    user = Users.query.filter_by(email=email).first()
    login_user(user)
    user.confirmed = True
    db.session.commit()
    return redirect(url_for('home'))


def login_html(standalone=None, pattern=None, placeholder=None, error_message=None):
    """
    End point which handles the password resetting
    ---
    parameters:
        standalone: whether this html is standalone or not
        pattern: The school's email pattern
        placeholder: placeholder text for email field
        error_message: error message to display if user inputs invalid email
    return: 
        login page html
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if (user and bcrypt.check_password_hash(user.password, form.password.data)):
            print(form.remember.data)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if current_user.confirmed:
                flash('Logged in!', 'success')
            else:
                flash("Your account isn't confirmed yet! You can't sell or message until your account is confirmed.", 'info')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'error')
    return render_template('login.html', title='Login', form=form, standalone=standalone,
                           pattern=pattern, placeholder=placeholder, error_message=error_message)


@userAuth.route("/login", methods=['GET', 'POST'])
def login():
    """
    The login page endpoint
    ---
    get:
        parameters:
            None
        responses:
            200:
                The login page html
    post:
        parameters:
            None
        responses:
            301: 
                Redirects to next page (page that brought user to login page)
                or home if logged in successfully
    """
    standalone = request.args.get('standalone')
    if session.get('school') is None:
        return login_html()
    school = School.query.filter_by(id=session['school']).first()
    pattern = school.email_pattern
    placeholder = "e.g. xxxx@" + school.email_domain
    error_message = "Must be a " + school.name + " email address!"
    return login_html(standalone, pattern, placeholder, error_message)


@userAuth.route("/logout")
def logout():
    """
    End point to log out the current user
    ---
    get:
        parameters:
            None
        responses:
            301: 
                Redirects to home
    """
    logout_user()
    standalone = request.args.get('standalone')
    flash('Logged out!',
          'info')
    # return render_template('home.html', title="Home", standalone=standalone)
    return redirect(url_for('home'))
