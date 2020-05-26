from integration import OeAvisaIntegration
from twitter_integration import TwitterIntegration
import os
import json
import boto3

import logging
from dotenv import load_dotenv
from threading import Thread

log_level = os.getenv('OEAVISA_LOG_LEVEL', logging.INFO)
logging.basicConfig(level = log_level)
logger = logging.getLogger()
load_dotenv()

class OeAvisaIntegrator:
  INTEGRATIONS = {
    'twitter': TwitterIntegration()
  }

  def __init__(self):
    self.queue = boto3.resource('sqs',
      aws_access_key_id     = os.getenv('AWS_ACCESS_KEY_ID'),
      aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
      region_name           = os.getenv('AWS_REGION')
    ).get_queue_by_name(QueueName = os.getenv('SQS_ITEMS_QUEUE'))
    self.consume_sqs_messages()

  def consume_sqs_messages(self):
    while True:
      for message in self.queue.receive_messages():
        logger.debug('RECEIVED SQS MESSAGE: ' + message.body)
        self.process_message(message)
        message.delete()

  def process_message(self, message):
    message = json.loads(message.body)
    for integration in self.INTEGRATIONS.values():
      Thread(target = integration.process_message, args = (message, )).start()

if __name__ == "__main__":
    OeAvisaIntegrator()