#!/usr/bin/env python
# coding:utf-8
import logging
import re
import webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from models import *
from google.appengine.api.users import User


class LogSenderHandler(InboundMailHandler):

    def parse_subject(self, subject, person):
        tag_names = re.findall(ur"\[([a-zA-Z0-9]+)\]", subject)
        if tag_names == []:
            tag_names = ['inbox', ]
        tag_keys = [Tag.get_or_insert_tag(person, t).key() for t in tag_names]
        subject = re.sub(ur"(s*\[[a-zA-Z0-9]+\]\s*)", '', subject)
        return subject, tag_keys

    def receive(self, message):
        user = User(email=re.findall("([a-zA-Z\.]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+)", message.sender)[0])
        person = Person.gql("WHERE user = :1", user).get()
        subject, tags = self.parse_subject(message.subject, person)
        content = u""
        for content_type, body in message.bodies('text/html'):
            content += body.decode()
        mess = Message(title=subject, tags=tags, person=person, content=content)
        mess.put()
        logging.info("Received a message from: " + message.sender)

app = webapp2.WSGIApplication([LogSenderHandler.mapping()], debug=True)