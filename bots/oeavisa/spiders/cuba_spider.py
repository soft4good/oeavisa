import scrapy
from datetime import datetime
import os
import logging

from oeavisa.items  import OeAvisaProduct#, OeAvisaRssItem
from oeavisa.stores import foreignStores, cuStores, testStores

class EnviosCubaSpider(scrapy.Spider):
  name = "cuba"

  def envStores(self):
    env = os.getenv('OEAVISA_ENV')
    return {'cu': cuStores, 'test': testStores}.get(env, foreignStores)

  def start_requests(self):
    envStores = self.envStores()
    for province, stores in envStores.items():
      for name, url in stores:
        yield scrapy.Request(url, self.parse, meta = {'store': name, 'province': province} )

  def parse(self, response):
    for link in response.css('.mainNav a.invarseColor::attr(href)'):
      if link is not None:
        yield response.follow(link, self.parse_products, meta = response.meta)

  def parse_products(self, response):
    for product_element in response.css('.hProductItems li.span3'):
      product = OeAvisaProduct()

      product['name']     = product_element.css('div.thumbTitle a.invarseColor::text').get().strip()
      product['url']      = response.urljoin(product_element.css('div.thumbTitle a.invarseColor').attrib['href'])
      product['price']    = product_element.css('div.thumbPrice span::text').get().strip()
      product['store']    = response.meta['store']
      product['province'] = response.meta['province']

      # product.rss.title       = product_element.css('div.thumbTitle a.invarseColor::text').get().encode('utf-8').strip()
      # product.rss.link        = response.urljoin(product_element.css('div.thumbTitle a.invarseColor').attrib['href'])
      # product.rss.guid        = response.urljoin(product_element.css('div.thumbTitle a.invarseColor').attrib['href'])
      # product.rss.description = product_element.css('div.thumbTitle a.invarseColor::text').get().encode('utf-8').strip()
      # product.rss.pub_date    = datetime.now()
      # product.rss.enclosure   = {}
      
      yield product