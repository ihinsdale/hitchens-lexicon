import tweepy
import keys
import io
import math, random

# Setup Twitter client
twitter_keys = keys.twitter()

CONSUMER_KEY = twitter_keys['CONSUMER_KEY']
CONSUMER_SECRET = twitter_keys['CONSUMER_SECRET']
ACCESS_KEY = twitter_keys['ACCESS_KEY']
ACCESS_SECRET = twitter_keys['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# Open hapaxes file and select one
hapaxes = io.open('hapaxes', 'r', encoding='utf8')

def file_len(open_file):
    i = -1
    for i, l in enumerate(open_file):
        pass
    return i + 1

starting_line = int(math.floor(random.random() * (file_len(hapaxes) - 5)))
hapaxes.close()
hapaxes = io.open('hapaxes', 'r', encoding='utf8')

print hapaxes
for index, line in enumerate(hapaxes):
    if index >= starting_line and index < starting_line + 5:
        print line

hapaxes.close()

#api.update_status(sys.argv[1])