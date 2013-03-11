import flask, unittest, flask_pillow

class TestingBase(object):
    def setUp(self):
        app = self.app = flask.Flask(__name__)
        pillow = flask_pillow.Pillow(app)
        app.debug = True
        @app.route('/test1')
        def test1():
            return flask_pillow.pillow(
                {'who': 'world'}, 'rest', html_source='Hello, {{ rest.who }}')

class TestAccept(TestingBase, unittest.TestCase):
    def test_accept(self):
        with self.app.test_client() as c:
            resp = c.get('/test1', headers=dict(Accept='text/html'))
            self.assertEqual(200, resp.status_code)
            self.assertEqual('Hello, world', resp.data)
        with self.app.test_client() as c:
            resp = c.get('/test1', headers=dict(Accept='text/json'))
            self.assertEqual(200, resp.status_code)
            self.assertEqual('{"who": "world"}', resp.data)

    def test_query(self):
        with self.app.test_client() as c:
            resp = c.get('/test1?content-type=text/html')
            self.assertEqual(200, resp.status_code)
            self.assertEqual('Hello, world', resp.data)
        with self.app.test_client() as c:
            resp = c.get('/test1?content-type=application/json')
            self.assertEqual(200, resp.status_code)
            self.assertEqual('{"who": "world"}', resp.data)

