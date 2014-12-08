"""`main` is the top level module for your Flask application."""
from google.appengine.ext import db
# Import the Flask Framework
from flask import Flask, request, redirect, url_for, make_response, render_template
import jinja2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.routing import BaseConverter
import hmac
import re


app = Flask(__name__)
app.config['DEBUG'] = True
app.debug = True

# templages

loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
env = jinja2.Environment(autoescape=True,
                         loader=loader)
env.globals.update(url_for=url_for)

# views

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']

        errors = get_errors(username, password, verify, email)
        if errors:
            return render_template('signup.html', username=username, email=email, **errors)
        else:
            q = UserLogin.all()
            q.filter("username =", username)
            if q.get():
                return render_template('signup.html', username=username, email=email, username_error='Already signed up.')
            else:
                password_hash = generate_password_hash(password)
                user = UserLogin(username=username, password_hash=password_hash)
                user.put()
                last = request.args.get('last', url_for('view_wiki'))                    
                response = make_response(redirect(last))
                return add_login_cookie(user, response)
    else:
        return render_template('signup.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        q = UserLogin.all()
        q.filter("username =", username)
        user = q.get()

        if user and check_password_hash(user.password_hash, password):
            last = request.args.get('last', url_for('view_wiki'))
            response = make_response(redirect(last))
            return add_login_cookie(q[0], response)
        else:
            return render_template('login.html', username=username, password_error="Invalid login.")
    else:
        return render_template('login.html')

@app.route('/logout', methods=["GET"])
def logout():
    last = request.args.get('last', url_for('view_wiki'))
    response = make_response(redirect(last))
    response.set_cookie('userhash', '', expires=0)
    return response

# edit view

# @app.route('/_edit', methods=["GET", "POST"])
@app.route('/_edit', methods=["GET", "POST"])
@app.route('/_edit/', methods=["GET", "POST"])
@app.route('/_edit/<wiki_page>', methods=["GET", "POST"])
def edit_wiki(wiki_page=''):
    userhash = request.cookies.get('userhash', '')
    user_id = check_secure_val(userhash)
    if user_id is None:
        return redirect(url_for('login', wiki_page=wiki_page))
    else:
        user = UserLogin.get_by_id(int(user_id))

        if request.method == 'POST':
            content = request.form['content']
            if content:
                entry = WikiEntry(content=content, wiki_page=wiki_page)
                entry.put()
                return redirect(url_for('view_wiki', wiki_page=wiki_page))
            else:
                return render_template('edit_wiki.html', username=user.username, error='Please submit some content', request=request)
        else:
            entry = WikiEntry.get_latest(wiki_page)
            if entry:
                content = entry.content
            else:
                content = ''
            return render_template('edit_wiki.html', content=content, username=user.username, wiki_page=wiki_page, request=request)

# wiki view
        
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
        
app.url_map.converters['regex'] = RegexConverter
PAGE_RE = r"((?:[a-zA-Z0-9_-]+/?)*)"
@app.route('/<regex("{0}"):wiki_page>'.format(PAGE_RE))
@app.route('/')
def view_wiki(wiki_page=''):
    userhash = request.cookies.get('userhash', '')
    user_id = check_secure_val(userhash)
    entry_id = request.args.get('entry_id', None)
    if user_id is None:
        username = None
    else:
        username = UserLogin.get_by_id(int(user_id)).username

    if entry_id:
        entry = WikiEntry.get_by_id(int(entry_id))
    else:
        entry = WikiEntry.get_latest(wiki_page)
    if entry:       
        return render_template('view_wiki.html', content=entry.content, username=username, wiki_page=wiki_page, request=request)
    else:
        return redirect(url_for('edit_wiki', wiki_page=wiki_page))

# history view

@app.route('/_history', methods=["GET", "POST"])
@app.route('/_history/', methods=["GET", "POST"])
@app.route('/_history/<wiki_page>', methods=["GET", "POST"])
def history(wiki_page=''):
    userhash = request.cookies.get('userhash', '')
    user_id = check_secure_val(userhash)
    if user_id is None:
        username=None
    else:
        username = UserLogin.get_by_id(int(user_id)).username
    entries = WikiEntry.all().filter('wiki_page =', wiki_page).order('-created').fetch(limit=10)
    if entries:       
        return render_template('history.html', entries=entries, username=username, wiki_page=wiki_page, request=request)
    else:
        return redirect(url_for('edit_wiki', wiki_page=wiki_page))

# security
    
def redirect_to_wiki_page(wiki_page, entry_id):
    redirection = redirect(url_for('view_wiki', wiki_page=wiki_page, entry_id=entry_id))
    # redirection = redirect('/' + wiki_page)
    return make_response(redirection)

def add_login_cookie(user, response):
    user_id = user.key().id()
    userhash = make_secure_val(str(user_id))
    response.set_cookie('userhash', userhash)
    return response

def make_secure_val(s):
    return "{0}|{1}".format(s, hash_str(s))

SECRET = 'imsosecret'
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

## check signin errors

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

def get_errors(username, password, verify, email):
    errors = dict()
    if not valid_username(username): 
        errors['username_error'] = username_error
    if not valid_password(password):
        errors['password_error'] = password_error
    if not password_match(password, verify):
        errors['verify_error'] = verify_error
    if not valid_email(email):
        errors['email_error'] = email_error
    return errors

## models

class WikiEntry(db.Model):
    wiki_page = db.StringProperty(required=False)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_latest(cls, wiki_page):
        return cls.all().filter('wiki_page =', wiki_page).order('-created').get()
    
class UserLogin(db.Model):
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
