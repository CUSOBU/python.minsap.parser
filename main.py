import re
import html
import logging
import requests

from htmldom import htmldom
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler

from utils import (MONTHS, ENTRIES,
                   parse_infected_info,
                   parse_date,
                   parse_confirmed_total,
                   record_exist, store_data)

PARSER = 'lxml'
try:
    import lxml
except ImportError:
    PARSER = 'html.parser'

logger = logging.getLogger('parser.covid19.cusobucuba.com')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh = RotatingFileHandler('requests.log', mode='a', maxBytes=5 *
                         1024 * 1024, backupCount=1, encoding=None, delay=0)
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.debug('Started Sync')

if __name__ == "__main__":
    url = 'https://salud.msp.gob.cu/'
    logger.debug(f'Requesting {url}')
    session = requests.Session()
    r = session.get(url)
    if r.status_code == 200:
        content = r.content.decode(
            'utf-8').replace('\n', ' ').replace('&nbsp;', ' ')
        soup = BeautifulSoup(content, PARSER)
        posts = soup.find_all('article')
        for post in posts:
            url = post.find('a')['href']
            try:
                logger.debug(f'Requesting {url}')
                r = session.get(url)
                if r.status_code == 200:
                    dom = htmldom.HtmlDom()
                    dom.createDom(r.content.decode(
                        'utf-8').replace('\n', ' ').replace('&nbsp;', ' '))

                    title = dom.find('h1.post-title')
                    content = html.unescape(title.html().replace('\n', ' '))
                    date = parse_date(content)

                    # Si existe el fichero ya el parte se ha registrado
                    if record_exist(date):
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
                    # print({'day': date, 'total': total, 'new': new, 'persons': persons})
                    # open(f'{str(date)}.json', 'w').write(str({'day': date, 'total': total, 'new': new, 'persons': persons})
                    store_data(f'{str(date)}.json', {
                        'day': date,
                        'total': total,
                        'new': new,
                        'persons': persons
                    })
            except IndexError:
                logger.debug('An index error has been found')
