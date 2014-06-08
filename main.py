#!/usr/bin/env python
# coding:utf-8

import webapp2
import jinja2
import os
import re
import json
from cgi import escape
from google.appengine.api import users
from models import *

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.user = users.get_current_user()
        self.person = Person.gql("WHERE user = :1", self.user).get()

    def render(self, tpl_file, tvals={}):
        tvals['user'] = self.user
        tvals['person'] = self.person
        tvals['logout'] = users.create_logout_url("/")
        tpl = jinja_environment.get_template('templates/' + tpl_file + '.html')
        self.response.out.write(tpl.render(tvals))

    def render_json(self, data):
        self.response.out.write(json.dumps(data))


class WelcodeHandler(BaseHandler):
    def get(self):  # promo page
        if self.person:
            self.redirect('/main/')
        else:
            self.render('welcome')

    def post(self):  # register
        if self.request.get('connect'):
            person = Person(user=self.user)
            person.put()
            Tag.get_or_insert_tag(person, 'inbox')
            self.redirect('/main/')


class MainHandler(BaseHandler):
    def get(self):  # main page
        messages = self.person.get_open_messages()
        bg_messages = self.person.get_bg_messages()
        current_message = self.person.get_current_message()
        tvals = {
            'messages': messages,
            'bg_messages': bg_messages,
            'current_message': current_message,
        }
        self.render('main', tvals)

    def post(self):  # post new mess
        if self.request.get('addmess'):
            tag_names = re.findall(ur"([a-zA-Z0-9]+)", self.request.get('tags'))
            tag_keys = [Tag.get_or_insert_tag(self.person, t).key() for t in tag_names]
            content = self.request.get('content')
            title = self.request.get('title')
            mess = Message(person=self.person, tags=tag_keys, content=content, title=title)
            mess.put()
            self.redirect('/mess/%s/' % mess.key())


class SettingsHandler(BaseHandler):
    def get(self):  # settings page
        self.render('settings')

    def post(self):  # save changes
        self.render('/settings/')


class StatsHandler(BaseHandler):
    def get(self):  # stats page
        self.render('stats')


class EditMessageHandler(BaseHandler):
    def get(self, mess_id):  # form for editing
        mess = Message.gql("WHERE __key__ = :1", db.Key(mess_id)).get()
        if not mess:
            self.redirect('/main/')
        tvals = {'mess': mess}
        self.render('edit_mess', tvals)

    def post(self, mess_id):  # submit form & ajax actions
        mess = Message.gql("WHERE __key__ = :1", db.Key(mess_id)).get()
        if not mess:
            self.redirect('/main/')
        elif self.request.get('ajaxmess'):
            if self.request.get('setcurr'):
                mess.set_curr()
            elif self.request.get('gotobg'):
                mess.set_bg()
            elif self.request.get('done'):
                mess.done()
            elif self.request.get('upd'):
                mess.update()
            elif self.request.get('addtag'):
                tag_name = escape(self.request.get('addtag'))
                mess.del_tag(tag_name)
            elif self.request.get('deltag'):
                tag_name = escape(self.request.get('deltag'))
                mess.del_tag(tag_name)
            self.render_json({'result': 1})
        elif self.request.get('editmess'):  # sumbit form
            mess.content = self.request.get('content')
            mess.title = self.request.get('title')
            mess.save()
            self.redirect('/mess/%s/' % mess.key())
        elif self.request.get('delmess'):  # sumbit form
            mess.remove()
            self.redirect('/main/')

class MessageHandler(BaseHandler):
    def get(self, mess_id):  # main page
        message = Message.gql("WHERE __key__ = :1", db.Key(mess_id)).get()
        if not message:
            self.redirect('/main/')
        tvals = {'message': message}
        self.render('mess', tvals)


class TagHandler(BaseHandler):
    def get(self, tag_name):  # main page
        tag = escape(tag_name)
        key_name = Tag.get_key_name(tag_name, self.person)
        tag = Tag.get_by_key_name(key_name)
        if not tag:
            self.redirect('/main/')
        else:
            messages = Message.gql("WHERE tags = :1", tag.key())
            tvals = {
                'messages': messages,
                'tag': tag
            }
            self.render('main', tvals)


class DoneHandler(BaseHandler):
    def get(self):  # main page
        messages = self.person.get_recently_done()
        tvals = {
            'messages': messages,
        }
        self.render('done', tvals)


app = webapp2.WSGIApplication([
    ('/', WelcodeHandler),
    ('/main/', MainHandler),
    ('/done/', DoneHandler),
    ('/stats/', StatsHandler),
    ('/settings/', SettingsHandler),
    ('/mess/([A-Za-z0-9\-]+)/', MessageHandler),
    ('/mess/([A-Za-z0-9\-]+)/edit/', EditMessageHandler),
    ('/tag/([A-Za-z0-9\-\+]+)/', TagHandler),
], debug=True)