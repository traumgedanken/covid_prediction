from scrapy import Spider


class WorldometerSpider(Spider):
    name = 'worldometer'
    start_urls = ['https://www.worldometers.info/coronavirus/']

    def parse(self, response):
        rows = response.xpath('//tr')
        for row in rows:
            country = row.xpath('./td[2]/a[@class="mt_a"]/text()').get()
            population = row.xpath('./td[last()-1]/a/text()').get()
            if country and population:
                yield {
                    'name': country,
                    'population': int(population.replace(',', ''))
                }
