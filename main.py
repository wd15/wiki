"""`main` is the top level module for your Flask application."""
from google.appengine.ext import db
# Import the Flask Framework
from flask import Flask, request, redirect, url_for, make_response
import jinja2
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from google.appengine.api import memcache
import time

from database import BlogEntry, UserLogin
from tools import get_errors, redirect_for_welcome, check_secure_val, json_response

app = Flask(__name__)
app.config['DEBUG'] = True
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


## templates

loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
env = jinja2.Environment(autoescape=True,
                         loader=loader)
env.globals.update(url_for=url_for)
blog_html = env.get_template('blog.html')
submit_html = env.get_template('submit.html')
signup_template = env.get_template('signup.html')
welcome_template = env.get_template('welcome.html')
login_template = env.get_template('login.html')

## memcache

def cache(query, key, update):
    query_time_key = 'qt'
    value = memcache.get(key)
    if value is None or update:
        value = query()
        memcache.set(key, value)
        memcache.set(query_time_key, time.time())
    return value, int(time.time() - memcache.get(query_time_key))

def cache_entry(entry_id, update=False):
    query = lambda: BlogEntry.get_by_id(entry_id)
    return cache(query, str(entry_id), update)

def cache_entries(update=False):
    query = lambda: db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC")
    return cache(query, 'top10', update)

def cache_update(entry_id):
    cache_entry(entry_id, update=True)
    cache_entries(update=True)
    
## end points

@app.route('/', methods=['GET'])
def root():
    return redirect(url_for('blog'))

@app.route('/blog')
def blog():
    entries, qt_lag = cache_entries()
    return blog_html.render(entries=entries, qt_lag=qt_lag)

@app.route('/blog/.json')
def blog_json():
    entries = cache_entries()
    return json_response(json.dumps([e.to_dict() for e in entries]))

@app.route('/blog/<int:entry_id>')
def blog_entry_id(entry_id):
    entry, qt_lag = cache_entry(entry_id)
    return blog_html.render(entries=[entry], qt_lag=qt_lag)

@app.route('/blog/<int:entry_id>.json')
def blog_entry_id_json(entry_id):
    entry = BlogEntry.get_by_id(entry_id)
    return json_response(json.dumps(entry.to_dict()))

@app.route('/blog/newpost', methods=['GET', 'POST'])
def blog_newpost():
    if request.method == 'POST':
        subject = request.form["subject"]
        content = request.form["content"]
        if subject and content:
            entry = BlogEntry(subject=subject, content=content)
            entry.put()
            entry_id = entry.key().id()
            cache_update(entry_id)
            return redirect(url_for('blog_entry_id', entry_id=entry_id))
        else:
            return submit_html.render(subject=subject, content=content, error="Please submit both a title and some text!")
    else:
        return submit_html.render()

@app.route('/blog/flush')
def flush():
    memcache.flush_all()
    return redirect(url_for('blog'))

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404

@app.route('/blog/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']

        errors = get_errors(username, password, verify, email)
        if errors:
            return signup_template.render(username=username, email=email, **errors)
        else:
            q = UserLogin.all()
            q.filter("username =", username)
            if q.get():
                return signup_template.render(username=username, email=email, username_error='Already signed up.')
            else:
                password_hash = generate_password_hash(password)
                user = UserLogin(username=username, password_hash=password_hash)
                user.put() 
                return redirect_for_welcome(user)
    else:
        return signup_template.render()

@app.route('/blog/welcome', methods=["GET", "POST"])
def welcome():
    userhash = request.cookies.get('userhash', '')
    user_id = check_secure_val(userhash)
    if user_id:
        user = UserLogin.get_by_id(int(user_id))
        username = user.username
        return welcome_template.render(username=username)
    else:
        return redirect(url_for('main_page'))
    
@app.route('/blog/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        q = UserLogin.all()
        q.filter("username =", username)
        user = q.get()

        if user and check_password_hash(user.password_hash, password):
            return redirect_for_welcome(q[0])
        else:
            return login_template.render(username=username, password_error="Invalid login.")
    else:
        return login_template.render()

@app.route('/blog/logout', methods=["GET", "POST"])
def logout():
    redirection = redirect(url_for('signup'))
    response = make_response(redirection)
    response.set_cookie('userhash', '', expires=0)
    return response
 

