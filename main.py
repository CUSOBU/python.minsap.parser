import html
import logging
import re
from logging.handlers import RotatingFileHandler

from bs4 import BeautifulSoup
from htmldom import htmldom
from minsap.HTMLParser import strip_tags
from requests import get

import os.path

entries = [
    {'name': 'cubadata', 'url': 'https://covid19cubadata.github.io/data/covid19-cuba.json'},
    {'name': 'timeseries', 'url': 'https://pomber.github.io/covid19/timeseries.json'}
]

logger = logging.getLogger('parser.covid19.cusobucuba.com')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh = RotatingFileHandler('requests.log', mode='a', maxBytes=5 * 1024 * 1024, backupCount=1, encoding=None, delay=0)
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.debug('Started Sync')

url = 'https://salud.msp.gob.cu/'
logger.debug('Requesting ' + url)
r = get(url)
if r.status_code == 200:
    content = r.content.decode('utf-8').replace('\n', ' ').replace('&nbsp;', ' ')
    soup = BeautifulSoup(content, 'html.parser')
    posts = soup.find_all('article')
    for post in posts:
        url = post.find('a')['href']
        try:
            logger.debug('Requesting ' + url)
            r = get(url)
            if r.status_code == 200:
                dom = htmldom.HtmlDom()
                dom.createDom(r.content.decode('utf-8').replace('\n', ' ').replace('&nbsp;', ' '))

                title = dom.find('h1.post-title')
                date = None
                content = html.unescape(title.html().replace('\n', ' '))
                exp = re.search('día (?P<day>[0-9]+) de (?P<month>[a-z]+) (del|de) (?P<year>[0-9]+)', content)
                if exp:
                    day = exp.group('day')
                    month = exp.group('month')
                    if month == 'marzo':
                        month = 3
                    elif month == 'abril':
                        month = 4
                    year = exp.group('year')
                    date = str(year) + '-' + str(month) + '-' + str(day)

                    # Si existe el fichero ya el parte se ha registrado
                    if os.path.isfile('{}.json'.format(str(date))):
                        logger.debug('{}.json'.format(str(date)) + ' exist, continue')
                        continue

                new = total = 0
                entries = dom.find('div.themeform').find('p')
                for i in entries:
                    content = re.sub(" +", " ", html.unescape(i.html().replace('\n', ' ')))
                    exp = re.search('se confirma[a-z]+ (?P<new>([0-9]+|[a-z ]+)) (?:nuevo|caso)', content)
                    if exp:
                        new = exp.group('new')
                    exp = re.search('acumulado de (?P<total>[0-9]+)', content)
                    if exp:
                        total = exp.group('total')

                if not re.match('[0-9]+', new):
                    new = re.sub(' (nuevo(s)?|caso(s)?)', '', new)
                    if new == 'diez':
                        new = 10
                    elif new == 'nueve':
                        new = 9
                    elif new == 'ocho':
                        new = 8
                    elif new == 'cinco':
                        new = 5
                else:
                    new = int(new)

                persons = []
                entries = dom.find('div.themeform').find('li')
                checker = new
                for i in entries:
                    content = strip_tags(re.sub(" +", " ", html.unescape(i.html().replace('\n', ' '))))
                    exp = re.search('^( )?Ciudadan(a|o)', content)
                    if exp:
                        entry = {'age': 0, 'province': None, 'municipality': None, 'contacts': 0, 'origen': content}
                        exp = re.search('(?P<age>[0-9]+) años', content)
                        if exp:
                            entry['age'] = exp.group('age')
                        exp = re.search('municipio( de)? (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
                        if not exp:
                            exp = re.search('reside en (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
                        if exp:
                            entry['municipality'] = exp.group('name')
                        exp = re.search('provincia (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
                        if exp:
                            entry['province'] = exp.group('name')
                            if re.search('mismo nombre', entry['province']):
                                entry['province'] = entry['municipality']
                        exp = re.search('(?P<contacts>[0-9]+) contactos', content)
                        if exp:
                            entry['contacts'] = exp.group('contacts')
                        persons.append(entry)
                        checker -= 1
                        if checker == 0:
                            break
                # print({'day': date, 'total': total, 'new': new, 'persons': persons})
                open('{}.json'.format(str(date)), 'w').write(str({'day': date, 'total': total, 'new': new, 'persons': persons}))

        except IndexError:
            logger.debug('An index error has been found')
