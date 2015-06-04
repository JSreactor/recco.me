import tornado.web

import handlers


urls = (
    tornado.web.url(r"/", handlers.HomePageHandler, name='homepage'),
    tornado.web.url(r"/blog/", handlers.WebsiteBlog, name='website-blog'),
    tornado.web.url(
        r"/about/", handlers.WebsiteAboutHandler,
        name='website-about'
    ),
    tornado.web.url(
        r"/how-it-works/", handlers.HowItWorksHandler,
        name='website-how-it-works'
    ),
    tornado.web.url(
        r"/privacy-policy/", handlers.WebsitePrivacyPolicyHandler,
        name='website-privacy-policy'
    ),
    tornado.web.url(
        r"/terms-of-service/", handlers.WebsiteTermsOfServiceHandler,
        name='website-terms-of-service'
    ),
)
