import scrapy
import pymongo
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from getwebdata.items import GetwebdataCar, GetwebdataCollinfo
from getwebdata.settings import my_mongo_uri, my_database
from datetime import datetime
import re

CAR_BRANDS = ["ford","chevrolet","chevy","ram","toyota","honda","nissan","hyundai","jeep","gmc", \
 "subaru","kia","bmw","lexus","infiniti","volkswagen","vw","dodge","chrysler","audi","mercedes-benz","benz",\
"mazda","mini","buick","fiat","cadillac","jaguar","acura","volvo","scion","mercedes","mb"]
PRICE_MIN = 2000
PRICE_MAX = 15000
YEAR_MIN = '2000'
MILEAGE_MIN = 5000
MILEAGE_MAX = 150000

#NOTE:
#only supports craigslist
#only supports SF bay area
#date: show today's result only
#price range 2000-15000
#mileage range 5000-150000
#year is from 2000
#both dealer and owner
#entries without mileage or without price will be skipped
#TODO:
#log all ops on the site: num of clicks, brand, type, price etc.
#"https://sfbay.craigslist.org/search/cta?max_price=15000&min_price=2000&postedToday=1",

class craigspider(CrawlSpider):
    name = "craig"
    allowed_domains = ["craigslist.org"]
    start_urls = [
    "https://sfbay.craigslist.org/search/cta?postedToday=1&min_price=2000&max_price=15000&min_auto_year=2000&min_auto_miles=5000&max_auto_miles=150000",
    ]
    collection_name = 'craig'
    last_update_url = ''
    page_num = 0
    total_page_num = 0
    total_processed_link_num = 0
    valid_link_num = 0

    rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="button next"]',)), callback="parse_page", follow=True),)

    def __init__(self, debug='', *args, **kwargs):
        self.debug = debug
        super(craigspider, self).__init__(*args, **kwargs)
        if self.debug != '1':
            self.client = pymongo.MongoClient(my_mongo_uri)
            self.db = self.client[my_database]
            cursor = self.db[self.collection_name].find({'coll_name':self.collection_name})
            if cursor != None:
                for document in cursor:
                    self.last_update_url = document['last_update_url']
                    print "----Got last update url = %s"%self.last_update_url
        else:
            print "----Dry run for debugging"

    def closed(self, reason):
        cursor = self.db[self.collection_name].find({'coll_name':self.collection_name})
        if cursor != None:
            for document in cursor:
                last_total_processed_link_num = document['total_processed_link_num']
        stats_cnt = GetwebdataCollinfo()
        stats_cnt['total_processed_link_num'] = self.total_processed_link_num + last_total_processed_link_num
        self.db[self.collection_name].update(
                                {'coll_name': self.collection_name},
                                {'$set': dict(stats_cnt) },upsert=True,multi=True )
        print "--Spider closing, total_processed_link_num=%d, valid_link_num=%d this run"%(self.total_processed_link_num,self.valid_link_num)

    def parse_start_url(self, response):
        return self.parse_page(response)

    def parse_page(self, response):
        self.page_num = self.page_num + 1
        if self.page_num == 1:
            self.total_page_num = 1 + int(response.xpath("//span[@class='totalcount']/text()").extract()[0])/100
        if self.page_num == self.total_page_num:
            print "----This is the last page, stop following"
            self._follow_links = False
        print "--Opening page%d URL = %s"%(self.page_num, response.url)

        links = response.xpath("//p[@class='row']/span[@class='txt']/span[@class='pl']/a/@href").extract()
#        print "----Total number of URLs = %d on this page"%len(links)
        if self.debug != '1':
            if self.last_update_url == '':
                self.last_update_url = links[0]
                print "----Set the first threshold url %s"%self.last_update_url
        for i,href in enumerate(links):
            if self.debug != '1':
                if href == self.last_update_url:
                    print "----Last update URL found on this page at link%d, stop following next pages"%i
                    self._follow_links = False
                    break
                #Always save the newest link on the 1st page once
                if self.page_num == 1 and i == 0:
                    updateurl = GetwebdataCollinfo()
                    updateurl['coll_name'] = self.collection_name
                    updateurl['last_update_url'] = links[0]
                    self.db[self.collection_name].update(
                                            {'coll_name': self.collection_name},
                                            {'$set': dict(updateurl) },upsert=True,multi=True )
                    print "----Saving last_update_url to new URL %s"%(updateurl['last_update_url'])
            url = response.urljoin(href)
            yield scrapy.Request(url, callback=self.parse_link_detail)

    def parse_link_detail(self, response):
        self.total_processed_link_num = self.total_processed_link_num + 1
        items = []
        entries = response.xpath("//section[@class='body']")
        for a_entry in entries:
            item = GetwebdataCar()

            tmp_title = a_entry.xpath("h2[@class='postingtitle']/span[@class='postingtitletext']")
            #price
            price = tmp_title.xpath("span[@class='price']/text()").extract()[0].replace("$","")
            if int(price) < PRICE_MIN or int(price) > PRICE_MAX:
                print "----Price %s is not within valid range, skip... "%price
                continue
            #place
            place = tmp_title.xpath("small/text()").extract()[0].strip().replace("(","").replace(")","")

            tmp_attrs = a_entry.xpath("section[@class='userbody']/div[@class='mapAndAttrs']/p[@class='attrgroup']/span")
            #entry title string
            entry_title = tmp_attrs.xpath("b/text()").extract()[0]
            #year from 1970
            year = re.findall(r"\d{4}",entry_title)[0]
            if year == '' or year < YEAR_MIN:
                print "----Year not found or too old in %s, skip..."%entry_title
                continue
            #brand
            brand = ''
            brand_str = entry_title.lower().split()
            for b in CAR_BRANDS:
                if b in brand_str:
                    brand = b
                    break
            if brand == '':
                print "----Brand not found in %s, skip brand"%brand_str

            #mileage, vin, title_status, car_type
            mileage = ''
            vin = ''
            title_status = ''
            car_type = ''
            for i in tmp_attrs.extract():
                tmp_value = re.findall(r"<b>(.*?)</b>",i)
                if 'odometer: ' in i:
                    #mileage
                    mileage = tmp_value[0]
                elif 'VIN: ' in i:
                    vin = tmp_value[0]
                elif 'title status: ' in i:
                    title_status = tmp_value[0]
                elif 'type: ' in i:
                    car_type = tmp_value[0]
            if mileage == '' or int(mileage) < MILEAGE_MIN or int(mileage) > MILEAGE_MAX:
                print "----Mileage %s not within range"%mileage
                continue

            #date
            tmp_date = a_entry.xpath("section[@class='userbody']/div[@class='postinginfos']/p[@class='postinginfo reveal']/time/@datetime").extract()[0]
            tmp_date = tmp_date.replace("T"," ")
            #ignore timezone str for now
            date = re.sub("-\d{4}","",tmp_date)

            item['price'] = price
            item['entry_title'] = entry_title
            item['year'] = year
            item['brand'] = brand
            item['mileage'] = mileage
            item['vin'] = vin
            item['title_status'] = title_status
            item['car_type'] = car_type
            item['date'] = date
            item['url'] = place
            item['url'] = response.url
            items.append(item)
            self.valid_link_num = self.valid_link_num + 1
            print "----Found valid entry at link %s"%item['url']
        return items

