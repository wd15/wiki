from google.appengine.ext import db

## database classes

class WikiEntry(db.Model):
    wiki_page = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

class UserLogin(db.Model):
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
