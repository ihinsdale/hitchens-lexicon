import psycopg2
import urllib2, urllib, urlparse
import lxml.html, lxml.cssselect
from nltk import word_tokenize, sent_tokenize

# Connect to database
conn = psycopg2.connect(database="hitch")
cur = conn.cursor()

# Create list of Slate Hitchens archive page urls
pages = ['']
for num in range(2, 17):
    pages.append('.' + str(num))

def date_transform(datetime):
    """datetime should be a string of the form 'JULY 22 2013 5:12 PM',
       returns date in ISO 8601 format, as recommended for Postgres: '2013-07-22'"""
    words = datetime.split()[:3]
    months = {
        'Jan.': '01',
        'Feb.': '02',
        'March': '03',
        'April': '04',
        'May': '05',
        'June': '06',
        'July': '07',
        'Aug.': '08',
        'Sept.': '09',
        'Oct.': '10',
        'Nov.': '11',
        'Dec.': '12'
    }
    try:
        date = words[2] + '-' + months[words[0]] + '-' + words[1]
        return date
    except:
        print 'Error transforming datetime'
        return None

# Create list of article urls
urls = []
headers = {'User-Agent' : 'Mozilla 5.10'}
for page in pages:
    url = 'http://www.slate.com/authors.christopher_hitchens' + page + '.html'
    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    tree = lxml.html.fromstring(response.read())
    tiles = tree.find_class("tile")
    for tile in tiles:
        link = tile.cssselect('a.primary')[0].get('href')
        urls.append(link[0:-4] + 'single.html') # ensures there is no article pagination
print urls

# Save each article to the db
for index, url in enumerate(urls):
    try:
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        tree = lxml.html.fromstring(response.read())
        title = tree.find_class("hed")[0].text_content()
        # also tokenize title
        subtitle = tree.find_class("dek")[0].text_content()
        # also tokenize subtitle
        publication_date = date_transform(tree.find_class("pub-date")[0].text_content())
        text_blocks = tree.find_class("text")
        content = ''
        for block in text_blocks:
            text_content = block.cssselect('p')[0].text_content()
            if not block.cssselect('p > em') or block.cssselect('p > em')[0].text_content() != text_content:
            # this branching necessary to exclude possible italicized description of the article
                content += text_content + ' '
        content_tokenized = [word for sent in sent_tokenize(content) for word in word_tokenize(sent)]
        cur.execute("""INSERT INTO documents (url, title, subtitle, publication_date, content, content_tokenized) VALUES (%s, %s, %s, %s, %s, %s);""", (url, title, subtitle, publication_date, content, content_tokenized))
        conn.commit()
        print index
    except:
        print 'Error saving' + str(index) +': ' + url

# Close database connection
cur.close()
conn.close()
