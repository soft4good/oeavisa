import tweepy
import logging
from config import create_api
import time
import random
from Levenshtein import *
import redis

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger()
r = redis.Redis(host='localhost', port=6379, db=0) # TODO: use .env

TW_HANDLE = '@oeavisa'

STOP_WORDS = TW_HANDLE + ' a ante bajo cabe con contra de desde durante en entre hacia hasta mediante para por según sin so sobre tras versus vía el la los las un una unos unas al del lo y e ni que pero más mas aunque sino siquiera o u ora sea bien ya cerca lejos este aquel pues porque puesto como más igual menos así si no tal aunque pesar cuando mientras antes apenas'

RESPONSES = [
    'dale te aviso',
    'oka!',
    'voy a fijarme y te aviso',
    'ok, te digo cuando eso',
    'tu lo sabe, si aparece te tiro'
]

CANNED_RESPONSES = {
    '':      'el qué? no te entendí',
    'ping':  'pong',
    'harry': 'potter'
}

# https://stackoverflow.com/questions/25346058/removing-list-of-words-from-a-string
def cleanup_message(message):
    query_words = message.lower().strip().split()
    stop_words  = STOP_WORDS.split()
    return ' '.join([word for word in query_words if word not in stop_words])

def process_message(tweet, api):
    logger.info("RECEIVED: " + tweet.text)
    clean_message = cleanup_message(tweet.text)
    logger.info("RECEIVED (clean): " + clean_message)

    response = CANNED_RESPONSES.get(clean_message)
    if response is None:
        r.sadd(clean_message, str(tweet.id) + ':' + tweet.user.screen_name)
        response = random.sample(RESPONSES, 1)[0]
    return response


def process_mention(tweet, api):
    if not tweet.user.following:
        tweet.user.follow()
    
    try:
        response = process_message(tweet, api)
        api.update_status(
            status = "@" + tweet.user.screen_name + " " + response,
            in_reply_to_status_id = tweet.id,
        )
    except tweepy.TweepError as error:
        if error.api_code == 187:
            logger.warning('Duplicate message.')
        else:
            raise error

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")

    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id = since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None or tweet.user.id == api.me().id:
            continue
        process_mention(tweet, api)
    
    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(20)

if __name__ == "__main__":
    main()