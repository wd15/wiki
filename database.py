from google.appengine.ext import db
import datetime

## database classes

class BlogEntry(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def to_dict(self):
        d = dict()
        for key, prop in self.properties().iteritems():
            value = getattr(self, key)
            if isinstance(value, datetime.date):
                value = value.strftime('%a %b %H:%M:%S %Y')
            d[key] = value
        return d
    
class UserLogin(db.Model):
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
