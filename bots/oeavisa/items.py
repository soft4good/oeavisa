# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
# from scrapy_rss import RssedItem

class OeAvisaProduct(Item):
  # define the fields for your item here like:
  # name = scrapy.Field()
  url      = Field(serializer=str)
  name     = Field(serializer=str)
  price    = Field()
  store    = Field(serializer=str)
  province = Field(serializer=str)

# class OeAvisaRssItem(RssedItem):
#   # define the fields for your item here like:
#   # name = scrapy.Field()
#   url      = Field()
#   name     = Field()
#   price    = Field()
#   store    = Field()
#   province = Field()

class OeAvisaStore(Item):
  # define the fields for your item here like:
  # name = scrapy.Field()
  name = Field()
  url  = Field()