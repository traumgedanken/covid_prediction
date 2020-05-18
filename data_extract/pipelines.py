from data_extract.spiders.worldometer_spider import WorldometerSpider
from storage import get_db_instance


class MongoPipeline:
    db = get_db_instance()

    def process_item(self, item, spider):
        if isinstance(spider, WorldometerSpider):
            collection = self.db.get_collection('countries')
            if collection.count({'name': item['name']}) == 0:
                collection.insert_one(item)

        return item
