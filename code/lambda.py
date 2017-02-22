#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from __future__ import print_function
import logging
import requests
import re
from bs4 import BeautifulSoup


print('Loading comidaBot function')

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
    logger.debug(event)
    bot_event = event
    raw_text = None
    try:
        raw_text = bot_event['text']
    except KeyError:
        pass
    if not raw_text:
        location = 'npr'
    else:
        location = raw_text.strip().lower()
    result = ''
    if location in AVAILABLE_LOCATIONS:
        response = requests.get(URL)
        if (response.status_code != 200):
            logger.error("page responded with %s code" % response.status_code)
            result += 'Could not get food truck data.\n'
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            areas = AVAILABLE_LOCATIONS[location]['areas']
            for area in areas:
                h2 = soup.find('h2', text=re.compile(r'%s' % area))
                if h2:
                    result += '\n## ' + area + '\n'
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
                                result += '%s\n' % link.get_text()
            if result != '':
                result += '\nhttp://foodtruckfiesta.com/apps/maplarge.html\n'
            extra = AVAILABLE_LOCATIONS[location]['extra']
            if extra:
                result += '\n%s\n' % extra
            # Check to see if our result is still empty and warn user
            if result == '':
                result += 'No available areas for your location'
    else:
        result += "Your location is not available. Available locations:\n"
        for key in AVAILABLE_LOCATIONS:
            result += '-%s\n' % key
    logger.info('result %s' % result)
    return {'text': result}