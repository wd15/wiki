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
form_html = env.get_template('form.html')
fizzbuzz_html = env.get_template('fizzbuzz.html')

@app.route('/', methods=["GET"])
def main_page():
    foods = request.args.getlist('food')
    return form_html.render(foods=foods)


@app.route('/fizzbuzz', methods=['GET'])
def fizzbuzz():
    n = request.args.get('n')
    if n:
        n = int(n)
    return fizzbuzz_html.render(n=n)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


