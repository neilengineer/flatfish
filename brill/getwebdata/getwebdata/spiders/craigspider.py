import scrapy
from scrapy.spider import BaseSpider
from getwebdata.items import GetwebdataItem
import re
from datetime import datetime

TOP_SELLING_BRANDS = ["ford","chevrolet","chevy","ram","toyota","honda","nissan","hyundai","jeep","gmc", \
    "subaru","kia","bmw","lexus","infiniti","volkswagen","dodge","chrysler","audi","mazda","mini"]
DATE=''
PRICE_MIN = 2000
PRICE_MAX = 20000
YEAR_MIN = '1970'
MILEAGE_MIN = 5000

#NOTE:
#only supports SF bay area
#only supports craigslist
#date: today and yesterday
#price range 2000-20000
#year is from 1970
#entries without mileage or without price will be skipped
#TODO:
#filter out spam info : if no year number in title skip
#log all ops on the site: num of clicks, brand, type, price etc.

class craigspider(BaseSpider):
    name = "craig"
    allowed_domains = ["craigslist.org"]
    start_urls = [
	"https://sfbay.craigslist.org/search/cta?max_price=20000&min_price=3000&postedToday=1",
    ]
    date_today = datetime.today().date()

    def parse(self, response):
        links = response.xpath("//p[@class='row']/span[@class='txt']/span[@class='pl']/a/@href").extract()
        for href in links:
            url = response.urljoin(href)
            print "----Processing URL = %s"%url
            yield scrapy.Request(url, callback=self.parse_link_detail)

    def parse_link_detail(self, response):
        items = []
        entries = response.xpath("//section[@class='body']")
        for a_entry in entries:
            item = GetwebdataItem()

            tmp_title = a_entry.xpath("h2[@class='postingtitle']/span[@class='postingtitletext']")
            #price
            price = tmp_title.xpath("span[@class='price']/text()").extract()[0].replace("$","")
            if int(price) < PRICE_MIN or int(price) > PRICE_MAX:
                print "----Price %s is not within valid range, skip... "%price
                continue

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
            for b in TOP_SELLING_BRANDS:
                if b in brand_str:
                    brand = b
                    break
            if brand == '':
                print "----Brand not found in %s"%brand_str
                continue
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
            if mileage == '' or int(mileage) < MILEAGE_MIN:
                print "----Mileage %s not within range"%mileage
                continue

            #date
            tmp_date = a_entry.xpath("section[@class='userbody']/div[@class='postinginfos']/p[@class='postinginfo reveal']/time/@datetime").extract()[0]
            tmp_date = tmp_date.replace("T"," ")
            #ignore timezone str for now
            tmp_date = re.sub("-\d{4}","",tmp_date)
            date_obj = datetime.strptime(tmp_date, '%Y-%m-%d %H:%M:%S')
            if date_obj.date() == date_today:
                date = tmp_date
            else:
                print "----Date %s not within range"%tmp_date
                continue

            item['price'] = price
            item['entry_title'] = entry_title
            item['year'] = year
            item['brand'] = brand
            item['mileage'] = mileage
            item['vin'] = vin
            item['title_status'] = title_status
            item['car_type'] = car_type
            item['date'] = date
            item['url'] = response.url
            items.append(item)
        return items

