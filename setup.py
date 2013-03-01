"""
Flask-RESTify
-------------

This is the description for that library
"""
from setuptools import setup

setup(
    name='Flask-RESTify',
    version='0.9',
    url='http://example.com/flask-restify/',
    license='BSD',
    author='Rich Harkins',
    author_email='rich.harkins+restify@gmail.com',
    description='Serializes view responses based on the Accept header',
    long_description=__doc__,
    py_modules=['flask_restify'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='tests'
)

