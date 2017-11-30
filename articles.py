from colorama import Fore, Back, Style
import re
import requests
import constants
import utils
import json

articles = []


def init():
    global articles
    print('[0%] Loading articles.\r'),  # comma lets next print overwrite.
    articles = requests.get(constants.API_ARTICLES_ENDPOINT).json()
    print('[100%] Loaded articles.')


def does_file_exist(raw_text):
    file_content = unicode(raw_text, 'utf-8')
    for a in articles:
        last_pgraph = unicode(a['content'].split('</p><p>')[-1])
        if last_pgraph[:-len('</p>')] in file_content:
            return True
    return False


def remove_article(article_id):
    for article in reversed(articles):
        if article['id'] == article_id:
            articles.remove(article)
            return True
    raise ValueError('No article in local storage with id {}.'.format(article_id))


def analyze_article(raw_text):
    lines = filter(None, [line.strip() for line in raw_text.split('\n')])
    data = {
        'title': utils.get_title(lines[0]),
        'outquotes': []
    }

    try:
        byline = next((line for line in lines if line.find('By') >= 0))
    except StopIteration:
        byline = lines[utils.identify_line_manually(lines, 'byline')]
    data['contributors'] = utils.get_contributors(byline)

    content_start_index = utils.get_content_start(lines)
    if content_start_index == -1:
        content_start_index = utils.identify_line_manually(lines, 'content start')
    try:
        summary = next((line for line in lines
                        if 'focus sentence:' in line.lower()))
    except StopIteration:
        summary = lines[content_start_index]
        summary_words = summary.split(' ')
        if len(summary_words) > 25:
            summary = ' '.join(summary_words[:25]) + "..."
    data['summary'] = utils.get_summary(summary)


    paragraphs = lines[content_start_index:]
    print(Fore.GREEN + Style.BRIGHT + 'content: ' + Style.RESET_ALL +
          '({}   ...   {}) '.format(paragraphs[0], paragraphs[-1]))
    data['content'] = '<p>' + '</p><p>'.join(paragraphs) + '</p>'

    try:
        outquote_index = next((
            i for i in range(len(lines))
            if re.findall(r"(?i)outquote\(?s?\)?:?", lines[i])))
        while (outquote_index < content_start_index
               and not re.search(r'Request:|Article:|(?i)(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})', lines[outquote_index].lower())):
            line = re.sub(r"(?i)outquote\(?s?\)?:?", '', lines[outquote_index])\
                       .strip()
            if line != '':
                data['outquotes'].append(line)
            outquote_index += 1
    except StopIteration:
        pass

    print(Fore.GREEN + Style.BRIGHT + 'outquotes: ' +
            Style.RESET_ALL + str(data['outquotes']))

    return data


def post_authorships(authorship_data):
    article_id, contributor_ids = authorship_data
    for c in contributor_ids:
        utils.post_modify_headers(
            constants.API_AUTHORSHIPS_ENDPOINT,
            data=json.dumps({
                'article_id': article_id,
                'user_id': c
            }))
    return article_id


def post_outquotes(article_data):
    for outquote in article_data['outquotes']:
        utils.post_modify_headers(
            constants.API_OUTQUOTES_ENDPOINT,
            data=json.dumps({
                'article_id': article_data['id'],
                'text': outquote.decode('utf-8')
            }))
    return article_data['id']