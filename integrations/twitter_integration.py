import time, os, json, logging, random, tweepy
from threading import Thread
from dotenv import load_dotenv

load_dotenv(dotenv_path= '.twitter.env')
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger()

from integration import OeAvisaIntegration

class OeAvisaStreamListener(tweepy.StreamListener):
  def __init__(self, api, callback):
    self.api = api
    self.me = api.me()
    self.callback = callback

  def on_status(self, status):
    self.callback(status)

class TwitterIntegration(OeAvisaIntegration):
  NAME = 'twitter'

  TW_SCREEN_NAME = 'OeAvisa'
  TW_HANDLE = '@oeavisa'

  FOLLOW_ME_MESSAGE = " Sígueme pa' poder notificarte! ;)" # TODO: use emoji :D
  FOLLOW_ME_ON_HIT  = "Tengo pa' tí. Sígueme pa' poder notificarte! ;)"

  def __init__(self):
    logger.info('TWITTER Initializing...')
    super().__init__()
    self.api = self.create_api()
    tweepy.Stream(
      auth     = self.api.auth,
      listener = OeAvisaStreamListener(self.api, self.process_mention)
    ).filter(track = [self.TW_SCREEN_NAME], is_async = True)

    Thread(target = self.consume_direct_messages).start()

  def cleanup_message(self, message):
      message = message.lower().replace(self.TW_HANDLE, '')
      return super().cleanup_str(message)
  

  def process_tweet(self, tweet):
    clean_message = self.cleanup_message(tweet.text)
    logger.info(f'TWITTER_PROCESS_TWEET (clean): {clean_message}')

    response = self.CANNED_RESPONSES.get(clean_message)
    if response is None:
      self.register_query(clean_message, f'{tweet.id}:{tweet.user.id}:{tweet.user.screen_name}')
      response = random.sample(self.RESPONSES, 1)[0]

    return response


  def process_direct_message(self, message):
    clean_message = self.cleanup_message(message.message_create['message_data']['text'])

    sender_id = message.message_create['sender_id']
    response = self.CANNED_RESPONSES.get(clean_message)
    
    if response is None and str(self.api.me().id) != str(sender_id):
      logger.info(f'TWITTER_PROCESS_DIRECT_MESSAGE (clean): {clean_message}')
      user = self.api.get_user(sender_id)
      self.register_query(clean_message, f'{message.id}:{user.id}:{user.screen_name}')
    
    if response is None: response = random.sample(self.RESPONSES, 1)[0]
    
    try:
      self.api.send_direct_message(sender_id, response)
      self.api.destroy_direct_message(message.id)
    except Exception as error:
      logger.error(f'TWITTER_PROCESS_DIRECT_MESSAGE {error}')


  def process_mention(self, tweet):
    mentions = list( map(lambda x: x['screen_name'], tweet.entities['user_mentions']) )
    
    if len(mentions) == 1 and self.TW_SCREEN_NAME in mentions:
      logger.info(f'TWITTER_PROCESS_MENTION Found mention: {tweet.text}')
      
      if not tweet.user.following: tweet.user.follow() # follow user
      
      try:
        response = self.process_tweet(tweet)
        self.api.update_status( # respond to user
          status = f'@{tweet.user.screen_name} {response}',
          in_reply_to_status_id = tweet.id,
        )
      except tweepy.TweepError as error:
        if error.api_code == 187:
          logger.warning('TWITTER_PROCESS_MENTION Duplicate message.')
        else:
          raise error

  def process_hit(self, hit, subscriber):
    tweet_id, user_id, screen_name = subscriber.split(':')
    logger.info('TWITTER_PROCESS_HIT Handle: ' + subscriber)
    logger.info(f'TWITTER_PROCESS_HIT Response: {self.hit_response(hit)}')
    try:
      self.api.send_direct_message(user_id, self.hit_response(hit)) # respond to user with hit
      return True
    except tweepy.TweepError as error:
      if error.api_code != 226: # This request looks like it might be automated. To protect our users from spam...
        try:
          self.api.update_status( # respond to user asking to follow
            status = f"@{screen_name} {self.FOLLOW_ME_ON_HIT}",
            in_reply_to_status_id = tweet_id,
          )
        except Exception as error:
          logger.warning(f'TWITTER_PROCESS_HIT {error}')
      return False

  def consume_direct_messages(self):
    while True:
      time.sleep(60)
      logger.info('TWITTER_CONSUME_DIRECT_MESSAGE Starting...')
      
      messages = self.api.list_direct_messages()
      for message in messages:
        time.sleep(5)
        try:
          self.process_direct_message(message)
        except Exception as error:
          logger.error(f'TWITTER_CONSUME_DIRECT_MESSAGE {error}')
    

  def create_api(self):
    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth, 
      wait_on_rate_limit        = True, 
      wait_on_rate_limit_notify = True
    )

    try:
      api.verify_credentials()
    except Exception as e:
      logger.error("TWITTER_CREATE_API Error creating API", exc_info=True)
      raise e
    
    logger.info("TWITTER_CREATE_API Created!")
    
    return api