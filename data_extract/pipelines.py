from data_extract.spiders.wiki_spider import WikiSpider
from data_extract.spiders.worldometer_spider import WorldometerSpider
from storage import get_db_instance


class MongoPipeline:
    db = get_db_instance()

    def process_item(self, item, spider):
        if isinstance(spider, WorldometerSpider):
            collection = self.db.get_collection('countries')
            if collection.count({'name': item['name']}) == 0:
                collection.insert_one(item)

        elif isinstance(spider, WikiSpider):
            collection = self.db.find('cases')
            collection.insert_many(item['cases'])

        return item
