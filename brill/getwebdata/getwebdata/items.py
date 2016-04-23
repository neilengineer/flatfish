# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy

class GetwebdataItem(scrapy.Item):
    brand = scrapy.Field()
    entry_title = scrapy.Field()
    year = scrapy.Field()
    car_type = scrapy.Field()
    price = scrapy.Field()
    mileage = scrapy.Field()
    vin = scrapy.Field()
    title_status = scrapy.Field()
    date = scrapy.Field()
    url = scrapy.Field()
    place = scrapy.Field()

class Getwebdata_Time(scrapy.Item):
    last_update_time = scrapy.Field()

