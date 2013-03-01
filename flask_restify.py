import flask, json

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

class RESTify(object):
    def __init__(self, app=None, _base=None, **_kw):
        self.app = app
        self.handlers = {}
        self.auto_setup = _kw
        if app is not None:
            self.init_app(self.app)

    def init_app(self, app):
        self.setup(app)
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def setup(self, app):
        config = app.config.setdefault('RESTIFIERS', {})
        config.update(self.handlers)
        default_setup = not bool(self.auto_setup)
        if self.auto_setup.get('html', default_setup):
            @self.restifarian('text/html', '.html',
                              template='html_template',
                              __default_template=None,
                              template_source='html_template_source',
                              __default_template_source=None,
                              __all__=True)
            def to_html(template=None, template_source=None, **_kw):
                if template is not None:
                    return flask.render_template(template, **_kw)
                else:
                    return flask.render_template_string(template_source, **_kw)
        if self.auto_setup.get('json', default_setup):
            @self.restifarian('text/json', 'application/json', '.json', obj='?')
            def to_json(obj):
                return json.dumps(obj)

    def teardown(self, exception):
        ctx = stack.top

    def restifarian(_self, _fn=None, *_mimetypes, **_translate):
        '''Define a rendering handler for mimetypes.
        '''
        if _fn is None:
            return lambda fn: \
                _self.restifarian(fn, *_mimetypes, **_translate)
        elif isinstance(_fn, str):
            return lambda fn: \
                _self.restifarian(fn, _fn, *_mimetypes, **_translate)
        else:
            def handler(_entity, _name=None, **_kw):
                translated = {}
                found = set()
                found_entity = False
                for dest in _translate:
                    if dest[:2] == '__':
                        pass
                    else:
                        found.add(dest)
                        src = _translate[dest]
                        if src == '?':
                            found_entity = True
                            translated[dest] = _entity
                        else:
                            default = \
                                _translate.get('__default_' + dest, KeyError)
                            if default is KeyError:
                                translated[dest] = _kw[src]
                            else:
                                translated[dest] = _kw.get(src, default)
                if _kw.get('__all__', False):
                    for name in _kw:
                        if name not in found:
                            translated[name] = _kw[name]
                if not found_entity and _name is not None:
                    translated[_name] = _entity
                return _fn(**translated)
            for mimetype in _mimetypes:
                _self.handlers[mimetype] = handler
                if _self.app is not None:
                    config = _self.app.config.get('RESTIFIERS')
                    if config is not None:
                        config.update(_self.handlers)
            return _fn

    @classmethod
    def restify(_cls, _entity, _name='rest', _default=None, **_kw):
        '''Serialize the returned object based on Accept header.
        '''

        app = flask.current_app
        override = flask.request.values.get('content-type')
        if override is not None:
            mimetypes = [override]
        else:
            mimetypes = [mimetype for mimetype, priority
                         in flask.request.accept_mimetypes]
        restifiers = app.config.get('RESTIFIERS')
        if restifiers:
            for mimetype in mimetypes:
                handler = restifiers.get(mimetype)
                if handler is not None:
                    return handler(_entity, _name, **_kw)
        else:
            return _entity if _default is None else _default

restify = RESTify.restify

