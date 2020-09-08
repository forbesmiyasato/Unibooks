from flask import render_template, url_for, flash, request, redirect, Blueprint, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Message
from ..forms import RegistrationForm, LoginForm, PasswordResetForm
from .. import app, db, bcrypt, mail
from ..models import Users, School

userAuth = Blueprint('userAuth', __name__,
                     static_folder="../static", template_folder="../template")
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
salt = "email_confirm"


@userAuth.route("/register", methods=['GET', 'POST'])
def register():
    standalone = request.args.get('standalone')
    form = RegistrationForm()
    school = School.query.filter_by(id=session['school']).first()
    pattern = school.email_pattern
    placeholder = "Your " + school.name + " email address"
    error_message = "Must be a " + school.name + " email address!"
    print(pattern)
    print(form.email.data)
    print(form.password.data)
    print(error_message)
    if form.validate_on_submit():
        print(form.email.data)
        print(form.password.data)
        email = form.email.data
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        school = request.form.get('school')
        print("REGISTER_SCHOOL", school)
        user = Users(email=email, password=hashed_password, school=school)

        token = serializer.dumps(email, salt=salt)  # salt is optional
        link = url_for('userAuth.confirm_email', token=token, _external=True)
        msg = Message('Confirm Email', sender="pacificubooks@gmail.com", recipients=[email],
                      html=render_template('confirmation_email.html', email=email, link=link))

        mail.send(msg)

        db.session.add(user)
        db.session.commit()
        flash(
            f'Your account has been created, you can now login!', 'success')
        return redirect(url_for('userAuth.login'))
    return render_template('register.html', title='Register', form=form, standalone=standalone,
                           pattern=pattern, errorMessage=error_message, placeholder=placeholder)


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


@userAuth.route('/password_reset', methods=['POST'])
def send_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    email = request.form.get('email')
    print("!!!!!!!!!!!!!!!!!!", email)
    token = serializer.dumps(email, salt=salt)  # salt is optional
    link = url_for('userAuth.reset_password', token=token, _external=True)
    msg = Message('Password Reset', sender="pacificubooks@gmail.com", recipients=[email],
                  html=render_template('password_email.html', link=link))
    mail.send(msg)
    # flash(
    #     f'Confirmation email sent to {current_user.email}', 'success')
    return jsonify({'result': 'success'})


@userAuth.route('/password_reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt=salt, max_age=60)
        print(email)
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
    try:
        email = serializer.loads(token, salt=salt, max_age=60)
        print(email)
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
    return render_template('home.html')


def login_html(standalone=None):
    print("111", standalone)
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if (user and bcrypt.check_password_hash(user.password, form.password.data)):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Logged in!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password',
                  'error')
    return render_template('login.html', title='Login', form=form, standalone=standalone)


@userAuth.route("/login", methods=['GET', 'POST'])
def login():
    standalone = request.args.get('standalone')
    return login_html(standalone)


@userAuth.route("/logout")
def logout():
    logout_user()
    standalone = request.args.get('standalone')
    flash('Logged out!',
          'info')
    return render_template('home.html', title="Home", standalone=standalone)
