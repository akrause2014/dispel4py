Dispel4Py
=========

Dispel4Py is a Python library used to describe abstract workflows for distributed data-intensive applications. These workflows are compositions of processing elements representing knowledge discovery activities (such as batch database querying, noise filtering and data aggregation) through which significant volumes of data can be streamed in order to manufacture a useful knowledge artefact. Such processing elements may themselves be defined by compositions of other, more fundamental computational elements, in essence having their own internal workflows. Users can construct workflows importing existing processing elements from a registry, or can define their own, recording them in a registry for later use by themselves or others.

Abstract dataflows described in Dispel4Py can be executed in numerous environments, for example using a Storm cluster or as an MPI job. Thus Dispel4Py allows to construct workflows without particular knowledge of the specific context in which they are to be executed, granting them greater generic applicability.

Dependencies 
------------

Dispel4Py has been tested with Python versions *2.7.2* and *2.6.6*.

- networkx

If using the registry:

- requests

If using Storm as execution engine:

- Python Storm thrift generated code, available here: https://github.com/krux/python-storm

Installation
------------

The easiest way to install dispel4py is via pip (https://pypi.python.org/pypi/pip):

`sudo pip install git+git://github.com/akrause2014/dispel4py.git#egg=dispel4py`

Documentation
-------------

The wiki documentation explains how to install and test Dispel4Py: https://github.com/akrause2014/dispel4py/wiki 



![Logo](http://www2.epcc.ed.ac.uk/~amrey/VERCE/Dispel4Py/_images/DISPEL4PY_web.jpg)

