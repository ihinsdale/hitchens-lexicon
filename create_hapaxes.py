from __future__ import division
import psycopg2
from nltk import sent_tokenize
from nltk.probability import FreqDist
import lxml.html
import urllib2
import math
import json
import re
import io

# Connect to db
conn = psycopg2.connect(host="127.0.0.1",database="hitch")
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
corpus_tokenized_lowered = []
for token in corpus_tokenized:
    corpus_tokenized_lowered.append(token.lower())
fdist = FreqDist(corpus_tokenized)
fdist_lowered = FreqDist(corpus_tokenized_lowered)
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

def define(word):
    try:
        url = 'http://www.google.com/dictionary/json?callback=a&sl=en&tl=en&q=' + word
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        jsonstring = '[' + response.read()[2:-1] + ']'
        data = json.loads(jsonstring)
        # Get first definition of the word
        for entry in data[0]['primaries'][0]['entries']:
            if entry['type'] == 'meaning':
                # Clean the definition of any html
                html = lxml.html.fragment_fromstring('<p>' + entry['terms'][0]['text'] + '</p>')
                definition = html.text_content()
                break
        return definition.encode('utf8')
    except:
       raise ValueError(word + 'is not in dictionary')

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

# output hapaxes, the url of the column in which they're used, and the definition to a file
output = io.open('hapaxes', 'w', encoding='utf8')
for hapax in hapaxes:
    try:
        full_definition = define(hapax)
        definition = truncate(full_definition, 0, 103)
        def_url = 'https://www.google.com/#q=define:+' + hapax
        column_sentences = [sent for sent in sent_tokenize(content_dict[source_dict[hapax][0]])]
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
        hitchtext = truncate(sentence['text'], sentence['start'], 94)
        block = unicode(hapax + '\n' + definition + '\n' + def_url + '\n' + hitchtext + '\n' + source_dict[hapax][0] + '\n', encoding='utf8')
        output.write(block)
        print hapax
        print definition
    except ValueError:
       print 'No definition for: ' + hapax
output.close()

# Close database connection
cur.close()
conn.close()

# Hitchens' vocabulary
vocabulary = set(corpus_tokenized_lowered)
print len(vocabulary) # 31,222 seems much too small