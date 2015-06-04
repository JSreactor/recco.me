from base.handlers import BaseHandler


class HomePageHandler(BaseHandler):

    def post(self):
        '''redirects user to website'''

        self.finish('''
            <html><body><script type="text/javascript">window.top.location.href = 'http://recco.me/'</script></body></html>
        ''')

    def get(self):
        '''render homepage'''

        if self.get_current_user():
            self.redirect(self.reverse_url('recommendations', 'movies'))
        else:
            self.jinja_render('website/homepage.html')


class WebsiteAboutHandler(BaseHandler):

    def get(self):

        self.jinja_render('website/about.html')


class HowItWorksHandler(BaseHandler):

    def get(self):

        self.jinja_render('website/how-it-works.html')


class WebsitePrivacyPolicyHandler(BaseHandler):

    def get(self):
        '''render blog page'''

        self.jinja_render('website/privacy_policy.html')


class WebsiteTermsOfServiceHandler(BaseHandler):

    def get(self):
        '''render blog page'''

        self.jinja_render('website/terms_of_service.html')


class WebsiteBlog(BaseHandler):

    def get(self):
        '''render blog page'''

        self.jinja_render('website/blog.html')
