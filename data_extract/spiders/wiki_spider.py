import datetime

from scrapy import Spider, Request

from storage import get_db_instance


class WikiSpider(Spider):
    name = 'wiki'
    countries = get_db_instance().get_collection('countries')

    def start_requests(self):
        for country in self.countries.find():
            yield Request(f'https://en.wikipedia.org/wiki/COVID-19_pandemic_in_{country["name"]}?id={country["_id"]}',
                          callback=self.parse)

    def parse(self, response):
        country = parse_country(response.xpath('//h1/text()').get())
        country_id = response.url.split('id=')[-1]
        rows = response.xpath('//b[text()="# of cases"]/../../../following-sibling::tr')
        cases = []
        for row in rows:
            date_ = row.xpath('./td[1]/text()').get()
            deaths = row.xpath('.//div[contains(@style, "#A50026")]/@title').get()
            recoveries = row.xpath('.//div[contains(@style, "SkyBlue")]/@title').get()
            active_cases = row.xpath('.//div[contains(@style, "Tomato")]/@title').get()
            if date_ and date_.count('-') == 2:
                cases.append({
                    'country': country,
                    'date': datetime.datetime.strptime(date_, "%Y-%m-%d"),
                    'deaths': parse_number(deaths),
                    'recoveries': parse_number(recoveries),
                    'active': parse_number(active_cases),
                    'country_id': country_id
                })
        if cases:
            yield {'cases': cases}


def parse_number(number):
    if not number:
        return 0
    return int(number)


def parse_country(country):
    return country.replace('COVID-19 pandemic in', '').replace('the', '').strip()
