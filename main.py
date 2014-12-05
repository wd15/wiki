"""`main` is the top level module for your Flask application."""
from google.appengine.ext import db
# Import the Flask Framework
from flask import Flask, request, redirect, url_for, make_response, render_template
import jinja2
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from google.appengine.api import memcache
import time
from werkzeug.routing import BaseConverter

from database import WikiEntry, UserLogin
import tools

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

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']

        errors = tools.get_errors(username, password, verify, email)
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
                wiki_page = request.args.get('wiki_page')
                response = tools.redirect_to_wiki_page(wiki_page)
                response = tools.add_login_cookie(user, response)
                return response
    else:
        return render_template('signup.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    wiki_page = request.args.get('wiki_page')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        q = UserLogin.all()
        q.filter("username =", username)
        user = q.get()

        if user and check_password_hash(user.password_hash, password):
            response = tools.redirect_to_wiki_page(wiki_page)
            return tools.add_login_cookie(q[0], response)
        else:
            return render_template('login.html', username=username, password_error="Invalid login.")
    else:
        return render_template('login.html')

@app.route('/logout', methods=["GET"])
def logout():
    wiki_page = request.args.get('wiki_page')
    response = tools.redirect_to_wiki_page(wiki_page)
    response.set_cookie('userhash', '', expires=0)
    return response

@app.route('/_edit', methods=["GET", "POST"])
@app.route('/_edit/', methods=["GET", "POST"])
@app.route('/_edit/<wiki_page>', methods=["GET", "POST"])
def edit_wiki(wiki_page=''):
    userhash = request.cookies.get('userhash', '')
    user_id = tools.check_secure_val(userhash)

    if user_id is None:
        return redirect(url_for('login', wiki_page=wiki_page))
    else:
        user = UserLogin.get_by_id(int(user_id))

        if request.method == 'POST':
            content = request.form['content']
            print 'content',content
            if content:
                entry = WikiEntry.all().filter('wiki_page =', '/' + wiki_page).get()
                if entry:
                    entry.content = content
                else:
                    entry = WikiEntry(content=content, wiki_page='/' + wiki_page)
                entry.put()
                return tools.redirect_to_wiki_page(wiki_page)
            else:
                return render_template('edit_wiki.html', username=user.username, error='Please submit some content')
        else:
            entry = WikiEntry.all().filter('wiki_page =', '/' + wiki_page).get()
            if entry:
                content = entry.content
            else:
                content = ''
            return render_template('edit_wiki.html', content=content, username=user.username, wiki_page=wiki_page)

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
        
# app.url_map.converters['regex'] = RegexConverter
# PAGE_RE = r"(/(?:[a-zA-Z0-9_-]+/?)*)"
@app.route('/')
@app.route('/<wiki_page>')
def view_wiki(wiki_page=''):
    userhash = request.cookies.get('userhash', '')
    user_id = tools.check_secure_val(userhash)
    if user_id is None:
        username = None
    else:
        username = UserLogin.get_by_id(int(user_id)).username
    entry = WikiEntry.all().filter('wiki_page =', '/' + wiki_page).get()
    if entry:       
        return render_template('view_wiki.html', content=entry.content, username=username, wiki_page=wiki_page)
    else:
        return redirect(url_for('edit_wiki', wiki_page=wiki_page))
