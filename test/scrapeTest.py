#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import logging
import requests
from bs4 import BeautifulSoup
import re

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

URL = 'http://foodtruckfiesta.com/dc-food-truck-list/'
AVAILABLE_LOCATIONS = {
    'POLITICO': {
        'areas': ['Rosslyn'],
        'extra': 'There are probably other trucks outside too. Don\'t forget about Chipotle, Chop\'t, Potbelly, Wiseguy and that deli I don\'t know the name of.'
    },
    'bid': {
        'areas': [],
        'extra': None
    }
}

def run2(location='POLITICO'):
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
                result += '\nhttp://foodtruckfiesta.com/dc-food-truck-list/\n'
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
    logger.info(result)


def run(location='POLITICO'):
    """
    scrape foodtruckfiesta data
    """
    if location in AVAILABLE_LOCATIONS:
        response = requests.get(URL)
        if (response.status_code != 200):
            logger.error("page responded with %s code" % response.status_code)
            exit()
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            areas = AVAILABLE_LOCATIONS[location]['areas']
            for area in areas:
                trucks = ''
                h2 = soup.find('h2', text=re.compile(r'%s' % area))
                if h2:
                    nextNode = h2
                    while True:
                        nextNode = nextNode.nextSibling
                        try:
                            tag_name = nextNode.name
                        except AttributeError:
                            tag_name = ''
                        if tag_name == 'h2':
                            logger.info('found next h2 %s stop' % nextNode)
                            break
                        elif tag_name != 'div' or tag_name == '':
                            continue
                        else:
                            link = nextNode.find('a')
                            if link:
                                trucks += '%s\n' % link.get_text()
                                logger.info('trucks: %s' % trucks)
                else:
                    logger.info("area not found")
                logger.info('continue')
if __name__ == '__main__':
    run2()
