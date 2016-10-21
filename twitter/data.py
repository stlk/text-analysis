'''
Load tweets of users I've liked some of their tweets.

Python: 3.4
'''

import sys, time
import psycopg2
import psycopg2.extras
import settings
from twython import Twython, TwythonRateLimitError, TwythonAuthError

from data_cleanup import cleanup

'''
This function allows us to check the remaining statuses and applications
limits imposed by twitter.
When the app_status or the timeline_status is exhausted, forces a wait
for the period indicated by twitter
'''
def handle_rate_limiting():
    # prepopulating this to make the first 'if' check fail
    app_status = {'remaining':1}
    while True:
        if app_status['remaining'] > 0:
            status = twitter.get_application_rate_limit_status(resources=['statuses', 'application'])
            status = status['resources']
            app_status = status['application']['/application/rate_limit_status']
            timeline_status = status['statuses']['/statuses/user_timeline']
            if timeline_status['remaining'] == 0:
                wait = max(timeline_status['reset'] - time.time(), 0) + 1
                time.sleep(wait)
            else:
                return
        else:
            wait = max(app_status['reset'] - time.time(), 0) + 10
            time.sleep(wait)

# ---------------------------------------------------------
# Connections
# ---------------------------------------------------------

twitter = Twython(settings.APP_KEY, settings.APP_SECRET, oauth_version=2)
ACCESS_TOKEN = twitter.obtain_access_token()
twitter = Twython(settings.APP_KEY, access_token=ACCESS_TOKEN)

conn = psycopg2.connect('dbname={}'.format(settings.DATABASE))
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

screen_name = 'josefrousek' # The main twitter account

# ---------------------------------------------------------
#  Get tweets user has liked
# ---------------------------------------------------------

favorites = twitter.get_favorites(screen_name=screen_name, count=200)

liked_users_ids = [tweet['user']['id'] for tweet in favorites]

# we want only unique records
liked_users_ids = list(set(liked_users_ids))

# add the main twitter account so we can compare distances
me = twitter.show_user(screen_name=screen_name)
liked_users_ids.append(me['id'])

# ---------------------------------------------------------
#  Get 200 tweets per user
#  (200 is the maximum number of tweets imposed by twitter)
# ---------------------------------------------------------

for id in liked_users_ids:
    try:
        print('[Log] loading:', id)

        handle_rate_limiting()
        params = {'user_id': id, 'count': 200, 'contributor_details': 'true' }
        try:
            tl = twitter.get_user_timeline(**params)
        except TwythonAuthError as e:
            pass
        # aggregate tweets
        text = ' '.join([tw['text'] for tw in tl])

        if len(tl) == 0:
            continue

        try:
            item = {
                'raw_text': cleanup(text),
                'user_id': id,
                'n_tweets': len(tl),
                'screen_name': tl[0]['user']['screen_name'],
                'lang': tl[0]['lang'],
            }
        except Exception as e:
            print('[Exception Raised] Eror constructing entity, skipping. %s', e)
            continue

        cur.execute('SELECT n_tweets FROM tweets WHERE user_id = %s', (id, ))
        twt = cur.fetchall()

        if len(twt) == 0:
            cur.execute('''INSERT INTO tweets(raw_text,user_id,n_tweets,screen_name,lang) VALUES (%(raw_text)s, %(user_id)s, %(n_tweets)s, %(screen_name)s, %(lang)s)''', item)
        else:
            cur.execute('''UPDATE tweets SET raw_text=%(raw_text)s, n_tweets=%(n_tweets)s, screen_name=%(screen_name)s, lang=%(lang)s WHERE user_id=%(user_id)s''', item)
            print('replaced id ', tl[0]['user']['screen_name'], id, len(tl), tl[0]['lang'])


    except TwythonRateLimitError as e:
        # Wait if we hit the Rate limit
        reset = int(twitter.get_lastfunction_header('x-rate-limit-reset'))
        wait = max(reset - time.time(), 0) + 10 # addding 10 second pad
        print('[Exception Raised] Rate limit exceeded waiting: %s', wait)
        time.sleep(wait)

conn.commit()

# ---------------------------------------------------------
#  check how many records we now have in the database
# ---------------------------------------------------------

cur.execute('SELECT * FROM tweets')
follower_docs = cur.fetchall()

documents = [tw['raw_text'] for tw in follower_docs]
print('We have ' + str(len(documents)) + ' records.')

n_tweets = sum([tw['n_tweets']  for tw in follower_docs if 'n_tweets' in tw.keys()])
print('Total number of tweets: ', n_tweets)
print('On average #tweets per document: ', n_tweets / len(documents))
