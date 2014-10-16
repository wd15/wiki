"""`main` is the top level module for your Flask application."""
from google.appengine.ext import db
# Import the Flask Framework
from flask import Flask, request, redirect, url_for
import jinja2
import os

app = Flask(__name__)
app.config['DEBUG'] = True
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


## templates


loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
env = jinja2.Environment(autoescape=True,
                         loader=loader)
ascii_html = env.get_template('ascii.html')
output_html = env.get_template('output.html')



@app.route('/', methods=["GET", "POST"])
def main_page():
    arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
    if request.method == 'POST':
        title = request.form["title"]
        art = request.form["art"]
        if title and art:
            a = Art(title=title, art=art)
            a.put()
            arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
            return redirect(url_for('main_page'))
        else:
            return ascii_html.render(art=art, title=title, error="we need both a title and some artwork!", arts=arts)
    else:
        return ascii_html.render(arts=arts)


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    
