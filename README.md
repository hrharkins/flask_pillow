flask_resitfy
=============

Accept-sensitive translation wrapper for Flask views.

Simple Example
==============

    from flask_resitfy import restify

    @app.route('/somewhere')
    def view():
        data = get_model_data()
        return restify(data, html_template='view.html')

Automatic Rendering
===================

The response provided is derived from the following sources:

 1. The content-type query argument
 1. The types available in the accept header


