"""`main` is the top level module for your Flask application."""
from google.appengine.ext import db
# Import the Flask Framework
from flask import Flask, request, redirect, url_for
import flask
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
env.globals.update(url_for=url_for)
blog_html = env.get_template('blog.html')
submit_html = env.get_template('submit.html')


## end points

@app.route('/', methods=['GET'])
def root():
    return redirect(url_for('blog'))

@app.route('/blog')
def blog():
    blogposts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
    return blog_html.render(blogposts=blogposts)

@app.route('/blog/<int:post_id>')
def blog_by_id(post_id):
    blogpost = BlogPost.get_by_id(post_id)
    return blog_html.render(blogposts=[blogpost])

@app.route('/blog/newpost', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form["title"]
        post = request.form["post"]
        if title and post:
            entry = BlogPost(title=title, post=post)
            entry.put()
            return redirect(url_for('blog_by_id', post_id=entry.key().id()))
        else:
            return submit_html.render(title=title, post=post, error="Please submit both a title and a blog post!")
    else:
        return submit_html.render()


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404

## database classes

class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    post = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    
