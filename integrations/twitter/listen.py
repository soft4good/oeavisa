import tweepy
import logging
from config import create_api
import time

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger()

def parse_message(message):

def process_mention(api, tweet):
    if not tweet.user.following:
        tweet.user.follow()
    
    

    api.update_status(
        status = "OK!",
        in_reply_to_status_id = tweet.id,
    )
  

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")

    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id = since_id).items():
        logger.info("RECEIVED: " + tweet.text)
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None or tweet.user.id == api.me().id:
            continue
        process_mention(api, tweet)
    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(60)

if __name__ == "__main__":
    main()