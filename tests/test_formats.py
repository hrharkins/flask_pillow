import flask, unittest, flask_pillow

class HelloWorld(object):
    def to_json(self):
        return 'Hello world'

class TestJSON(unittest.TestCase):
    def test_object_dumps(self):
        app = self.app = flask.Flask(__name__)
        pillow = flask_pillow.Pillow(app)
        app.debug = True
        @app.route('/test1')
        def test1():
            return flask_pillow.pillow(HelloWorld())

        with self.app.test_client() as c:
            resp = c.get('/test1', headers=dict(Accept='json'))
            self.assertEqual(200, resp.status_code)
            self.assertEqual('"Hello world"', resp.data)

