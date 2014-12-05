import re
import hmac
from flask import Flask, request, redirect, url_for, make_response

## make secure cookies

SECRET = 'imsosecret'
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "{0}|{1}".format(s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

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

def add_login_cookie(user, response):
    user_id = user.key().id()
    userhash = make_secure_val(str(user_id))
    response.set_cookie('userhash', userhash)
    return response

def redirect_to_wiki_page(wiki_page):
    redirection = redirect('/' + wiki_page)
    return make_response(redirection)

def json_response(s):
    response = make_response(s)
    response.headers['Content-Type'] = "application/json"
    return response
