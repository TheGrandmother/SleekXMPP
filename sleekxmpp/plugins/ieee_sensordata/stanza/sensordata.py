"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se,
    bjorn.westrom@consoden.se and henrik.sommerland@gmail.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp import Iq, Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase
import re


class Sensordata(ElementBase):
    """ Placeholder for the namespace, not used as a stanza """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'sensordata'
    plugin_attrib = name
    interfaces = set(tuple())


class FieldCategories():
    """
    All field types are optional booleans that default to False
    """
    field_categories = set(['m', 'p', 's', 'c', 'i', 'h'])


class QOS():
    """
    Quality of service types
    """
    field_status = set([
        'ms', 'pr', 'ae', 'me', 'mr', 'ar', 'of',
        'w', 'er', 'so', 'iv', 'eos', 'pf', 'ic'
    ])


class NodeHandler():
    """
    Provides methods for working with collections of nodes.
    """

    def add_node(self, node_id, source_id=None,
                 source_partition=None, substanzas=None):
        """
        Add a new node element. Each item is required to have a
        node_id, but may also specify a source_id value and cacheType.

        Arguments:
            node_id  -- The ID for the node.
            source_id  -- [optional] identifying the data
                source controlling the device
            source_partition -- [optional] narrowing down
                the search to a specific kind of node
        """
        if node_id not in self._nodes:
            self._nodes.add((node_id))
            node = ResponseNode(parent=self)
            node['id'] = node_id
            node['src'] = source_id
            node['pt'] = source_partition
            if substanzas is not None:
                node.set_timestamps(substanzas)

            self.iterables.append(node)
            return node
        return None

    def del_node(self, node_id):
        """
        Remove a single node.

        Arguments:
            node_id  -- Node ID of the item to remove.
        """
        if node_id in self._nodes:
            nodes = [i for i in self.iterables if isinstance(
                i, self.node_type)]
            for node in nodes:
                if node['id'] == node_id:
                    self.xml.remove(node.xml)
                    self.iterables.remove(node)
                    return True
        return False

    def get_nodes(self):
        """Return all nodes."""
        nodes = []
        for node in self['substanzas']:
            if isinstance(node, self.node_type):
                nodes.append(node)
        return nodes

    def set_nodes(self, nodes):
        """
        Set or replace all nodes. The given nodes must be in a
        list or set where each item is a tuple of the form:
            (node_id, source_id, source_partition)

        Arguments:
            nodes -- A series of nodes in tuple format.
        """
        self.del_nodes()
        for node in nodes:
            if isinstance(node, self.node_type):
                self.add_node(node['id'], node['src'],
                              node['pt'], substanzas=node['substanzas'])
            else:
                self.add_node(*node)

    def del_nodes(self):
        """Remove all nodes."""
        self._nodes = set()
        nodes = [i for i in self.iterables if isinstance(i, self.node_type)]
        for node in nodes:
            self.xml.remove(node.xml)
            self.iterables.remove(node)


class Node(ElementBase):
    """ Node element in a request """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'nd'
    plugin_attrib = name
    interfaces = set(['id', 'src', 'pt'])


class Request(ElementBase, NodeHandler):
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'req'
    plugin_attrib = name
    node_type = Node
    interfaces = set([
        'id', 'nodes', 'fields',
        'st', 'dt', 'ut',
        'from', 'to', 'when',
        'historical', 'all'])

    interfaces.update(FieldCategories.field_categories)
    _flags = set([
        'st', 'dt', 'ut',
        'from', 'to', 'when',
        'all'])
    _flags.update(FieldCategories.field_categories)

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
        self._fields = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._nodes = set([node['id'] for node in self['nodes']])
        self._fields = set([field['n'] for field in self['fields']])

    def _get_flags(self):
        """
        Helper function for getting of flags. Returns all flags in
        dictionary format: { "flag name": "flag value" ... }
        """
        flags = {}
        for f in self._flags:
            if not self[f] == '':
                flags[f] = self[f]
        return flags

    def _set_flags(self, flags):
        """
        Helper function for setting of flags.

        Arguments:
            flags -- Flags in dictionary format: { "flag name": "flag value" }
        """
        for f in self._flags:
            if flags is not None and f in flags:
                self[f] = flags[f]
            else:
                self[f] = None

    def add_field(self, name):
        """
        Add a new field element. Each item is required to have a
        name.

        Arguments:
            name  -- The name of the field.
        """
        if name not in self._fields:
            self._fields.add(name)
            field = RequestField(parent=self)
            field['n'] = name
            self.iterables.append(field)
            return field
        return None

    def del_field(self, name):
        """
        Remove a single field.

        Arguments:
            name  -- name of field to remove.
        """
        if name in self._fields:
            fields = [i for i in self.iterables if isinstance(i, RequestField)]
            for field in fields:
                if field['n'] == name:
                    self.xml.remove(field.xml)
                    self.iterables.remove(field)
                    return True
        return False

    def get_fields(self):
        """Return all fields."""
        fields = []
        for field in self['substanzas']:
            if isinstance(field, RequestField):
                fields.append(field)
        return fields

    def set_fields(self, fields):
        """
        Set or replace all fields. The given fields must be in a
        list or set where each item is RequestField or string

        Arguments:
            fields -- A series of fields in RequestField or string format.
        """
        self.del_fields()
        for field in fields:
            if isinstance(field, RequestField):
                self.add_field(field['n'])
            else:
                self.add_field(field)

    def del_fields(self):
        """Remove all fields."""
        self._fields = set()
        fields = [i for i in self.iterables if isinstance(i, RequestField)]
        for field in fields:
            self.xml.remove(field.xml)
            self.iterables.remove(field)


class RequestField(ElementBase):
    """ Field element in a request """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'f'
    plugin_attrib = name
    interfaces = set(['n'])


class Error(ElementBase):
    """ Error element in a request failure """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'err'
    plugin_attrib = name


class ResponseNode(Node):
    """Node in a response element"""
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'nd'
    plugin_attrib = name
    interfaces = set(['id', 'src', 'pt', 'ts'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._timestamps = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._timestamps = set([ts['v'] for ts in self['ts']])

    def add_timestamp(self, timestamp, substanzas=None):
        """
        Add a new timestamp element.

        Arguments:
            timestamp  -- The timestamp in ISO format.
        """

        if timestamp not in self._timestamps:
            self._timestamps.add((timestamp))
            ts = Timestamp(parent=self)
            ts['v'] = timestamp
            if substanzas is not None:
                ts.set_datas(substanzas)
            self.iterables.append(ts)
            return ts
        return None

    def del_timestamp(self, timestamp):
        """
        Remove a single timestamp.

        Arguments:
            timestamp  -- timestamp (in ISO format) of the item to remove.
        """
        if timestamp in self._timestamps:
            timestamps = [
                i for i in self.iterables if isinstance(i, Timestamp)]
            for ts in timestamps:
                if ts['v'] == timestamp:
                    self.xml.remove(ts.xml)
                    self.iterables.remove(ts)
                    return True
        return False

    def get_timestamps(self):
        """Return all timestamps."""
        timestamps = []
        for timestamp in self['substanzas']:
            if isinstance(timestamp, Timestamp):
                timestamps.append(timestamp)
        return timestamps

    def set_timestamps(self, timestamps):
        """
        Set or replace all timestamps. The given timestamps must be in a
        list or set where each item is a timestamp

        Arguments:
            timestamps -- A series of timestamps.
        """
        self.del_timestamps()
        for timestamp in timestamps:
            if isinstance(timestamp, Timestamp):
                self.add_timestamp(
                    timestamp['v'], substanzas=timestamp['substanzas'])
            else:
                self.add_timestamp(timestamp)

    def del_timestamps(self):
        """Remove all timestamps."""
        self._timestamps = set()
        timestamps = [i for i in self.iterables if isinstance(i, Timestamp)]
        for timestamp in timestamps:
            self.xml.remove(timestamp.xml)
            self.iterables.remove(timestamp)


class Response(ElementBase, NodeHandler):
    """ Fields element, top level in a response message with data """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'resp'
    plugin_attrib = name
    node_type = ResponseNode
    interfaces = set(['id', 'more', 'nodes'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._nodes = set([node['id'] for node in self['nodes']])


class Field(ElementBase):
    """
    Field element in response Timestamp. This is a base class,
    all instances of fields added to Timestamp must be of types:
        DataQuantity
        DataInteger32
        DataInteger64
        DataString
        DataBoolean
        DataDate
        DataDateTime
        DataTime
        DataDuration
        DataEnum
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'field'
    plugin_attrib = name
    interfaces = set(['n', 'x', 'category', 'qos', 'lns', 'loc', 'ctr'])
    interfaces.update(FieldCategories.field_categories)
    interfaces.update(QOS.field_status)

    _flags = set()
    _flags.update(FieldCategories.field_categories)
    _flags.update(QOS.field_status)

    def set_localization(self, loc):
        m = re.match('^\d+([|][^,]*){0,2}(,\d+([|][^,]*){0,2})*$', loc)
        if m is None:
            raise ValueError(
                'Mallformed localization string: {}'.format(loc))
        self['loc'] = loc

    def _get_flags(self):
        """
        Helper function for getting of flags. Returns all flags in
        dictionary format: { "flag name": "flag value" ... }
        """
        flags = {}
        for f in self._flags:
            if not self[f] == '':
                flags[f] = self[f]
        return flags

    def _set_flags(self, flags):
        """
        Helper function for setting of flags.

        Arguments:
            flags -- Flags in dictionary format: { "flag name": "flag value"}
        """
        for f in self._flags:
            if flags is not None and f in flags:
                self[f] = flags[f]
            else:
                self[f] = None

    def _get_typename(self):
        return 'invalid type, use subclasses!'


class Timestamp(ElementBase):
    """ Timestamp element in response Node """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'ts'
    plugin_attrib = name
    interfaces = set(['v', 'datas'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._datas = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._datas = set([data['n'] for data in self['datas']])

    def add_data(self, typename, name, value,
                 unit=None, data_type=None, flags=None,
                 lns=None, loc=None, ctr=None):
        """
        Add a new data element.

        Arguments:
            typename   -- The type of data element
                (q, i, l, s, b, d, dt, dr, t, e)
            value      -- The value of the data element
            unit       -- [optional] The unit.
                Only applicable for type quantity
            dataType   -- [optional] The data type of an enum
        """
        if name not in self._datas:
            data_obj = None
            if typename == 'q':
                data_obj = DataQuantity(parent=self)
                data_obj['u'] = unit
            if typename == 'i':
                data_obj = DataInteger32(parent=self)
            if typename == 'l':
                data_obj = DataInteger64(parent=self)
            elif typename == 's':
                data_obj = DataString(parent=self)
            elif typename == 'b':
                data_obj = DataBoolean(parent=self)
            elif typename == 'd':
                data_obj = DataDate(parent=self)
            elif typename == 'dt':
                data_obj = DataDateTime(parent=self)
            elif typename == 'dr':
                data_obj = DataDuration(parent=self)
            elif typename == 't':
                data_obj = DataTime(parent=self)
            elif typename == 'e':
                data_obj = DataEnum(parent=self)
                data_obj['t'] = data_type

            data_obj['n'] = name
            data_obj['v'] = value

            if flags is not None:
                data_obj._set_flags(flags)

            self._datas.add(name)
            self.iterables.append(data_obj)
            return data_obj
        return None

    def del_data(self, name):
        """
        Remove a single data element.

        Arguments:
            data_name  -- The data element name to remove.
        """
        if name in self._datas:
            datas = [i for i in self.iterables if isinstance(i, Field)]
            for data in datas:
                if data['n'] == name:
                    self.xml.remove(data.xml)
                    self.iterables.remove(data)
                    return True
        return False

    def get_datas(self):
        """ Return all data elements. """
        datas = []
        for data in self['substanzas']:
            if isinstance(data, Field):
                datas.append(data)
        return datas

    def set_datas(self, datas):
        """
        Set or replace all data elements. The given elements must be in a
        list or set where each item is a data elemen.

        Arguments:
            datas -- A series of data elements.
        """
        self.del_datas()
        for data in datas:
            self.add_data(
                typename=data._get_typename(), name=data['n'], value=data['v'],
                unit=data['u'], data_type=data['t'], flags=data._get_flags())

    def del_datas(self):
        """Remove all data elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, Field)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)


class DataQuantity(Field):
    """
    Field for quantity aka float.
    """
    name = 'q'
    plugin_attrib = name
    interfaces = set(['v', 'u'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'q'


class DataInteger32(Field):
    """
    Field for a 32-bit signed integer
    """
    name = 'i'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'i'


class DataInteger64(Field):
    """
    Field for a 64-bit signed integer
    """
    name = 'l'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'l'


class DataString(Field):
    """
    Field data of type string
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 's'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 's'


class DataBoolean(Field):
    """
    Field data of type boolean.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'b'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'b'


class DataDate(Field):
    """
    Date field.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'd'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'd'


class DataDateTime(Field):
    """
    Date-Time field.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'dt'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'dt'


class DataTime(Field):
    """
    Time valued field.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 't'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 't'


class DataDuration(Field):
    """
    Duration field.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'dr'
    plugin_attrib = name
    interfaces = set(['v'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'dr'


class DataEnum(Field):
    """
    Field data of type enum.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'e'
    plugin_attrib = name
    interfaces = set(['v', 't'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return 'e'


class Accepted(ElementBase):
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'accepted'
    plugin_attrib = name
    interfaces = set(['queued', 'id'])


class Started(ElementBase):
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'started'
    plugin_attrib = name
    interfaces = set(['id'])


class Done(ElementBase):
    """ Done element used to signal that all data has been transferred """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'done'
    plugin_attrib = name
    interfaces = set(['id'])


class Cancel(ElementBase):
    """ Cancel element used to signal that a request shall be cancelled """
    namespace = 'urn:ieee:iot:sd:1.0'
    name = 'cancel'
    plugin_attrib = name
    interfaces = set(['id'])


register_stanza_plugin(Iq, Request)
register_stanza_plugin(Request, Node, iterable=True)
register_stanza_plugin(Request, RequestField, iterable=True)

register_stanza_plugin(Iq, Cancel)
register_stanza_plugin(Iq, Started)
register_stanza_plugin(Iq, Accepted)

register_stanza_plugin(Message, Done)
register_stanza_plugin(Message, Started)
register_stanza_plugin(Message, Accepted)

register_stanza_plugin(Iq, Response)
register_stanza_plugin(Message, Response)
register_stanza_plugin(Response, ResponseNode, iterable=True)
register_stanza_plugin(ResponseNode, Timestamp, iterable=True)
register_stanza_plugin(Timestamp, Field, iterable=True)
register_stanza_plugin(Timestamp, DataQuantity, iterable=True)
register_stanza_plugin(Timestamp, DataInteger32, iterable=True)
register_stanza_plugin(Timestamp, DataInteger64, iterable=True)
register_stanza_plugin(Timestamp, DataString, iterable=True)
register_stanza_plugin(Timestamp, DataBoolean, iterable=True)
register_stanza_plugin(Timestamp, DataDateTime, iterable=True)
register_stanza_plugin(Timestamp, DataTime, iterable=True)
register_stanza_plugin(Timestamp, DataDate, iterable=True)
register_stanza_plugin(Timestamp, DataDuration, iterable=True)
register_stanza_plugin(Timestamp, DataEnum, iterable=True)
