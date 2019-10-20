.. image:: https://badge.fury.io/py/Flask-REST-JSONAPI.svg
    :target: https://badge.fury.io/py/Flask-REST-JSONAPI
.. image:: https://travis-ci.org/miLibris/flask-rest-jsonapi.svg
    :target: https://travis-ci.org/miLibris/flask-rest-jsonapi
.. image:: https://coveralls.io/repos/github/miLibris/flask-rest-jsonapi/badge.svg
    :target: https://coveralls.io/github/miLibris/flask-rest-jsonapi
.. image:: https://readthedocs.org/projects/flask-rest-jsonapi/badge/?version=latest
    :target: http://flask-rest-jsonapi.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


ComboJSONAPI is an advanced fork of the `Flask-REST-JSONAPI <https://flask-rest-jsonapi.readthedocs.io/en/latest/quickstart.html>`_ library
===========================================================================================================================================
The fork adds/improves upon the following:

1.  Added support for :code:`marshmallow=3.0.0`.
2.  Filters have been improved. Now deep-filtering is available. It allows for looking up objects like in the example below:

    .. code:: python

        filter=[{"name": "manager_id__group_id__name", "op": "ilike", "val": "Test%"}]

    - There's a table  :code:`User` with fields:

        - :code:`manager_id`,  a foreign key to the table :code:`User`
        - :code:`group_id`,  a foreign key to the table :code:`Group`

    - There's a table :code:`Group` with a field:

        - :code:`name` - the name of a group

3. Sorting has been improved. Now a 'deep' sort is available which follows the same principle as the 'deep' filters.
4. Added validation and deserialization for values that can be used as filters.
5. Custom fields can now have custom methods for filtering and sorting. More on that below.
6. Added support for plugins (`More on that here <docs/plugins/create_plugins.rst>`_).
7. Added **Permission** plugin which allows to create various access systems for CRUD operations with models and their fields (`Permission docs <docs/plugins/permission_plugin.rst>`_)
8. Added **ApiSpecPlugin** plugin which allows to generate simplified auto specification for JSONAPI (`ApiSpecPlugin docs <docs/plugins/api_spec_plugin.rst>`_)
9. Added **RestfulPlugin** plugin for the apispec library which is a dependency of the **ApiSpecPlugin** which allows to decsribe GET parameters with the help of marshmallow schemes (`RestfulPlugin docs <docs/plugins/restful_plugin.rst>`_)
10. Added **EventPlugin** plugin for creating RPC for cases when JSON:API isn't enough (`EventPlugin docs <docs/plugins/event_plugin.rst>`_).
11. Added **PostgreSqlJSONB** plugin which lets sort and filter using top level keys in PostgreSQL's `JSONB`:code:\ fields (`PostgreSqlJSONB docs <docs/plugins/postgresql_jsonb.rst>`_).


Custom fields filters example.
----------------------------------------------------------------------
Lets say we have a custom field :code:`Flag` which is built around the concept of using bytes. It's represented as a number in the database:

.. code:: python

    from enum import Enum

    class Flag(Enum):
        null = 1
        success = 1 << 1
        in_process = 1 << 2
        error = 1 << 3

To have a client work with such a field without worrying about the implementation details a custom :code:`marshmallow` field type is needed
which will do serialization and deserialization. JSON:API, as it is, cannot work with such datatype as well, unless we want the end user to worry
about its implementation details.

.. code:: python

    from enum import Enum
    from marshmallow_jsonapi import fields
    from sqlalchemy import and_, or_
    from sqlalchemy.sql.functions import GenericFunction
    from sqlalchemy import Integer


    class BitAnd(GenericFunction):
        type = Integer
        package = 'adc_custom'
        name = 'bit_and'
        identifier = 'bit_and'


    def bit_and(*args, **kwargs):
        return BitAnd(*args, **kwargs)


    class FlagField(fields.List):
        def __init__(self, *args, flags_enum=None, **kwargs):
            if flags_enum is None or not issubclass(flags_enum, Enum):
                raise ValueError("invalid attr %s" % flags_enum)
            self.flags_enum = flags_enum

            # Тип FlagField - это массив для сваггера, а элементы этого массива строки
            super().__init__(fields.String(enum=[e.name for e in self.flags_enum]), *args, **kwargs)

        @classmethod
        def _set_flag(cls, flag, add_flag):
            if add_flag:
                flag |= add_flag
            return flag

        def _deserialize(self, value, attr, data, **kwargs):
            flag = 0
            for i_flag in value:
                flag |= getattr(self.flags_enum, i_flag, 1).value
            return flag

        def _serialize(self, value, attr, obj, **kwargs):
            return [
                i_flag.name
                for i_flag in self.flags_enum
                if value & i_flag.value == i_flag.value
            ]

        def _in_sql_filter_(self, marshmallow_field, model_column, value, operator):
            """
            Создаёт фильтр для sqlalchemy с оператором in
            :param marshmallow_field: объект класса поля marshmallow
            :param model_column: объект класса поля sqlalchemy
            :param value: значения для фильтра
            :param operator: сам оператор, например: "eq", "in"...
            :return:
            """
            filters_flag = []
            for i_flag in value:
                flag = self._deserialize(0, self.flags_enum[i_flag], None, None)
                filters_flag.append(and_(flag != 0, model_column != 0, bit_and(model_column, flag) != 0))
            return or_(*filters_flag)




The author of the fork: `Aleksei Nekrasov (znbiz) <https://github.com/Znbiz>`_
