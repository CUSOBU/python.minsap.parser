import html
import re
from json import dump
from os.path import isfile
from minsap.HTMLParser import strip_tags


ENTRIES = [
    {'name': 'cubadata', 'url': 'https://covid19cubadata.github.io/data/covid19-cuba.json'},
    {'name': 'timeseries', 'url': 'https://pomber.github.io/covid19/timeseries.json'}
]


MONTHS = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12,
}
NUMBERS = {
    'nueve': 9,
    'ocho': 8,
    'diez': 10,
    'cinco': 5,
}


def store_data(file_name, info):
    with open(file_name, 'w') as file:
        dump(info, file, indent=True)


def record_exist(date):
    return isfile(f'{str(date)}.json')


def parse_date(content):
    exp = re.search(
        'día (?P<day>[0-9]+) de (?P<month>[a-z]+) (del|de) (?P<year>[0-9]+)', content)
    if exp:
        day = exp.group('day')
        month = exp.group('month')
        month = MONTHS.get(month.lower(), month)
        year = exp.group('year')
        return '-'.join((str(year), str(month), str(day)))


def parse_confirmed_total(entries):
    new = total = 0

    for entry in entries:
        content = re.sub(
            " +", " ", html.unescape(entry.html().replace('\n', ' ')))
        exp = re.search(
            'se confirma[a-z]+ (?P<new>([0-9]+|[a-z ]+)) (?:nuevo|caso)', content)
        new = exp.group('new') if exp else new

        exp = re.search('acumulado de (?P<total>[0-9]+)', content)
        total = exp.group('total') if exp else total

    if not re.match('[0-9]+', str(new)):
        new = re.sub(' (nuevo(s)?|caso(s)?)', '', new)
        new = NUMBERS.get(new.lower(), new)
    else:
        new = int(new)
    total = int(total)
    return total, new


def parse_infected_info(entry_raw):
    content = strip_tags(
        re.sub(" +", " ", html.unescape(entry_raw.html().replace('\n', ' '))))
    exp = re.search('^( )?Ciudadan(a|o)', content)
    if exp:
        entry = {'age': 0, 'province': None,
                 'municipality': None, 'contacts': 0, 'origen': content}
        # age
        exp = re.search('(?P<age>[0-9]+) años', content)
        entry['age'] = int(exp.group(
            'age')) if exp else entry['age']
        # municipality
        exp = re.search(
            'municipio( de)? (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
        if not exp:
            exp = re.search(
                'reside en (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
        entry['municipality'] = exp.group(
            'name') if exp else entry['municipality']
        # province
        exp = re.search(
            'provincia (?P<name>[a-zA-ZüñáéíóúÁÉÍÓÚ ]+)', content)
        if exp:
            entry['province'] = exp.group('name')
            if re.search('mismo nombre', entry['province']):
                entry['province'] = entry['municipality']
        # contacts
        exp = re.search(
            '(?P<contacts>[0-9]+) contactos', content)
        entry['contacts'] = int(exp.group(
            'contacts')) if exp else entry['contacts']
        #
        return entry
