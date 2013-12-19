from __future__ import division
import psycopg2
from nltk import sent_tokenize
from nltk.probability import FreqDist
from lxml import etree
import urllib2
import keys
import math

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
for hapax in hapaxes:
    # Remove hapaxes which are only hapaxes because of capitalization
    if hapax.lower() not in lowered_hapax_dict:
        hapaxes.remove(hapax)
print('Number of hapaxes after trimming: ' + str(len(hapaxes)))

def ask_merriam_webster(word):
    url = 'http://www.dictionaryapi.com/api/v1/references/collegiate/xml/' + hapax + '?key=' + merriam_webster_key
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    xml = response.read()
    root = etree.fromstring(xml)
    return root.find('entry')

def getDefinition(word):
    definitionXML = ask_merriam_webster(word)
    if definitionXML is not None:
        return definitionXML.find('def').find('dt').text[1:]
    definitionXML = ask_merriam_webster(word.lower())
    if definitionXML is not None:
        return definitionXML.find('def').find('dt').text[1:]
    else:
        raise ValueError(word + 'is not in dictionary')

# output hapaxes, the url of the column in which they're used, and the definition to a file
output = open('hapaxes', 'w')
merriam_webster_key = keys.dictionary()
for hapax in hapaxes[5000:5010]:
    try:
        definition = getDefinition(hapax)
        print definition
        column_sentences = [sent for sent in sent_tokenize(content_dict[source_dict[hapax][0]])]
        sentence = {
            'text': '', 
            'start': None,
            'length': None
        }
        for sent in column_sentences:
            index = sent.find(hapax)
            if index != -1:
                sentence['text'] = sent
                sentence['start'] = index
                sentence['length'] = len(sent)
                break
        if sentence['length'] <= 102:
            hitchtext = sentence['text']
        elif sentence['start'] < (99 - len(hapax)) / 2:
            hitchtext = sentence['text'][:sentence['text'].rfind(' ', 0, 99)] + '...'
        elif sentence['length'] - sentence['start'] < (99 - len(hapax)) / 2:
            hitchtext = '...' + sentence['text'][sentence['text'].find(' ', sentence['length'] - 99) + 1 :]
        else:
            selection_start = sentence['text'].find(' ', math.ceil(sentence['start'] - (96 - len(hapax)) / 2)) + 1
            selection_end = sentence['text'].rfind(' ', 0, math.floor(sentence['start'] + len(hapax) + (96 - len(hapax)) / 2))
            hitchtext = '...' + sentence['text'][selection_start:selection_end] + '...'
        output.write(hapax + '\n' + source_dict[hapax][0] + '\n' + definition + '\n' + hitchtext + '\n')
    except ValueError:
        print 'No definition for: ' + hapax
output.close()

# Close database connection
cur.close()
conn.close()

# Hitchens' vocabulary
# Remove all encoded characters from corpus_tokenized_lowered
# Create set from that list
