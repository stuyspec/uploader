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
    if 'Title: ' in line:
        line = line[line.find('Title: ') + len('Title: '):]
    line = line.strip()
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


def get_content_start(input):
    HEADER_LINE_PATTERN = re.compile(
        r'(?i)(outquote(\(s\))?s?:)|(focus sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})|article:?'
    )
    try:
        header_end = next((index
                           for index, value in enumerate(reversed(input))
                           if HEADER_LINE_PATTERN.search(value)))
        return len(input) - header_end
    except StopIteration:
        return -1


def read_article(text):
    input = filter(None, [line.strip() for line in text.split('\n')])

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

    outquote_index = next((i for i in range(len(input)) if re.findall(r"(?i)outquote\(?s\)?:?", input[i])), -1)
    if outquote_index != -1:
        while (outquote_index < content_start_index
               and 'focus sentence:' not in input[outquote_index].lower()):
            line = re.sub(r"(?i)outquote\(?s\)?:?", '', input[outquote_index])\
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
    text="""Assuming Altruism
The Spectator/Opinions/Issue 2
By Jane Rhee
Words: 965
Focus Sentence: The U.S. should adopt a presumed consent organ donation system.
Outquotes:
Ultimately, complete consent and altruism must remain the crux of organ donation. A redesigned standard donation procedure and presumed consent will not change that.
Combating this passivity is the first step the U.S. must take in order to provide transplants for the more than 116,000 people waiting for a donation.

Rafael Matesanz reviews the numbers released by Spain’s Ministry of Health from his office. As the director of the institution in charge of Spain’s organ transplant system, he quickly crunches the numbers—4,360 transplants carried out in 2014 means the organ donation rate has risen from 14 donors per million citizens in the late 20th century to 36 per million. This places Spain at the top of the list in terms of global organ donations, surpassing the United States and France at 26 per million and Germany at 11 per million.

Matesanz does not attribute Spain’s incredible numbers to exceptional citizen altruism. In an interview with Newsweek, when asked if Spanish citizens have a “unique store of generosity,” he shook his head, replying, “We have asked the same question in various surveys over the years and every time 56 percent or 57 percent say they would donate their organs after dying … [that’s] roughly the EU average.” He cites a newly streamlined organ donation process as the key. That, in conjunction with Spain’s donation laws, seems to be the key in attaining such high numbers. Yet the feasibility of the U.S. following such a model remains up in the air.

Currently, the deceased donation system in the U.S. works as follows: you must first sign up to put your name on the donor list with your state’s Organ Donor Registry via the Department of Motor Vehicles. You have the opportunity to choose which tissues or organs you wish to donate as well as the freedom to change your donation status at any time. In the unfortunate instance that you are ever left brain dead, doctors will work in conjunction with a representative from the closest Organ Procurement Organization (OPO) branch (which is a private non-profit organization). Following approval, the OPO will contact the Organ Procurement and Transplantation Network (OPTN), which matches donors to their recipients.

In 2012, the U.S. Department of Health and Human Services conducted a national survey on organ donation behaviors and beliefs. Similar to the proportions in 1993 and 2005, adults in the U.S. consistently maintain a positive view of organ donation, with 94.9 percent supporting or strongly supporting organ donation. That 94.9 percent, however, reveals a stark contrast between ideological beliefs and actual action when you consider that only 60.1 percent of adults have signed up to be a donor. 

Even of those that refused to sign up, only a quarter cited either religion or health as reasons for not donating. The rest reported reasons such as “undecided/don’t know” and “not interested,” demonstrating indifference as opposed to legitimate barriers.

Combating this passivity is the first step the U.S. must take in order to provide transplants for the more than 116,000 people waiting for a donation. But history makes it clear that passivity—in the face of the most recent presidential election—is going nowhere. It then follows that one viable option is to implement the presumed consent system.

Presumed consent, a system that France implemented earlier this year, is also known as an “opt-out” system, meaning that it is assumed all citizens wish to donate unless they explicitly state they do not wish to. And in the first few days, only 150,000 people out of the population of 66 million opted out. 

Not only does presumed consent battle passivity, it also changes the context in which we view organ donation. A 2012 study done by researchers at Cornell University and Stanford University revealed that in an “opt-in” system, like that of the U.S., citizens see organ donation as an “exceptional act of altruism.” Yet in an “opt-out” system, the refusal to donate becomes the exceptional act. In other words, the “opt-in” system is like leaving your entire estate to charity. The “opt-out” system is like skipping your daughter’s wedding to sleep in. The former requires some hint of virtue, while the latter is simply a given.

The second thing we must do is aim to focus our efforts on education and efficiency. The benefits and risks of organ donations must be taught to students before they make the personal decision to remove their names from the list of potential donors. In addition, the idea that Americans and their families will lose freedom over their bodies after death must be set straight. In reality, doctors in the U.S. will respect the family’s ultimate decision as they determine what will happen with their kin’s body. This is due to a few factors, including a combination of fear of legal conflict and bad publicity, as well as an understanding that keeping the body intact may bring the family closure. 

Looking to Spain as the model of efficiency, the country has implemented an initiative to train 16,000 professionals to be both transplant coordinators and internal care specialists, instead of having to tread through the complex networks of hospitals and outside organizations. Germany especially has an extremely low donation record because of an “uncontrollably complex web of private clinics and insurance firms.” The U.S. must ensure that the OPO and OPTN work not as private companies with a government affiliation, but transparent government branches with more uniform standards and training methods for staff. Though this will require an investment of time and resources, it will prevent viable donations from slipping through the cracks that our inefficient system currently has. 

Ultimately, complete consent and altruism must remain the crux of organ donation. A redesigned standard donation procedure and presumed consent will not change that.
"""
    data = read_article(text)
    requests.post(
        constants.API_ARTICLES_ENDPOINT,
        data=json.dumps(data),
        headers={
            'Content-Type': 'application/json'
        })
    
