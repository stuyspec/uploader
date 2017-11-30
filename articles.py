#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from colorama import init, Fore, Back, Style
init()

import re, requests, json, ast
import constants, utils, main, config, drive, media, sections

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
        last_pgraph = unicode(existing_article['content'].split('</p><p>')[-1])
        if last_pgraph[:-len('</p>')] in file_content:
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
    byline = re.findall(r"[\w\p{L}\p{M}']+|[.,!-?;]", byline)

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


HEADER_LINE_PATTERN = re.compile(
    r'Request:|Article:|(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})'
)


def identify_line_manually(lines, missing_value):
    """Takes list of paragraphs and returns user input for the line # of any
    missing_value."""
    print(Fore.RED + Style.BRIGHT + missing_value.upper() +
          ' could not be found. Press ENTER to extend ' +
          'article. Input a line # to indicate ' + missing_value.upper() +
          ', "n" to indicate nonexistence.' + Style.RESET_ALL)
    line_num = 0
    while line_num + 5 < len(lines):
        if line_num > 0 and line_num % 5 == 0:
            user_option = raw_input()
            if utils.represents_int(user_option):
                return int(user_option)
            elif user_option != '':
                break
        print('[{}] {}'.format(line_num, lines[line_num]))
        line_num += 1

    print('\n[**INITIAL SCANNING FAILED**]\n')
    line_num = 0
    for line_num in range(len(lines)):
        print('[{}] {}'.format(line_num, lines[line_num]))
    while 1:
        user_option = raw_input()
        if utils.represents_int(user_option):
            return int(user_option)
        elif user_option != '':
            break
    return -1


def get_content_start(lines):
    try:
        header_end = next((index
                           for index, value in enumerate(reversed(lines))
                           if HEADER_LINE_PATTERN.search(value)))
        return len(lines) - header_end
    except StopIteration:
        return -1


def read_article(text):
    lines = filter(None, [line.strip() for line in text.split('\n')])

    if 'draft due' in lines[0].lower():
        lines = lines[1:]

    data = {'title': get_title(lines[0]), 'outquotes': []}

    try:
        byline = next((line for line in lines if line.find('By') >= 0))
    except StopIteration:
        byline = lines[identify_line_manually(lines, 'byline')]
    data['contributors'] = get_contributors(byline)

    content_start_index = get_content_start(lines)
    if content_start_index == -1:
        content_start_index = identify_line_manually(lines, 'content start')

    try:
        summary = next((line for line in lines
                        if 'focus sentence:' in line.lower()))
    except StopIteration:
        summary = lines[content_start_index]
        summary_words = summary.split(' ')
        if len(summary_words) > 25:
            summary = ' '.join(summary_words[:25]) + "..."
    data['summary'] = get_summary(summary)

    
    paragraphs = lines[content_start_index:]
    print(Fore.GREEN + Style.BRIGHT + 'content: ' + Style.RESET_ALL +
          '({}   ...   {}) '.format(paragraphs[0], paragraphs[-1]))
    data['content'] = '<p>' + '</p><p>'.join(paragraphs) + '</p>'

    outquote_index = next((i for i in range(len(lines)) if re.findall(r"(?i)outquote\(?s?\)?:?", lines[i])), -1)
    if outquote_index != -1:
        while (outquote_index < content_start_index
               and not re.search(r'Request:|Article:|(?i)(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})', lines[outquote_index].lower())):        
            line = re.sub(r"(?i)outquote\(?s?\)?:?", '', lines[outquote_index])\
                       .strip()
            if line != '':
                data['outquotes'].append(line)
            outquote_index += 1

    print(Fore.GREEN + Style.BRIGHT + 'outquotes: ' +
            Style.RESET_ALL + str(data['outquotes']))

    return data


def read_staff_ed(text):
    lines = filter(None, [line.strip() for line in text.split('\n')])

    data = {
        'title': get_title(lines[0]),
        'contributors': ["The Editorial Board"],
        'outquotes': []
    }

    paragraphs = filter(None,
                        lines[identify_line_manually(lines, 'content start'):])
    data['summary'] = paragraphs[0]
    data['content'] = '<p>' + '</p><p>'.join(paragraphs) + '</p>'

    return data

def post_article(data):
    created_at = None
    if data['volume'] == 107:
        if data['issue'] == 16:
            created_at = "2017-06-09T17:57:55.149-05:00"
        elif data['issue'] == 15:
            created_at = "2017-05-26T17:57:55.149-05:00"
        elif data['issue'] == 14:
            created_at = "2017-05-08T17:57:55.149-05:00"
        elif data['issue'] == 13:
            created_at = "2017-04-21T17:57:55.149-05:00"
        elif data['issue'] == 12:
            created_at = "2017-03-31T17:57:55.149-05:00"
        elif data['issue'] == 11:
            created_at = "2017-03-10T17:57:55.149-05:00"

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

    if created_at is None:
        raise ValueError('No created_at for Volume {} Issue {}.'.format(data['volume'], data['issue']))
    data['created_at'] = created_at
    data['section_id'] = 27
    article_response = requests.post(
        constants.API_ARTICLES_ENDPOINT,
        data=json.dumps(data),
        headers=config.headers)
    article_response.raise_for_status()

    main.updateHeaders(article_response)

    article = article_response.json()
    global articles
    articles.append(article)
    return article.get('id', -1)


def remove_first_paragraph(article_id):
    article_response = requests.get(constants.API_ARTICLES_ENDPOINT + '/' + str(article_id))


def add_reference(article_id, reference_id):
    article_response = requests.get(constants.API_ARTICLES_ENDPOINT + '/' + str(article_id))
    article_response.raise_for_status()
    content = article_response.json()['content']
    content = '<spec-reference id={}></spec-reference>'.format(reference_id) + content
    return update_article(article_id, {'content': content})


def remove_reference(article_id):
    article_response = requests.get(constants.API_ARTICLES_ENDPOINT + '/' + str(article_id))
    article_response.raise_for_status()
    content = article_response.json()['content']
    content = re.sub(r"<spec-reference id=(\d*)><\/spec-reference>", '', content)
    return update_article(article_id, {'content': content})


def edit_content(article_id):
    article_response = requests.get(constants.API_ARTICLES_ENDPOINT + '/' + str(article_id))
    article_response.raise_for_status()
    content = article_response.json()['content']
    f = open('editing.in', 'w')
    f.write(content.encode('utf-8'))
    f.close()
    raw_input('Content has been written to editing.in. Press ENTER when editing is completed.')
    f = open('editing.in', 'r')
    new_content = f.read()
    f.close()
    return update_article(article_id, {'content': content})


def make_article_carousel(article_id):
    article_response = requests.get(constants.API_ARTICLES_ENDPOINT + '/' + str(article_id))
    article_response.raise_for_status()
    content = article_response.json()['content']
    content = '<spec-img-carousel></spec-img-carousel>' + content
    return update_article(article_id, {'content': content})


def update_article(article_id, data):
    article_response = requests.put(
        constants.API_ARTICLES_ENDPOINT + '/' + str(article_id),
        data=json.dumps(data),
        headers={
            'Content-Type': 'application/json'
        })
    article_response.raise_for_status()
    return article_response.json().get('id', -1)


def clear_summary(article_id):
    return update_article(article_id, {'summary': ''})


def remove_article(article_id):
    for article in reversed(articles):
        if article['id'] == article_id:
            articles.remove(article)
            return True
    raise ValueError('No article in local storage with id {}.'.format(article_id))


def process_article(drive_file, section_name, media_files=[]):
    filename = drive_file['name']

    file_unwanted = re.search(r"(?i)worldbeat|survey|newsbeat|spookbeat",
                              filename)
    if file_unwanted:
        print(Fore.RED + Style.BRIGHT + file_unwanted.group().upper() +
              ' skipped.' + Style.RESET_ALL)
        return 'SKIP'

    print(
        Fore.CYAN + Style.BRIGHT + section_name.upper() +
        Fore.BLUE + ' ' + filename + Style.RESET_ALL,
        end=' ')
    raw_text = drive.download_document(drive_file)

    if file_article_exists(raw_text):
        print(Fore.RED + Style.BRIGHT + filename.encode("utf-8")
              + ' already exists.' + Style.RESET_ALL)
        raise ValueError('EXISTING ARTICLE')
    if re.search(r'(?i)staff\s?ed', filename):
        article_data = read_staff_ed(raw_text)
    else:
        article_data = read_article((raw_text))

    images = media.choose_media(media_files)

    if section_name == 'Humor':
        if config.issue == 4:
            section_name = 'Spooktator'
        if config.issue == 12:
            section_name = 'Disrespectator'
    elif re.search(r'(?i)staff\s?ed', filename):
        section_name = 'Staff Editorials'
    section_id = sections.choose_subsection(section_name)

    article_data['id'] = post_article({
        'title': article_data['title'],
        'content': article_data['content'],
        'summary': article_data['summary'],
        'volume': config.volume,
        'issue': config.issue,
        'section_id': section_id
    })

    # LEFt OFF here

    def rollback(res):
        try:
            print(Fore.RED + Style.BRIGHT + '\nCaught error: {}.'.format(res) + Style.RESET_ALL)
            remove_article(article_data['id'])
            destroy_response = requests.delete(
                constants.API_ARTICLES_ENDPOINT + '/{}'.format(
                    article_data['id']), config.headers)
            destroy_response.raise_for_status()
            config.update_headers(destroy_response)
            return True
        except Exception as e:
            print('Rollback failed with {}. Article {} remains evilly.'
                  .format(e, article_data['id']))

    article_promise = Promise(
        lambda resolve, reject: resolve(users.post_contributors(article_data))) \
        .then(lambda authorship_data:
              authorships.post_authorships(authorship_data)) \
        .then(lambda res: outquotes.post_outquotes(article_data)) \
        .then(lambda article_id:
              media.post_media(article_id, images)) \
        .then(lambda article_id: print(
        Fore.GREEN + Style.BRIGHT
        + '\nSuccessfully wrote Article #{}: {}.'
        .format(article_data['id'], article_data['title'])
        + Style.RESET_ALL)) \
        .catch(lambda res: rollback(res))

    result = article_promise.get()
    if result is not None and result is True:
        raise ValueError('ROLLBACK')