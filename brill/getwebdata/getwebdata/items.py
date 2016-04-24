# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy

#car info struct
#fields with #* are must have
class GetwebdataCar(scrapy.Item):
    brand = scrapy.Field()
    entry_title = scrapy.Field()    #*
    year = scrapy.Field()
    car_type = scrapy.Field()
    price = scrapy.Field()          #*
    mileage = scrapy.Field()        #*
    vin = scrapy.Field()
    title_status = scrapy.Field()
    date = scrapy.Field()
    url = scrapy.Field()            #*
    place = scrapy.Field()

#Per collection generic info
class GetwebdataCollinfo(scrapy.Item):
    coll_name = scrapy.Field()
    last_update_url = scrapy.Field()
    last_update_time = scrapy.Field()

