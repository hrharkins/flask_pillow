flask_resitfy
=============

Accept-sensitive translation wrapper for Flask views.

Simple Example
==============

In the app setup:

    from flask_restify import RESTify
    
    RESTify(app)

In the view code:

    from flask_restify import restify

    @app.route('/somewhere')
    def view():
        data = get_model_data()
        return restify(data, html_template='view.html')

Automatic Rendering
===================

The response provided is derived from the following sources:

 1. The content-type query argument
 1. The types available in the accept header, in order of specified priority

The first one available wins and has a restifarian function call upon it.  There are a few of these functions
configured by default, each of which can be disabled if desired by passing *thing*=False to RESTify(app, ...)

 * html -- text/html -- If html_template is provided, it is used in render_template (by file),
    or if html_template_source is provided it is used in render_template_string.
 * json -- application/json, text/json

Custom restifarians
===================

    @RESTify.restifarian('x-application/url-list', src='?')
    def to_url_list(src):
        if isinstance(src, (tuple, list, set)):
            return '\n'.join(src)
        else:
            return RESTify.CONTINUE

