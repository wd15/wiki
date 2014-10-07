"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, request
import jinja2
import os
import codecs


app = Flask(__name__)
app.config['DEBUG'] = True
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.



loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
env = jinja2.Environment(autoescape=True,
                         loader=loader)
template = env.get_template('template.html')


@app.route('/', methods=["GET", "POST"])
def main_page():
    if request.method == 'POST':
        text = codecs.encode(request.form['text'], 'rot_13')
        return template.render(text=text)
    else:
        return template.render(text='hi!')

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


