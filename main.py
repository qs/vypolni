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

    def render(self, tpl_file, tvals={}):
        tvals['user'] = self.user
        tvals['logout'] = users.create_logout_url("/")
        tpl = jinja_environment.get_template('templates/' + tpl_file + '.html')
        self.response.out.write(tpl.render(tvals))

    def render_json(self, data):
        self.response.out.write(json.dumps(data))


class WelcodeHandler(BaseHandler):
    def get(self):
        if self.user:  # promo page
            self.redirect('/main/')
        else:
            self.render('welcome')


class JoinHandler(BaseHandler):
    def get(self):
        pref = Preference.query(Preference.user==self.user).get()
        if pref:  # already registered
            self.redirect('/main/')
        else:  # register
            pref = Preference(user=self.user)
            pref.put()
            self.redirect('/main/')

    def post(self):
        pref = Preference.query(Preference.user==self.user).get()
        if pref:  # already registered
            self.redirect('/main/')
        else:  # register
            pref = Preference(user=self.user)
            pref.put()
            self.redirect('/main/')


class MainHandler(BaseHandler):
    def get(self):
        curr = Quest.get_current(self.user)
        bg_cnt, bg_quests = Quest.get_bgs(self.user)
        open_cnt, open_quests = Quest.get_opens(self.user)
        closed_cnt = Quest.get_closed_cnt(self.user)
        tvars = {
            'curr': curr,
            'bg_cnt': bg_cnt,
            'bg_quests': bg_quests,
            'open_cnt': open_cnt,
            'open_quests': open_quests,
            'closed_cnt': closed_cnt,
        }
        self.render('main', tvars)

    def post(self):  # post quest
        if self.request.get('addquest'):
            title = escape(self.request.get('title'))
            if len(title) == 0:
                self.redirect('/main/')
            else:
                tags = escape(self.request.get('tags')).replace(' ', '').split(',')
                tags = [t for t in tags if len(t) > 0]
                content = self.request.get('content')
                quest = Quest(title=title, user=self.user, tags=tags, content=content)
                key = quest.put()
                self.redirect('/quest/%s/' % key.id())


class SettingsHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass


class QuestHandler(BaseHandler):
    def get(self, quest_id):
        quest = Quest.getone(int(quest_id))
        quest.statuses = [(status_names[QUEST_STATUS_OPEN], quest.dt.strftime("%Y-%m-%d %H:%M")), ]
        for statuses in quest.status_history:
            for k,v in statuses.items():
                quest.statuses.append( (status_names[int(k)], v[:16]) )
        print quest.statuses, quest.status_history
        self.render('quest', {'quest': quest})

    def post(self, quest_id):
        pass


class EditQuestHandler(BaseHandler):
    def get(self, quest_id):
        pass

    def post(self, quest_id):
        quest = Quest.getone(int(quest_id))
        if not quest:
            self.redirect('/main/')
        elif self.request.get('ajaxquest'):
            if self.request.get('setstatus'):
                print self.request.get('setstatus')
                quest.set_status(int(self.request.get('setstatus')))
            elif self.request.get('addtag'):
                tag_name = escape(self.request.get('addtag'))
                quest.add_tag(tag_name)
            elif self.request.get('deltag'):
                tag_name = escape(self.request.get('deltag'))
                quest.del_tag(tag_name)
            self.render_json({'result': 1})
        elif self.request.get('editquest'):  # sumbit form
            quest.content = self.request.get('content')
            quest.title = self.request.get('title')
            quest.save()
            self.redirect('/quest/%s/' % quest.key())
        elif self.request.get('delquest'):  # sumbit form
            quest.remove()
            self.redirect('/main/')


class FilterHandler(BaseHandler):
    def get(self, filter):
        conditions = dict([f.split('=') for f in filter.split('&')])
        quests = Quest.query().filter(Quest.user==self.user)
        if 'status' in conditions:
            quests = quests.filter(Quest.status==status_names.keys()[status_names.values().index(conditions['status'])])
        if 'tag' in conditions:
            quests = quests.filter(Quest.tags.IN([conditions['tag'], ]))
        self.render('filter', {'filter': filter, 'conditions': conditions, 'result': quests})

    def post(self, filter):
        self.render('filter')


app = webapp2.WSGIApplication([
    ('/', WelcodeHandler),
    ('/join/', JoinHandler),
    ('/main/', MainHandler),
    ('/settings/', SettingsHandler),
    ('/quest/([A-Za-z0-9\-]+)/', QuestHandler),
    ('/quest/([A-Za-z0-9\-]+)/edit/', EditQuestHandler),
    ('/find/([A-Za-z0-9\-\+\=\&]+)/', FilterHandler),
], debug=True)