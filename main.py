import html
import logging
import os
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import feedparser
from htmldom import htmldom

from utils import parse_confirmed_total, parse_infected_info, store_data, validate_title

DUMP_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dates')
PARSER = 'lxml'
try:
    import lxml
except ImportError:
    PARSER = 'html.parser'

logger = logging.getLogger('parser.covid19.cusobucuba.com')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh = RotatingFileHandler('requests.log', mode='a', maxBytes=5 * 1024 * 1024, backupCount=1, encoding=None, delay=False)
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.debug('Started Sync')

if __name__ == "__main__":
    # url = 'https://salud.msp.gob.cu/'
    url = 'https://salud.msp.gob.cu/?feed=rss2'
    logger.debug(f'Requesting {url}')

    news_feed = feedparser.parse(url)

    if news_feed:
        for post in news_feed.entries:
            try:

                title = post.title
                if not validate_title(title):
                    continue

                content = post.content[0]['value']
                date = datetime.strptime(time.strftime('%Y-%m-%d', post.published_parsed), '%Y-%m-%d') - timedelta(days=1)
                logger.debug(f'Requesting {url}')
                date = date.strftime("%Y-%m-%d")

                dom = htmldom.HtmlDom()
                dom.createDom(html.unescape(content.replace('\n', ' ')))

                # Si existe el fichero ya el parte se ha registrado
                # if record_exist(date):
                if os.path.isfile(os.path.join(DUMP_DIRECTORY, f'{date}.json')):
                    logger.debug(f'"{str(date)}.json" exist, continue')
                    continue

                entries = dom.find('div.themeform').find('p')
                total, new = parse_confirmed_total(entries)

                persons = []
                entries = dom.find('div.themeform').find('li')
                checker = new
                for entry in entries:
                    person = parse_infected_info(entry)
                    if person:
                        persons.append(person)
                        checker -= 1
                    if checker == 0:
                        break
                store_data(os.path.join(DUMP_DIRECTORY, f'{date}.json'), {'day': date, 'total': total, 'diff': checker, 'new': new, 'persons': persons})

            except IndexError:
                logger.debug('An index error has been found')
