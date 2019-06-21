from app import app, db
from app.forms import LoginForm, RegistrationForm, FileUploadForm
from app.models import User, File
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from io import BytesIO
import datetime


#
@app.route('/')
@app.route('/index', methods=['GET'])
@login_required
def index():
    files = File.query.filter_by(user_id=current_user.id)
    for file in files:
        if expired(file.datetime):
            db.session.delete(file)
            db.session.commit()
    files = File.query.filter_by(user_id=current_user.id)
    return render_template('index.html', title='', files=files)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('congratulations, you\'re now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.is_anonymous:
        return redirect(url_for('login'))
    form = FileUploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        date = form.date.data
        time = form.time.data
        datetime = datetime_convert(date, time)
        new_file = File(filename=file.filename, data=file.read(),
                        datetime=datetime, user_id=current_user.id)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        flash('This file format is not allowed')
    return render_template('upload.html', title='File upload', form=form)


@app.route('/file/<filename>/<file_id>', methods=['GET'])
@login_required
def file(filename, file_id):
    if current_user.is_anonymous:
        return redirect(url_for('login'))
    f = File.query.filter_by(filename=filename, user_id=current_user.id, id=file_id).first()
    if expired(f.datetime):
        return render_template('404.html', title='404 Not Found')
    return render_template('file.html', title=f.filename, datetime=f.datetime, id=f.id)


@app.route('/file/download/<file_id>/')
@login_required
def download(file_id):
    f = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    return send_file(BytesIO(f.data), attachment_filename=f.filename, as_attachment=True)


@app.route('/404')
def not_found():
    return render_template('404.html', title='Error 404')



def datetime_convert(date, time):
    d = str(date.strftime('%Y-%m-%d')).split('-')
    t = str(time).split(':')
    array = d + t
    for x in range(0, len(array)):
        array[x] = int(array[x])
    return datetime.datetime(*array)



def expired(expiration_time):
    current_time = datetime.datetime.now()
    if expiration_time > current_time:
        return False
    else:
        return True
