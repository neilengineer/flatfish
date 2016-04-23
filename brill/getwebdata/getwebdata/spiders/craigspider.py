import scrapy
import re
from scrapy.spider import BaseSpider
from getwebdata.items import GetwebdataItem
TOP_SELLING_BRANDS = ["ford","chevrolet","chevy","ram","toyota","honda","nissan","hyundai","jeep","gmc", \
    "subaru","kia","bmw","lexus","infiniti","volkswagen","dodge","chrysler","audi"]

#NOTE:
#only supports SF bay area
#only supports craigslist
#date: today and yesterday
#price range 3000-20000
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

    def parse(self, response):
        links = response.xpath("//p[@class='row']/span[@class='txt']/span[@class='pl']/a/@href").extract()
        for href in links:
            url = response.urljoin(href)
            print "Processing URL = %s"%url
            yield scrapy.Request(url, callback=self.parse_link_detail)

    def parse_link_detail(self, response):
        items = []
        entries = response.xpath("//section[@class='body']")
        for a_entry in entries:
            item = GetwebdataItem()

            tmp_title = a_entry.xpath("h2[@class='postingtitle']/span[@class='postingtitletext']")
            #price
            price = tmp_title.xpath("span[@class='price']/text()").extract()[0].replace("$","")
            if int(price) < 3000 or int(price) > 20000:
                print "Price %s is not valid, skip... "%price
                continue

            tmp_attrs = a_entry.xpath("section[@class='userbody']/div[@class='mapAndAttrs']/p[@class='attrgroup']/span")
            #entry title string
            entry_title = tmp_attrs.xpath("b/text()").extract()[0]
            #year 1970-2100
            year = re.findall(r"\d{4}",entry_title)[0]
            if year == '' or year < '1970':
                print "Year not found in %s"%entry_title
                continue
            #brand
            brand = ''
            brand_str = entry_title.lower().split()
            for b in TOP_SELLING_BRANDS:
                if b in brand_str:
                    brand = b
                    break
            if brand == '':
                print "Brand not found in %s"%brand_str
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
            if mileage == '':
                continue

            date = a_entry.xpath("section[@class='userbody']/div[@class='postinginfos']/p[@class='postinginfo reveal']/time/@datetime").extract()[0]

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

