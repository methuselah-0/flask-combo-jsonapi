from jsonapi_utils.constants import DEFAULT_PAGE_SIZE
from jsonapi_utils.data_layers.base import BaseDataLayer
from jsonapi_utils.exceptions import EntityNotFound
from pymongo import ASCENDING, DESCENDING


class MongoDataLayer(BaseDataLayer):

    def __init__(self, **kwargs):
        if kwargs.get('mongo') is None:
            raise Exception('You must provide a mongo connection')
        if kwargs.get('collection') is None:
            raise Exception('You must provide a collection to query')
        if kwargs.get('model') is None:
            raise Exception('You must provide a proper model class !')
        self.mongo = kwargs['mongo']
        self.key_param_name = kwargs.get('url_param_name')
        self.kwargs = kwargs

    def get_collection(self):
        collection = getattr(self.mongo, self.kwargs['collection'], None)
        if collection is None:
            raise Exception(
                'Collection %s does not exist' % self.kwargs['collection']
            )
        return collection

    def get_item(self, **view_kwargs):
        """Retrieve a single item from mongodb.

        :params dict view_kwargs: kwargs from the resource view
        :return dict: a mongo document
        """
        query = {self.kwargs['id_field']: view_kwargs.get('key_param_name')}
        result = self.get_collection().find_one(query)
        if result is None:
            raise EntityNotFound(self.kwargs['collection'],
                                 view_kwargs.get('key_param_name'))
        return result

    def persiste_update(self):
        """Since mongo does not use transaction, this method
        does not need an implementation."""
        pass

    def get_items(self, qs, **view_kwargs):
        query = self.get_base_query(**view_kwargs)
        if qs.filters:
            query = self.filter_query(query, qs.filters, self.kwargs['model'])
        query = self.get_collection().find(query)
        if qs.sorting:
            query = self.sort_query(query, qs.sorting)
        item_count = query.count()
        query = self.paginate_query(query, qs.pagination)

        return item_count, list(query)

    def filter_query(self, query, filter_info, model):
        """Filter query according to jsonapi rfc

        :param dict: mongo query dict
        :param list filter_info: filter information
        :return dict: a new mongo query dict

        """
        for item in filter_info.items()[model.__name__.lower()]:
            op = {'$%s' % item['op']: item['value']}
            query[item['field']] = op
        return query

    def paginate_query(self, query, paginate_info):
        """Paginate query according to jsonapi rfc

        :param pymongo.cursor.Cursor query: pymongo cursor
        :param dict paginate_info: pagination information
        :return pymongo.cursor.Cursor: the paginated query
        """
        page_size = int(paginate_info.get('sitze, 0')) or DEFAULT_PAGE_SIZE
        if paginate_info.get('number'):
            offset = int(paginate_info['number'] - 1) * page_size
        else:
            offset = 0
        return query[offset:offset+page_size]

    def sort_query(self, query, sort_info):
        """Sort query according to jsonapi rfc

        :param pymongo.cursor.Cursor query: pymongo cursor
        :param list sort_info: sort information
        :return pymongo.cursor.Cursor: the paginated query
        """
        expressions = {'asc': ASCENDING, 'desc': DESCENDING}
        for sort_opt in sort_info:
            field = sort_opt['field']
            order = expressions.get(sort_opt['order'])
            query = query.sort(field, order)
        return query

    def create_and_save_item(self, data, **view_kwargs):
        """
        Create and save a mongo document.

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return object: A publimodels object
        """
        self.before_create_instance(data, **view_kwargs)
        item = self.kwargs['model'](**data)
        self.get_collection().save(item)
        return item

    def persist_update(self):
        """Make changes made on an item persistant
        through the data layer"""
        pass

    def before_create_instance(self, data, **view_kwargs):
        """
        Hook called at object creation.

        :param dict data: data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def get_base_query(self, **view_kwargs):
        """
        Construct the base query to retrieve wanted data.
        This would be created through metaclass.

        :param dict view_kwargs: Kwargs from the resource view
        """
        raise NotImplemented

    @classmethod
    def configure(cls, data_layer):
        """
        Plug get_base_query to the instance class.

        :param dict data_layer: information from Meta class used to configure
        the data layer
        """
        if (data_layer.get('get_base_query') is None or
                not callable(data_layer['get_base_query'])):
            raise Exception('You must provide a get_base_query function'
                            ' width self as first parameter')
        cls.get_base_query = data_layer['get_base_query']
