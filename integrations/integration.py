import os
import re
import time
import json
import redis
from Levenshtein import *
from dotenv import load_dotenv
import logging
import boto3
from threading import Thread

load_dotenv()
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger()

# Inherit from this class, call register_query() set NAME and implement process_hit()
class OeAvisaIntegration:
  NAME = '' # set this!

  STOP_WORDS = 'a ante bajo cabe con contra de desde durante en entre hacia hasta mediante para por según sin so sobre tras versus vía el la los las un una unos unas al del lo y e ni que pero más mas aunque sino siquiera o u ora sea bien ya cerca lejos este aquel pues porque puesto como más igual menos así si no tal aunque pesar cuando mientras antes apenas te mi'

  RESPONSES = [
    'dale te aviso!',
    'oka!',
    'voy a fijarme y te aviso.',
    'ok, te digo cuando eso.',
    'tu lo sabe, si aparece te tiro.',
    'ya, no te preocupes mi herma.',
    'OK, tirado x la planta.',
    'anotado, el mío.'
  ]

  CANNED_RESPONSES = {
    '':      'el qué? no te entendí',
    'ping':  'pong',
    'harry': 'potter'
  }

  HIT_RESPONSE = 'oe, apareció %s en %s, %s. Míralo aquí: %s'

  def __init__(self):
    self.redis = redis.Redis(
      host     = os.getenv('REDIS_HOST'), 
      port     = os.getenv('REDIS_PORT'), 
      password = os.getenv('REDIS_PASSWORD'),
    )

  def integration_key(self):
    return f'oeavisa:{self.NAME}:'

  # call this to register your queries
  # query:  String - The query string
  # subscriber: String - We will send you this back on process_hit
  def register_query(self, query, subscriber):
    query = self.cleanup_str(query)
    self.redis.sadd(f'{self.integration_key()}{query}', subscriber)

  # implement this!
  def process_hit(self, hit, subscriber):
    pass


  def cleanup_str(self, string):
    stop_words = self.STOP_WORDS.split()
    words = list( dict.fromkeys( str(string).lower().strip().split() ) )    
    words = ' '.join([word for word in words if word not in stop_words])
    return re.sub('[^A-Za-z0-9ñáéíóú]+', ' ', words).strip()  
  
  def hit_response(self, hit):
    return self.HIT_RESPONSE % (
      hit['name'], 
      hit['store'], 
      hit['province'], 
      hit['url']
    )

  def process_message(self, message):
    message_str = " ".join([message['name'], message['store'], message['province']])
    message_str = self.cleanup_str(message_str)
    logger.info(f"INTEGRATION_PROCESS_MESSAGE {message_str} | {message['store']} | {message['province']}")
    
    for key in self.redis.scan_iter(f'{self.integration_key()}*'):
      query = str(key.decode('utf-8')).replace(self.integration_key(), '')
      
      # TODO: implement search unsing (at least) levensthein distance
      matching_words = set(query.split()) & set(message_str.split())
      is_hit = len(matching_words) == len(query.split())
      
      if is_hit:
        logger.info(f'INTEGRATION_PROCESS_MESSAGE HIT!! {query} | {message_str}')
        all_notified = True
        for subscriber in self.redis.smembers(key):
          try:
            success = self.process_hit(message, subscriber.decode('utf-8'))
          except Exception as error:
            logger.error(f'INTEGRATION_PROCESS_MESSAGE {error}')
            success = False
          
          if success: self.redis.srem(key, subscriber) 
          
          all_notified = all_notified and success
        
        if all_notified:
          self.redis.delete(key) # query satisfied -> delete
          logger.info(f'INTEGRATION_PROCESS_MESSAGE Query Satisfied (deleted): {query}')
