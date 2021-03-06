flask_pillow
============

Accept-sensitive translation wrapper for Flask views.

Why?
====

Translating an entity to a representation is often boilerplate.  This
module aims to remove that boilerplate by allowing view functions to simply
return a generic entity and letting restify() figure out what sort of
conversion function to call based on the Accept header.

Install
=======

pip install https://github.com/hrharkins/flask_restify/archive/v0.9beta.zip

Simple Example
==============

In the app setup:

    from flask_restify import RESTify
    
    RESTify(app)

In the view code:

    from flask_restify import restify

    @app.route('/somewhere')
    def view():
        data = get_model_data()     # Ideally translated into dictionaries.
        return restify(data, html_template='view.html')

Automatic Rendering
===================

The response provided is derived from the following sources:

 1. The "content-type" query argument in the request URL OR POST data.
 1. The types available in the accept header, in order of specified priority

The first one available that has an associated restifarian function call
upon it.  There are a few of these functions configured by default, each of
which can be disabled if desired by passing *thing*=False to RESTify(app,
...)

 * html -- text/html -- If html_template is provided, it is used in 
    render_template (by file), or if html_soruce is provided it 
    is used in render_template_string.
 * xml -- text/xml -- similar to html, except uses xml_template/xml_source
    instead of the html counterparts.
 * json -- application/json, text/json
 * yaml -- application/yaml, text/yaml -- requries the yaml library.

Custom restifarians
===================

Applications can define their own handler functions by applying the
@RESTify().restifarian decorator:

    REST = RESTify(app)

    @REST.restifarian('x-application/url-list', src='?')
    def to_url_list(src):
        if isinstance(src, (tuple, list, set)):
            return '\n'.join(src)
        else:
            return RESTify.CONTINUE

A few special cases exist.  To accept all keyword arguments, assign '*' to
one of the variables.  To apply a dictionary as keyword arguments, use the
special destination '__kw__'.  To assign the entity to a variable, set '?'
to the variable:

    @REST.restifarian('text/xml', entity='?', 
                      template='xml_template', source='xml_source', __kw__='*')
    def to_xml(_entity, _template=None, _source=None, **_kw):
        if _template:
            return render_template(_template, **_kw)
        elif _source:
            return render_template_string(_source, **_kw)
        else:
            return entity

Naming Note
===========

See http://dictionary.reference.com/browse/pillow, definition 5 as to the
basis for the name.  :)

Apologies to the other developer that had restify first.  I missed it in my
initial scan, so I changed the name accordingly!  Sorry I didn't catch it
up front!  :)


