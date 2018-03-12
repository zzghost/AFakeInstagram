import unittest
from ImitativeInstagram import app

class ImitativeInstagramTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        print "setup test"
    '''
    def setUpClass(cls):
        print "setup class"
    '''
    def tearDown(self):
        print "tear down"
    '''
    def tearDownClass(cls):
        print "tear down class"
    '''

    def register(self, username, password):
        return self.app.post("/reg/", data={"username": username, "password": password}, follow_redirects=True)

    def login(self, username, password):
        return self.app.post("/login/", data={"username": username, "password": password}, follow_redirects=True)

    def logout(self):
        return self.app.get("/logout/")

    def test_reg_logout_login(self):
        assert self.register("hello", "world").status_code == 200
        assert '-hello' in self.app.open("/").data
        self.logout()
        assert '-hello' not in self.app.open("/").data
        self.login("hello", "world")
        assert '-hello' in self.app.open("/").data


    def test1(self):
        print "test1"

    def test2(self):
        print "test2"