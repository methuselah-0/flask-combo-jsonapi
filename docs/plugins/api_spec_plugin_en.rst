ApiSpecPlugin
-------------

The plugin **ApiSpecPlugin** adds the following:

1. Automatically generated JSONAPI docs for **ResourceList** and **ResourceDetail** resource managers.
2. Auto specification support for RPC API created with the help of `EventPlugin <docs/plugins/event_plugin.rst>`_
3. Tags based grouping for created APIs (in **swagger**).

The plugin is built on top of **apispec** with the usage of `RestfulPlugin <docs/plugins/restful_plugin.rst>`_.

Simplified work algorithm: **apispec** -> **swagger**

Working with the plugin
~~~~~~~~~~~~~~~~~~~~~~~
To start working with the plugin, it is necessary to:

1. Add the plugin's instance upon the application initialization.
2. When initializing, the plugin supports the following parameters:

    * :code:`app: Flask` - an instance of the application
    * :code:`decorators: Tuple = None` - a tuple with decorators which are to be applied to the **swagger** router
    * :code:`tags: Dict[str, str] = None` - a list of tags with their description, they are used for grouping

3. When updating routers, a :code:`tag: str` parameter is used. If a tag that hadn't been described during the app initializatiion, an error will occur.
4. When creating RPC API using the `EventPlugin <docs/plugins/event_plugin.rst>`_ plugin, describe
   the API using yaml `YAML API description structure <https://swagger.io/docs/specification/data-models/>`_.

An example can be found in EventPlugin `here <docs/plugins/event_plugin.rst>`_.
