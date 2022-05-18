from base64 import b64encode
# from crypt import methods
from io import BytesIO
from json.tool import main

import cv2
import numpy as np
from PIL import Image
from flask import render_template, Response, flash, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from werkzeug.exceptions import abort
from wtforms import FileField, SubmitField
from app.main import main_bp
from app.main.camera import Camera

from source.test_new_images import detect_mask_in_image
from source.video_detector import detect_mask_in_frame

import mysql.connector
import re

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mriganka123",
    database="flask"
)

# mycursor = mydb.cursor()

# mycursor.execute("SHOW DATABASES")

# for x in mycursor:
#     print(x)


@main_bp.route("/")
def home_page():
    return render_template("home_page.html")


def gen(camera):
    while True:
        frame = camera.get_frame()
        frame_processed, mask_or_not = detect_mask_in_frame(frame)
        # print(mask_or_not)
        frame_processed = cv2.imencode('.jpg', frame_processed)[1].tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_processed + b'\r\n')


@main_bp.route('/video_feed')
def video_feed():
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')


def allowed_file(filename):
    ext = filename.split(".")[-1]
    is_good = ext in ["jpg", "jpeg", "png"]
    return is_good


@main_bp.route("/image-mask-detector", methods=["GET", "POST"])
def image_mask_detection():
    return render_template("image_detector.html",
                           form=PhotoMaskForm())


@main_bp.route("/image-processing", methods=["POST"])
def image_processing():
    form = PhotoMaskForm()

    if not form.validate_on_submit():
        flash("An error occurred", "danger")
        abort(Response("Error", 400))

    pil_image = Image.open(form.image.data)
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    array_image = detect_mask_in_image(image)
    rgb_image = cv2.cvtColor(array_image, cv2.COLOR_BGR2RGB)
    image_detected = Image.fromarray(rgb_image, 'RGB')

    with BytesIO() as img_io:
        image_detected.save(img_io, 'PNG')
        img_io.seek(0)
        base64img = "data:image/png;base64," + \
            b64encode(img_io.getvalue()).decode('ascii')
        return base64img


@main_bp.route("/login", methods=['GET', "POST"])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        code = request.form['code']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mydb.cursor()
        cursor.execute(
            'SELECT * FROM employee WHERE username = %s AND code = %s AND password = %s', (username, code, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # print(account)
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[5]
            session['username'] = account[2]
            # Redirect to home page
            # return 'Logged in successfully!'
            cursor.execute(
                "INSERT INTO `attendence`(`code`, `date`, `isPresent`) VALUES(%s, current_timestamp(), 'P')",
                (code,)
            )
            mydb.commit()
            flash(account[1] + " logged in and attendence given successfully!")
            return redirect(url_for('main.home_page'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template("login.html", msg=msg)


@main_bp.route("/register", methods=['GET', "POST"])
def register():
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'name' in request.form and 'username' in request.form and 'code' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        name = request.form['name']
        username = request.form['username']
        code = request.form['code']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mydb.cursor()
        cursor.execute(
            'SELECT * FROM employee WHERE code = %s', (code,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'INSERT INTO employee VALUES (NULL, %s, %s, %s, %s, %s)', (name, username, password, email, code,))
            mydb.commit()
            msg = name + ' successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@main_bp.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect("/")


# form
class PhotoMaskForm(FlaskForm):
    image = FileField('Choose image:',
                      validators=[
                          FileAllowed(['jpg', 'jpeg', 'png'], 'The allowed extensions are: .jpg, .jpeg and .png')])

    submit = SubmitField('Detect mask')
