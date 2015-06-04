import tornado.web

import handlers


urls = (
    tornado.web.url(
        r"/admin/items/(?P<category>[\w\d-]+)/delete/(?P<id>[\w\d-]+)/",
        handlers.ItemDeleteHandler,
        name='admin-item-delete'
    ),
    tornado.web.url(
        r"/admin/items/(?P<category>[\w\d-]+)/merge/",
        handlers.ItemsMergeHandler,
        name='admin-items-merge'
    ),
    tornado.web.url(
        r"/admin/items/(?P<category>[\w\d-]+)/",
        handlers.AllItemsHandler,
        name='admin-all-items'
    ),
 )
