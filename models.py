#!/usr/bin/env python
# coding:utf-8
from google.appengine.ext import db
from datetime import datetime

MESS_STATUS = {
    'open': 0,
    'background': 1,
    'current': 2,
    'done': 100,
}

HABIT_STATUS = {
    'open': 0,
    'success': 1,
    'fail': 2,
}

class Person(db.Model):
    user = db.UserProperty(required=True)
    dt = db.DateTimeProperty(auto_now_add=True)
    favtags = db.ListProperty(db.Key)

    def get_open_messages(self, tags=['inbox', ], status='open', page=0):
        status_id = MESS_STATUS[status]
        tags = Tag.gql("WHERE person = :1 AND title IN :2", self, tags).get()
        messages = Message.gql("""
            WHERE person = :1 AND tags = :2 AND status = :3 ORDER BY update_dt
            """, self, tags, status_id)
        return messages

    def get_recently_done(self, limit=10):
        messages = Message.gql("""
            WHERE person = :1 AND status = :2 ORDER BY finish_dt DESC LIMIT 10
            """, self, MESS_STATUS['done']) #TODO limit
        return messages

    def get_bg_messages(self):
        messages = Message.gql("""
            WHERE person = :1 AND status = :2 ORDER BY update_dt
            """, self, MESS_STATUS['current']).get()
        return messages

    def get_current_message(self):
        return Message.gql("""
            WHERE person = :1 AND status = :2 ORDER BY update_dt
            """, self, MESS_STATUS['background']).get()

    def get_tags(self):
        return Tag.gql("WHERE person = :1 ORDER BY title", self)


class Message(db.Model):
    person = db.ReferenceProperty(Person, required=True, collection_name='messages')
    title = db.StringProperty()
    dt = db.DateTimeProperty(auto_now_add=True)
    finish_dt = db.DateTimeProperty()
    update_dt = db.DateTimeProperty(auto_now_add=True)
    content = db.TextProperty(required=True)
    tags = db.ListProperty(db.Key)
    status = db.IntegerProperty(default=MESS_STATUS['open'])

    def get_tags(self):
        return Tag.gql("WHERE person = :1 AND __key__ IN :2 ORDER BY title", self.person, self.tags)

    def set_curr(self):
        mess = Message.gql("WHERE person = :1 AND status = :2", self.person, MESS_STATUS['current']).get()
        mess.status = MESS_STATUS['background']
        mess.save()
        self.status = MESS_STATUS['current']
        self.save()

    def set_bg(self):
        self.status = MESS_STATUS['background']
        self.save()

    def add_tag(self, tag_title):
        tag = Tag.get_or_insert_tag(self.person, tag_title)
        self.tags.append(tag.key())
        self.save()

    def del_tag(self, tag_title):
        tag = Tag.get_or_insert_tag(self.person, tag_title)
        self.tags.remove(tag.key())
        if not Message.gql("WHERE person = :1 AND tags = :2", self.person, tag.key()).get() and tag_title!='inbox':
            tag.remove()
        self.save()

    def update(self):
        self.update_dt = datetime.now()
        self.save()

    def done(self):
        self.finish_dt = datetime.now()
        self.status = MESS_STATUS['done']
        self.save()


class Tag(db.Model):
    person = db.ReferenceProperty(Person, required=True, collection_name='tags')
    title = db.StringProperty(required=True)
    content = db.TextProperty()

    @classmethod
    def get_or_insert_tag(cls, person, tag_name):
        key_name = cls.get_key_name(tag_name, person)
        tag = cls.get_by_key_name(key_name)
        if not tag:
            tag = cls(key_name=key_name, person=person, title=tag_name)
            tag.put()
        return tag

    @staticmethod
    def get_key_name(tag_name, person):
        return '%s_%s' % (person.user.nickname(), tag_name)


class Habit(db.Model):
    person = db.ReferenceProperty(Person, required=True, collection_name='habits')
    title = db.StringProperty(required=True)
    dt = db.DateTimeProperty(auto_now_add=True)
    progress = db.IntegerProperty(required=True)
    progress_max = db.IntegerProperty(required=True)
    finish_dt = db.DateTimeProperty()
    status = db.IntegerProperty(default=HABIT_STATUS['open'])

