import flask, json, sys

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

class Pillow(object):
    factories = {}

    def __init__(self, app=None, *factories, **_kw):
        self.factory_filter = _kw.pop('factories', None)
        self.app = app
        self.cases = {}
        self.factories = dict(self.factories)
        self.auto_setup = _kw
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.setup(app)
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def setup(self, app):
        factories = app.config.setdefault('PILLOW_FACTORIES', {})
        factory_filter = self.factory_filter
        for factory in self.factories:
            if not factory_filter or factory in factory_filter:
                if not factories.get(factory):
                    factories[factory] = True
                    self.factories[factory](self, app)
        configured = app.config.setdefault('PILLOW_CASES', {})
        for pattern in self.cases:
            case = self.cases[pattern]
            if not configured.get(pattern):
                configured[pattern] = case
        return

    def teardown(self, exception):
        ctx = stack.top

    def factory(_self, _fn=None, *_default_mimetypes, **_kw):
        if _fn is None:
            return lambda f: _self.factory(f, **_kw)
        elif isinstance(_fn, basestring):
            return lambda f: _self.factory(f, _fn, *_default_mimetypes, **_kw)
        else:
            if not _default_mimetypes:
                raise TypeError('Must specify the mimetypes factory handles')
            _self.factories[_fn.__name__] = \
                lambda self, app: _fn(self, app, _default_mimetypes, **_kw)

    @classmethod
    def default_factory(_cls, _fn=None, *_default_mimetypes, **_kw):
        if _fn is None:
            return lambda f: _cls.default_factory(f, **_kw)
        elif isinstance(_fn, basestring):
            return lambda f: _cls.default_factory \
                (f, _fn, *_default_mimetypes, **_kw)
        else:
            if not _default_mimetypes:
                raise TypeError('Must specify the mimetypes factory handles')
            _cls.factories[_fn.__name__] = \
                lambda self, app: _fn(self, app, _default_mimetypes, **_kw)

    def case(_self, _fn=None, *_mimetypes, **_kw):
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
                _self.restifarian(fn, *_mimetypes, **_kw)
        elif isinstance(_fn, str):
            return lambda fn: \
                _self.restifarian(fn, _fn, *_mimetypes, **_kw)
        else:
            _self.make_case(_fn, _mimetypes, **_kw)
            if _self.app is not None:
                _self.setup(_self.app)

    def make_case(self, fn, mimetypes, cls=object, **_kw):
        handler = make_translator(fn, '_entity', **_kw)
        for mimetype in mimetypes:
            for base in cls.__mro__:
                pattern = (mimetype, base.__name__)
                self.cases[pattern] = handler
        return fn

    @classmethod
    def pillow(_cls, entity, _name='rest', default=None, request=None, **_kw):
        '''Serialize the returned object based on Accept header.

        This method will use the config from the current_app to determine
        what to do.  It uses the RESTIFARIAN config element and tries to
        find keys matching the following (in order):

        1. The "content-type" GET or POST string.
        1. The mimetypes in the "Accept" header, in order.

        The first mimetype with a handler wins.
        '''

        app = flask.current_app
        if request is None:
            request = flask.request
        override = flask.request.values.get('content-type')
        override = override or flask.request.values.get('content_type')
        config = app.config.get('PILLOW_CASES')
        errors = {}
        if config is not None:
            if _name is not None:
                _kw[_name] = entity
            for pattern in _cls.permute(request, type(entity), override):
                handler = config.get(pattern)
                if handler is not None:
                    try:
                        result = handler(entity, **_kw)
                        if result is not _cls.CONTINUE:
                            return result
                    except Exception, e:
                        errors[pattern] = sys.exc_info()
            else:
                if default is not None:
                    return default(entity, **_kw)
        if errors:
            for pattern, exc_info in errors.iteritems():
                raise exc_info[1], None, exc_info[2]
        if override is None:
            mimetypes = [mimetype[0]
                         for mimetype in request.accept_mimetypes]
        else:
            mimetypes = [override]
        raise TypeError('Could not render %r into %s'
                        % (type(entity).__name__,
                           ', '.join(repr(t) for t in mimetypes)))

    CONTINUE = 'CONTINUE'

    @classmethod
    def permute(cls, request, entity_cls, override=None):
        if override is None:
            mimetypes = [mimetype[0] for mimetype in request.accept_mimetypes]
        elif isinstance(override, (list, tuple, set)):
            mimetypes = override
        else:
            mimetypes = [override]
        for mimetype in mimetypes:
            for base in entity_cls.__mro__:
                yield mimetype, base.__name__

pillow = Pillow.pillow

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

def templatize(_entity, _template=None, _source=None, **_kw):
    if _template is not None:
        return flask.render_template(_template, **_kw)
    elif _source is not None:
        return flask.render_template_string(_source, **_kw)
    else:
        raise ValueError('Either *_template or *_source must be set')

@Pillow.default_factory('json', 'text/json', 'application/json')
def to_json(pillow, app, mimetypes, mimetype_override=None,
                    serialize_objects=None, **_kw):
    mimetypes = mimetype_override or app.config.get('json-types', mimetypes)
    serialize_objects = (
        app.config.get('json-serialize-objects', True)
        if serialize_objects is None else serialize_objects)
    if serialize_objects:
        def json_dumps(*_args, **_kw):
            return json.dumps(*_args, default=lambda o: o.to_json(), **_kw)
    else:
        json_dumps = json.dumps
    pillow.case(json_dumps, *mimetypes, obj='?')

@Pillow.default_factory('yaml', 'text/yaml', 'application/yaml')
def to_yaml(pillow, app, mimetypes, mimetype_override=None, **_kw):
    mimetypes = mimetype_override or app.config.get('yaml-types', mimetypes)
    try:
        import yaml
        pillow.case(yaml.dump, *mimetypes, data='?')
    except ImportError:
        def fail(*_args, **_kw):
            raise ImportError('yaml was not available')
        pillow.case(fail)

@Pillow.default_factory('html', 'text/html')
def to_html(pillow, app, mimetypes, mimetype_override=None, **_kw):
    mimetypes = mimetype_override or app.config.get('html-types', mimetypes)
    pillow.case(templatize, *mimetypes,
                _template='html_template',
                _source='html_source',
                _entity='?',
                __kw__='*')

@Pillow.default_factory('xml', 'text/xml')
def to_xml(pillow, app, mimetypes, mimetype_override=None, **_kw):
    mimetypes = mimetype_override or app.config.get('xml-types', mimetypes)
    pillow.case(templatize, *mimetypes,
                _template='xml_template',
                _source='xml_source',
                _entity='?',
                __kw__='*')

