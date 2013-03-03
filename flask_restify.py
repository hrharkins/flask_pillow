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
                              _template='html_template',
                              _source='html_source',
                              _entity='?',
                              __kw__='*')
            def to_html(_entity, _template=None, _source=None, **_kw):
                if _template is not None:
                    return flask.render_template(_template, **_kw)
                elif _source is not None:
                    return flask.render_template_string(_source, **_kw)
                else:
                    return _entity
        if self.auto_setup.get('json', default_setup):
            @self.restifarian('text/json', 'application/json', '.json', obj='?')
            def to_json(obj):
                return json.dumps(obj)

    def teardown(self, exception):
        ctx = stack.top

    def restifarian(_self, _fn=None, *_mimetypes, **_translate):
        '''Define a rendering handler for mimetypes.

        This wraps up the handler fn using the keyword arguments for
        translation of the general restify() call to the specific
        handler.  Each name in the kwargs represents a destination name
        that handler accepts and the associated vaule names something the
        keyword arguments to restify that the value is mapped from.  The
        special value '?' denotes the "entity" positional argument provided
        to restify().

        For example:

        REST = RESTify(app)
        REST.restifarian(json.dumps, 'application/json',
                            'text/json', obj='?')

        Maps the entity object to the obj (first) argument of json.dumps.
        If restify is called thusly:

        @app.route(...)
        def handler():
            return restify({'who': 'world'})

        The result would be the JSON representation if that is the
        best acceptable type from the Accept header or content-type in the
        GET/POST values.

        The special destination '__kw__' determines what's provided as
        generic keyword arguments rather than a specific value.  Any source
        name can also be '*', which refers to the non-translated keyword
        arguments of the restify call:

        @REST.restifarian(__template='html_template',
                          __source='html_source',
                          __kw__='*'):
        def html_serialize(__template=None, __source=None, **_kw):
            if __template is not None:
                if __source is not None:
                    raise ValueError('Cannot have both __source and __template')
                else:
                    return render_template(__template, **_kw)
            elif __source is not None:
                return render_template_string(__source, **_kw)
            else:
                raise ValueError('Must specify either __source or __template')
        '''
        if _fn is None:
            return lambda fn: \
                _self.restifarian(fn, *_mimetypes, **_translate)
        elif isinstance(_fn, str):
            return lambda fn: \
                _self.restifarian(fn, _fn, *_mimetypes, **_translate)
        else:
            handler = make_translator(_fn, '_entity', **_translate)
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

        This method will use the config from the current_app to determine
        what to do.  It uses the RESTIFARIAN config element and tries to
        find keys matching the following (in order):

        1. The "content-type" GET or POST string.
        1. The mimetypes in the "Accept" header, in order.

        The first mimetype with a handler wins.
        '''

        app = flask.current_app
        override = flask.request.values.get('content-type')
        if override is not None:
            mimetypes = [override]
        else:
            mimetypes = [mimetype for mimetype, priority
                         in flask.request.accept_mimetypes]
        restifiers = app.config.get('RESTIFIERS')
        if _name is not None:
            _kw[_name] = _entity
        if restifiers:
            for mimetype in mimetypes:
                handler = restifiers.get(mimetype)
                if handler is not None:
                    result = handler(_entity, **_kw)
                    if result is not _cls.CONTINUE:
                        return result
        return _entity if _default is None else _default

    CONTINUE = 'CONTINUE'

restify = RESTify.restify

def make_translator(_fn, *_args, **_xlate):
    '''Creates a wrapper function on-the-fly to translate arguments.
    '''
    fn_args = list(_args)
    call_assign = []
    call_kwarg = None
    for dest in _xlate:
        src = _xlate[dest]
        if dest == '__kw__':
            if src == '*':
                call_kwarg = '**__kw__'
            else:
                call_kwarg = '**' + src
        else:
            if src is True:
                src = dest
            elif src is False:
                continue
            if src.endswith('?'):
                arg = int(src[:-1] or '0')
                call_assign.append('translated[%r] = %s'
                                   % (dest, _args[arg]))
            elif src == '*':
                call_assign.append('translated[%r] = __kw__' % dest)
            else:
                fn_args.append(src + '=type(None)')
                call_assign.append('if %s is not type(None): '
                                    'translated[%r] = %s'
                                   % (src, dest, src))
    fn_args.append('**__kw__')
    fn_src = ['def %s(%s):' % (_fn.__name__, ', '.join(fn_args))]
    if _fn.__doc__:
        fn_src.append('    %r' % _fn.__doc__)
    fn_src.append('    translated = {}')
    for assign in call_assign:
        fn_src.append('    ' + assign)
    if call_kwarg:
        fn_src.append('    translated.update(%s)' % call_kwarg)
    fn_src.append('    return _fn(**translated)')
    l = dict(_fn=_fn)
    exec '\n'.join(fn_src) in l
    return l[_fn.__name__]

