import tornado.web

import handlers


urls = (
    tornado.web.url(
        r"/(?P<category>movies|music|books|television|games|item\-info)/(?P<item_id>[\w\d-]+)/",
        handlers.ItemInfoHander,
        name='item-info'
    ),
    tornado.web.url(
        r"/update-item-info/(?P<item_id>[\w\d-]+)/",
        handlers.UpdateItemInfoHandler,
        name='update-item-info'
    ),
 )
