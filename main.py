"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, request, redirect, url_for
import jinja2
import os
import re


app = Flask(__name__)
app.config['DEBUG'] = True
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


## templates


loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
env = jinja2.Environment(autoescape=True,
                         loader=loader)
template = env.get_template('template.html')
welcome_template = env.get_template('welcome.html')


## regexps


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")


def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASSWORD_RE.match(password)

def password_match(p1, p2):
    return p1 == p2

def valid_email(email):
    return (email == '') or EMAIL_RE.match(email)

username_error = "That's not a valid username."
password_error = "That wasn't a valid password."
verify_error = "Your passwords didn't match."
email_error = "That's not a valid email."
##endpoints


@app.route('/', methods=["GET", "POST"])
def main_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']
        
        if valid_username(username) and \
          valid_password(password) and \
          password_match(password, verify) and \
          valid_email(email):
            return redirect(url_for('welcome', username=username))
        errors = dict()
        if not valid_username(username): 
            errors['username_error'] = username_error
        if not valid_password(password):
            errors['password_error'] = password_error
        if not password_match(password, verify):
            errors['verify_error'] = verify_error
        if not valid_email(email):
            errors['email_error'] = email_error
        return template.render(username=username, email=email, **errors)
    else:
        return template.render()


@app.route('/welcome', methods=["GET", "POST"])
def welcome():
    username = request.args.get('username')
    return welcome_template.render(username=username)

        
@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


