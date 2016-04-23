#!/usr/bin/env python
from pymongo import MongoClient

SERVER_URL = 'localhost'
SERVER_PORT = 27017
database = 'whichv'
collection = 'whichvcar'

if __name__ == '__main__':
    client = MongoClient(SERVER_URL, SERVER_PORT)
    coll = client[database][collection]

    print new_car_info
    coll.update(
                {"brand":brand, "name":name, "year":year, "price_date":date},
                {
                    '$set': new_car_info
                },
                upsert=True,
                multi=True,
               )

