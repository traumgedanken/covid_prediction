BOT_NAME = 'data_extract'

SPIDER_MODULES = ['data_extract.spiders']
NEWSPIDER_MODULE = 'data_extract.spiders'

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
   'data_extract.pipelines.MongoPipeline': 300,
}
