from __future__ import division
import psycopg2
from nltk import sent_tokenize
from nltk.probability import FreqDist
import lxml.html
import urllib2
import math, random
import json
import re
import io
import tweepy
import keys


# Connect to db
conn = psycopg2.connect(database="hitch",user="postgres")
cur = conn.cursor()

# Create corpus
cur.execute("SELECT url, content, content_tokenized FROM documents")
columns = cur.fetchall()
print 'Number of Slate columns in db: ' + str(len(columns))
corpus = ''
corpus_tokenized = []
source_dict = {}
content_dict = {}
for column in columns:
    url = column[0]
    content = column[1]
    tokens = column[2]
    content_dict[url] = content
    corpus += content
    corpus_tokenized += tokens
    for token in tokens:
        if token in source_dict:
            if len(source_dict[token]) < 5:
                source_dict[token].append(column[0])
        else:
            source_dict[token] = [column[0]]
print 'Number of types (words + punctuation) in corpus: ' + str(len(corpus_tokenized))

# Identify hapaxes

# Remove tokens which contain non-ASCII characters
# or which contain digits
_digits = re.compile('\d')
def contains_digits(d):
    return bool(_digits.search(d))

ascii_tokens = []
for token in corpus_tokenized:
    try:
        token.decode('ascii')
        if not contains_digits(token):
            ascii_tokens.append(token)
    except:
        continue

ascii_tokens_lowered = []
for token in ascii_tokens:
    ascii_tokens_lowered.append(token.lower())
fdist = FreqDist(ascii_tokens)
fdist_lowered = FreqDist(ascii_tokens_lowered)
hapaxes = fdist.hapaxes()
print('Number of hapaxes before trimming: ' + str(len(hapaxes)))
lowered_hapaxes = fdist_lowered.hapaxes()
lowered_hapax_dict = {}
for lowered_hapax in lowered_hapaxes:
    lowered_hapax_dict[lowered_hapax] = True
tmp_hapaxes = [] # necessary because removing from hapaxes while looping through it caused subtle bug
for hapax in hapaxes:
    # Remove hapaxes which are only hapaxes because of capitalization
    if hapax.lower() in lowered_hapax_dict:
        tmp_hapaxes.append(hapax)
hapaxes = tmp_hapaxes
print('Number of hapaxes after trimming: ' + str(len(hapaxes)))

# Tweet a random hapax

# Setup Twitter client
twitter_keys = keys.twitter()
print twitter_keys

CONSUMER_KEY = twitter_keys['CONSUMER_KEY']
CONSUMER_SECRET = twitter_keys['CONSUMER_SECRET']
ACCESS_KEY = twitter_keys['ACCESS_KEY']
ACCESS_SECRET = twitter_keys['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# Define helper functions to define a hapax, clean its definition and truncate,
# find its context in Hitchens' column and truncate
def asciirepl(match):
  s = match.group()  
  return '\\u00' + match.group()[2:]

def define(word):
    url = 'http://www.google.com/dictionary/json?callback=a&sl=en&tl=en&q=' + word + '&restrict=pr%2Cde&client=te'
    headers = {'User-Agent' : 'Mozilla 5.10'}
    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    jsonstring = '[' + response.read()[2:-1] + ']'
    #To replace hex characters with ascii characters
    response = re.compile(r'\\x(\w{2})')
    ascii_string = response.sub(asciirepl, jsonstring)
    data = json.loads(ascii_string)
    try:
        defs = data[0]['primaries'][0]['entries']
    except KeyError:
        try:
            defs = data[0]['webDefinitions'][0]['entries']
        except KeyError:
            raise ValueError('no definition')
    # Get first definition of the word
    for entry in defs:
        if entry['type'] == 'meaning':
            # Clean the definition of any html
            html = lxml.html.fragment_fromstring('<p>' + entry['terms'][0]['text'] + '</p>')
            definition = html.text_content()
            break
    return definition.encode('utf8')

def truncate(sentence, keyword_start, max_length):
    """returns a truncated version of a sentence: only complete words, with ellipses as necessary,
       and defaults to equal length on either side of keyword in sentence"""
    length = len(sentence)
    ellipsis_length = 3
    max_length_one_ellipsis = max_length - ellipsis_length
    max_length_two_ellipsis = max_length - 2 * ellipsis_length
    if length <= max_length:
        result = sentence
    elif keyword_start < (max_length_one_ellipsis - len(hapax)) / 2:
        result = sentence[:sentence.rfind(' ', 0, max_length_one_ellipsis)] + '...'
    elif length - keyword_start < (max_length_one_ellipsis - len(hapax)) / 2:
        result = '...' + sentence[sentence.find(' ', length - max_length_one_ellipsis) + 1 :]
    else:
        selection_start = sentence.find(' ', int(math.ceil(keyword_start - (max_length_two_ellipsis - len(hapax)) / 2))) + 1
        selection_end = sentence.rfind(' ', 0, int(math.floor(keyword_start + len(hapax) + (max_length_two_ellipsis - len(hapax)) / 2)))
        result = '...' + sentence[selection_start:selection_end] + '...'
    return result

# Tweet a hapax
def tweet_hapax(hapax, column, column_url, tweepy_api):
    """arguments should be strings"""
    print 'inside tweet hapax'
    full_definition = define(hapax)
    definition = truncate(full_definition, 0, 105 - len(hapax))
    print definition
    def_url = 'https://www.google.com/#q=define:+' + hapax
    column_sentences = [sent for sent in sent_tokenize(column)]
    sentence = {
        'text': '', 
        'start': None
    }
    for sent in column_sentences:
        index = sent.find(hapax)
        if index != -1:
            sentence['text'] = sent
            sentence['start'] = index
            break
    hitchtext = truncate(sentence['text'], sentence['start'], 94).encode('utf8') # encode as utf-8
    tweet1 = hapax.upper() + ': 1. ' + definition + ' ' + def_url + ' (1/2)'
    tweet2 = 'perhaps as in, "' + hitchtext + '" ' + column_url + ' (2/2)'
    tweepy_api.update_status(tweet1)
    tweepy_api.update_status(tweet2)
    print 'Successfully tweeted hapax:', hapax
    return

def try_up_to_5_times():
    for each in range(5):
        try:
            random_hapax = hapaxes[int(math.floor(random.random() * len(hapaxes)))]
            random_hapaxs_column = content_dict[source_dict[random_hapax][0]]
            random_hapaxs_column_url = source_dict[random_hapax][0]
            tweet_hapax(random_hapax, random_hapaxs_column, random_hapaxs_column_url, api)
            return
        except:
            continue
    return

try_up_to_5_times()

# Close database connection
cur.close()
conn.close()
