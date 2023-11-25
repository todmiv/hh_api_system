from pprint import pprint
import re
from collections import Counter
from json import dump as j_dump
from requests import get
from pycbrf import ExchangeRates


def get_vacancy_data(vacancy):
    params = {'text': vacancy}
    result = get(url=url, params=params).json()
    count_pages = result['pages']
    all_count = len(result['items'])
    return count_pages, all_count, result['items']


def process_vacancy(res, rate, skills_, salary):
    skills = set()
    res_full = get(res['url']).json()
    pp = res_full['description']
    pp_re = re.findall(r'^[\s\S][A-Za-z-?]+$', pp)
    its = set(x.strip(' -').lower() for x in pp_re)
    for sk in res_full['key_skills']:
        skills_.append(sk['name'].lower())
        skills.add(sk['name'].lower())
        print(sk['name'])
    for it in its:
        if not any(it in x for x in skills):
            skills_.append(it)
    if res_full['salary']:
        code = res_full['salary']['currency']
        if rate[code] is None:
            code = 'RUR'
        k = 1 if code == 'RUR' else float(rate[code].value)
        salary['from'].append(k * res_full['salary']['from'] if res['salary']['from'] else k * res_full['salary']['to'])
        salary['to'].append(k * res_full['salary']['to'] if res['salary']['to'] else k * res_full['salary']['from'])


def process_skills(skills_, salary, result):
    sk2 = Counter(skills_)
    up = sum(salary['from']) / len(salary['from'])
    down = sum(salary['to']) / len(salary['to'])
    result.update({'down': round(up, 2), 'up': round(down, 2)})
    add = []
    for name, count in sk2.most_common(15):
        add.append({'name': name, 'count': count, 'percent': round((count / result['count']) * 100, 2)})
    result['requirements'] = add
    return result


# Ввод интересующей вакансии
vacancy = input('Введите интересующую вакансию: ')
url = 'https://api.hh.ru/vacancies'
rate = ExchangeRates()  # загрузка текущих курсов валют

# Получение данных о вакансиях
count_pages, all_count, items = get_vacancy_data(vacancy)

result = {
    'keywords': vacancy,
    'count': all_count
}
salary = {'from': [], 'to': []}
skills_ = []

# Обработка каждой вакансии
for page in range(count_pages):
    if page > 20:
        break
    else:
        print(f"Обрабатывается страница {page}")
    params = {'text': vacancy, 'page': page}
    res_ = get(url=url, params=params).json()
    all_count = len(res_['items'])
    result['count'] += all_count
    for res in res_['items']:
        process_vacancy(res, rate, skills_, salary)

# Обработка навыков и формирование результатов
result = process_skills(skills_, salary, result)
pprint(result)

# Сохранение файла с результатами работы
with open('result.json', mode='w', encoding='utf-8') as f:
    j_dump([result], f)
