#!/usr/bin/env python
# coding:utf-8
from google.appengine.ext import ndb
from datetime import datetime


QUEST_STATUS_OPEN = 0
QUEST_STATUS_BG = 1
QUEST_STATUS_CURRENT = 2
QUEST_STATUS_CLOSED = 3


class BaseModel(ndb.Model):
    @classmethod
    def getone(c, key_name):
        k = ndb.Key(c, key_name)
        return k.get()

    @property
    def id(self):
        return self.key.id()


class Preference(BaseModel):
    user = ndb.UserProperty(required=True)
    dt = ndb.DateTimeProperty(auto_now_add=True)
    favtags = ndb.StringProperty(repeated=True)


class Note(BaseModel):
    user = ndb.UserProperty(required=True)
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    tags = ndb.StringProperty(repeated=True)
    dt = ndb.DateTimeProperty(auto_now_add=True)
    upd_dt = ndb.DateTimeProperty(auto_now_add=True)


class Quest(BaseModel):
    user = ndb.UserProperty(required=True)
    title = ndb.StringProperty(required=True)
    tags = ndb.StringProperty(repeated=True)
    dt = ndb.DateTimeProperty(auto_now_add=True)
    upd_dt = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty(required=True,
                                 default=QUEST_STATUS_OPEN,
                                 choices=[QUEST_STATUS_OPEN,
                                          QUEST_STATUS_BG,
                                          QUEST_STATUS_CURRENT,
                                          QUEST_STATUS_CLOSED])
    finish_dt = ndb.DateTimeProperty()
    status_history = ndb.JsonProperty()

    def set_status(self, status):
        if status == QUEST_STATUS_CURRENT:
            return
        if status == QUEST_STATUS_CURRENT:
            curr = Quest.query(Quest.status==QUEST_STATUS_CURRENT, Quest.user==self.user).get()
            if curr:
                curr.status = QUEST_STATUS_BG
                curr.put()
        self.status_history.append({status: str(datetime.now())})
        self.status = status
        self.put()

    @staticmethod
    def get_current(self, user):
        curr = Quest.query(Quest.user==user, Quest.status==QUEST_STATUS_CURRENT).get()
        return curr

    @staticmethod
    def get_bgs(self, user, limit=5):
        q = Quest.query(Quest.user==user, Quest.status==QUEST_STATUS_BG)
        cnt = q.count()
        quests = q.order(-Quest.upd_dt).fetch(limit)
        return cnt, quests

    @staticmethod
    def get_opens(self, user, limit=5):
        q = Quest.query(Quest.user==user, Quest.status==QUEST_STATUS_OPEN)
        cnt = q.count()
        quests = q.order(-Quest.upd_dt).fetch(limit)
        return cnt, quests