#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
import logging
import re
import json
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

URL = 'http://foodtruckfiesta.com/dc-food-truck-list/'
AVAILABLE_LOCATIONS = {
    'npr': {
        'areas': ['NoMa', 'CNN', 'Union Station'],
        'extra': 'Here\'s the SoundBites menu for this week: https://intranet.npr.org/intranet/publish/Main/Employee_Resources/Sound_Bites_Cafe.php'
    }
}


def lambda_handler(event, context):
    payload = {'response_type': 'in_channel'}
    text = ''
    raw_text = None
    user = None
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info(message)
    try:
        raw_text = message['text']
        user = message['user_name']
    except KeyError:
        pass
    try:
        url = message['response_url']
    except KeyError:
        logger.error("could nof find the response url")
        return
    if user:
        text += 'Hi %s, Here are your options for today\n' % user
    if not raw_text:
        location = 'npr'
    else:
        location = raw_text.strip().lower()
    if location in AVAILABLE_LOCATIONS:
        response = requests.get(URL)
        if (response.status_code != 200):
            logger.error("page responded with %s code" % response.status_code)
            text += 'Could not get food truck data.\n'
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            areas = AVAILABLE_LOCATIONS[location]['areas']
            for area in areas:
                h2 = soup.find('h2', text=re.compile(r'%s' % area))
                if h2:
                    text += '\n## ' + area + '\n'
                    nextNode = h2
                    while True:
                        nextNode = nextNode.nextSibling
                        try:
                            tag_name = nextNode.name
                        except AttributeError:
                            tag_name = ''
                        if tag_name == 'h2':
                            break
                        elif tag_name == 'div':
                            link = nextNode.find('a')
                            if link:
                                text += '%s\n' % link.get_text()
            if text != '':
                text += '\nhttp://foodtruckfiesta.com/apps/maplarge.html\n'
            extra = AVAILABLE_LOCATIONS[location]['extra']
            if extra:
                text += '\n%s\n' % extra
            # Check to see if our result is still empty and warn user
            if text == '':
                text += 'No available areas for your location'
    else:
        text += "Your location is not available. Available locations:\n"
        for key in AVAILABLE_LOCATIONS:
            text += '-%s\n' % key
    logger.info('text %s' % text)
    # Add text to the payload
    payload['text'] = text
    # Finally send a post response to slack
    requests.post(url, json=payload)
