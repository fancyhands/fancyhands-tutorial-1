#!/usr/bin/env python
from google.appengine.ext import db
from datetime import datetime, timedelta
from fancyhands import FancyhandsClient

import webapp2
import os
import jinja2
import logging
import urlparse
import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        prank = PrankModel.all().order('-date_updated').get()
        template_values = {'prank':prank}

        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))

    def post(self):
        # Get the data from the HTML POST
        phone_number = self.request.get('phone-number')
        prank_text = self.request.get('prank-text')

        # Set your Fancy Hands API Key and Secret here
        api_key = 'PuREN1kznQ4UyWI'
        secret = 'dzvNP3hg0idkb0x'

        # Setup the Fancy Hands Client
        client = FancyhandsClient(api_key, secret)

        # What our assistants see when selecting what request to perform.
        # In this case it will be Prank Call - 555-555-5555.
        title = 'Prank Call - %s' % phone_number

        # This is the content of the request.
        # In this case we just use what you want said in your prank.
        description = prank_text

        # This is the price you are willing to pay for the request to be completed.
        bid = 4.0

        # This is when the task expires from our system.
        # This must be no more than 7 days in the future and is required.
        expiration_date = datetime.now() + timedelta(1)

        custom_fields = []
        custom_field = {
          'label':'Reaction',
          'type':'textarea',
          'description':'What was their reaction?',
          'order':1,
          'required':True,
        }
        custom_fields.append(custom_field)

        prank_request = client.custom_create(title, description, bid, expiration_date, custom_fields)

        prank = PrankModel.create_from_callback(prank_request)

        # Render new data
        template_values = {'prank':prank}
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))

class PrankModel(db.Model):
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_updated = db.DateTimeProperty(auto_now=True)
    title = db.StringProperty()
    content = db.TextProperty()
    status = db.StringProperty()
    bid = db.FloatProperty()
    fh_key = db.StringProperty()

    @classmethod
    def create_from_callback(self, callback):
        prank = PrankModel.all().filter('fh_key =', callback['key']).get()

        if prank:
            prank.status = callback['status']
            prank.numeric_status = callback['numeric_status']
        else:
            prank = PrankModel()
            prank.status = callback['status']
            prank.title = callback['title']
            prank.content = callback['content']
            prank.status = callback['status']
            prank.bid = float(callback['api_bid'])
            prank.fh_key = callback['key']

        prank.put()
        return prank

class CallbackHandler(webapp2.RequestHandler):
    def post(self):
        callback = dict(urlparse.parse_qsl(self.request.body))
        callback_to_model(callback)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/callback', CallbackHandler),
], debug=True)
