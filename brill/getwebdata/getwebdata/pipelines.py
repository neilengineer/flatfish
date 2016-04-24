# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from datetime import datetime
from getwebdata.items import GetwebdataCollinfo
from getwebdata.settings import my_mongo_uri, my_database
#mongodb capped collection
#db.createCollection("log", { capped: true, size: 100000 })
#db.runCommand({"convertToCapped": "mycoll", size: 100000});

class GetwebdataPipeline(object):
    collection_name = 'craig'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=my_mongo_uri,
            mongo_db=my_database
#            mongo_uri=crawler.settings.get('MONGO_URI'),
#            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )
    def open_spider(self, spider):
        if spider.debug != '1':
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        if spider.debug != '1':
            updatetime = GetwebdataCollinfo()
            updatetime['last_update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db[self.collection_name].update(
                                    {'coll_name': self.collection_name},
                                    {
                                        '$set': dict(updatetime)
                                    },
                                    upsert=True,
                                    multi=True,
                                    )
            self.client.close()

    def process_item(self, item, spider):
        if spider.debug != '1':
            self.db[self.collection_name].insert(dict(item))
        return item

