#!/usr/bin/python
# -*- coding: utf-8 -*-

from colorama import init, Fore, Back, Style
init()

import re, requests, json, ast
import constants, utils, users

articles = []
backup_articles = []


def init():
    """Initiates globals with API data"""
    print('[0%] Loading articles.\r'),  # comma lets next print overwrite.
    global articles, backup_articles
    articles = requests.get(constants.API_ARTICLES_ENDPOINT).json()
    with open('backups/wp-articles-backup.txt', 'r') as f:
        backup_articles = ast.literal_eval(f.read()).values()
    print('[100%] Loaded articles.')


def file_article_exists(file_content):
    file_content = unicode(file_content, 'utf-8')
    for existing_article in articles:
        if existing_article['title'] not in file_content:
            continue
        last_pgraph = existing_article['content'][-1]
        if last_pgraph[last_pgraph.rfind('<p>') + len('<p>'):
                       -len('</p>')] in file_content:
            return True
    return False


def get_title(line):
    line = re.sub(r'Title:\s+', '', line.strip())    
    if re.search(r'The Spectator\s?\/[^\/]*\/\s?Issue\s?\d\d?', line):
        while 1:
            title = raw_input(Fore.RED + Style.BRIGHT + 'title COULD NOT be found: ')
            if title != '':
                return title
    print(Fore.GREEN + Style.BRIGHT + 'title: ' + Style.RESET_ALL +
          '({}) '.format(line))
    return line


def clean_name(name):
    name = name.replace(' - ', '-')
    # remove nickname formatting e.g. "By Ying Zi (Jessy) Mei"
    name = re.sub(r"\([\w\s-]*\)\s", '', name)
    return name


def get_contributors(byline):
    byline = re.sub(r"By:?", '', byline).strip()
    byline = re.findall(r"[\w']+|[.,!-?;]", byline)
    contributors = []
    cutoff = 0
    """Looks through tokens from left to right until a separator is reached,
    then joins the previous tokens into a name. 
    """
    for i in range(0, len(byline)):
        if byline[i] in ',&' or byline[i] == 'and':
            name = clean_name(' '.join(byline[cutoff:i]))
            contributors.append(name)
            cutoff = i + 1
    contributors.append(clean_name(' '.join(
        byline[cutoff:])))  # add last contributor
    contributors = filter(None, contributors)  # removes empty strings
    print((Fore.GREEN + Style.BRIGHT + 'contributors : ' + Style.RESET_ALL +
           '({0}) ').format(', '.join(contributors)))
    return contributors


def get_summary(line):
    line = re.sub(r"(?i)Focus Sentence:?", '', line).strip()
    print(Fore.GREEN + Style.BRIGHT + 'summary/focus: ' + Style.RESET_ALL +
          '({0}) ').format(line)
    return line


def identify_line_manually(content, missing_value):
    """Takes list of paragraphs and returns user input for the line # of any
    missing_value."""
    print(Fore.RED + Style.BRIGHT + missing_value.upper() +
          ' could not be found. Press ENTER to extend ' +
          'article. Input a line # to indicate ' + missing_value.upper() +
          ', "n" to indicate nonexistence.' + Style.RESET_ALL)
    line_num = 0
    while line_num + 5 < len(content):
        if line_num > 0 and line_num % 5 == 0:
            user_option = raw_input()
            if utils.represents_int(user_option):
                return int(user_option)
            elif user_option != '':
                break
        print('[{}] {}'.format(line_num, content[line_num]))
        line_num += 1
    return -1


HEADER_LINE_PATTERN = re.compile(
    r'Request:|Article:|(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})'
)


def get_content_start(input):
    try:
        header_end = next((index
                           for index, value in enumerate(reversed(input))
                           if HEADER_LINE_PATTERN.search(value)))
        return len(input) - header_end
    except StopIteration:
        return -1


def read_article(text):
    input = filter(None, [line.strip() for line in text.split('\n')])

    if 'draft due' in input[0].lower():
        input = input[1:]

    data = {'title': get_title(input[0]), 'outquotes': []}

    try:
        byline = next((line for line in input if line.find('By') >= 0))
    except StopIteration:
        byline = input[identify_line_manually(input, 'byline')]
    data['contributors'] = get_contributors(byline)

    content_start_index = get_content_start(input)
    if content_start_index == -1:
        content_start_index = identify_line_manually(input, 'content start')

    try:
        summary = next((line for line in input
                        if 'focus sentence:' in line.lower()))
    except StopIteration:
        summary = input[content_start_index]
        summary_words = summary.split(' ')
        if len(summary_words) > 25:
            summary = ' '.join(summary_words[:25]) + "..."
    data['summary'] = get_summary(summary)

    
    paragraphs = input[content_start_index:]
    print(Fore.GREEN + Style.BRIGHT + 'content: ' + Style.RESET_ALL +
          '({}   ...   {}) '.format(paragraphs[0], paragraphs[-1]))
    data['content'] = '<p>' + '</p><p>'.join(paragraphs) + '</p>'

    outquote_index = next((i for i in range(len(input)) if re.findall(r"(?i)outquote\(?s?\)?:?", input[i])), -1)
    if outquote_index != -1:
        while (outquote_index < content_start_index
               and not re.search(r'Request:|Article:|(?i)(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})', input[outquote_index].lower())):        
            line = re.sub(r"(?i)outquote\(?s?\)?:?", '', input[outquote_index])\
                       .strip()
            if line != '':
                data['outquotes'].append(line)
            outquote_index += 1

    print(Fore.GREEN + Style.BRIGHT + 'outquotes: ' +
            Style.RESET_ALL + str(data['outquotes']))

    return data


def read_staff_ed(text):
    input = filter(None, [line.strip() for line in text.split('\n')])

    data = {
        'title': get_title(input[0]),
        'contributors': ["The Editorial Board"],
        'outquotes': []
    }

    paragraphs = filter(None,
                        input[identify_line_manually(input, 'content start'):])
    data['summary'] = paragraphs[0]
    data['content'] = '<p>' + '</p><p>'.join(paragraphs) + '</p>'

    return data


def post_article(data):
    article_response = requests.post(
        constants.API_ARTICLES_ENDPOINT,
        data=json.dumps(data),
        headers={
            'Content-Type': 'application/json'
        })
    article_response.raise_for_status()

    article = article_response.json()
    global articles
    articles.append(article)

    if data['volume'] == 108:
        if data['issue'] == 1:
            created_at = "2017-09-11T17:57:55.149-05:00"
        elif data['issue'] == 2:
            created_at = "2017-09-29T17:57:55.149-05:00"
        elif data['issue'] == 3:
            created_at = "2017-10-17T17:57:55.149-05:00"
        elif data['issue'] == 4:
            created_at = "2017-10-31T17:57:55.149-05:00"
        elif data['issue'] == 5:
            created_at = "2017-11-10T17:57:55.149-05:00"
        requests.put(constants.API_ARTICLES_ENDPOINT + '/' + str(article['id']),
            data=json.dumps({'created_at': created_at}), headers={'Content-Type': 'application/json'})

    return article.get('id', -1)


def remove_article(article_id):
    for article in reversed(articles):
        if article['id'] == article_id:
            articles.remove(article)
            return True
    raise ValueError('No article in local storage with id {}.'.format(article_id))


if __name__ == '__main__':
    constants.init()
    f = open('test.in')
    text = f.read()
    data = read_article(text)
    
