from base import tests


class HomepageTest(tests.BasicTest):

    @tests.twilltest
    def test_homepage(self):
        self.tc.go('http://harma.dev:9999/')
        self.tc.find('Welcome')
        self.tc.find('Harma')
