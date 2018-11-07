"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se,
    bjorn.westrom@consoden.se, henrik.sommerland@gmail.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import re

from sleekxmpp import Iq, Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase
from sleekxmpp.plugins.ieee_sensordata.stanza import NodeHandler

namespace = 'urn:ieee:iot:ctr:1.0'


class Control(ElementBase):
    """ Placeholder for the namespace, not used as a stanza """
    namespace = namespace
    name = 'control'
    plugin_attrib = name
    interfaces = set(tuple())


class GetForm(ElementBase, NodeHandler):
    namespace = namespace
    name = 'getForm'
    interfaces = set(['nodes', 'st', 'dt', 'ut'])


class PGroup(ElementBase):
    namespace = namespace
    name = 'pGroup'
    interfaces = set(['n'])


class ControlSet(ElementBase, NodeHandler):
    namespace = namespace
    name = 'set'
    plugin_attrib = name
    interfaces = set(['nodes', 'datas', 'st', 'dt', 'ut'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
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
        self._nodes = set([node['id'] for node in self['nodes']])
        self._datas = set([data['n'] for data in self['datas']])

    def add_data(self, name, typename, value, enum_type=None):
        """
        Add a new data element.

        Arguments:
            name       -- The name of the data element
            typename   -- The type of data element
                          (boolean, color, string, date, dateTime,
                           double, duration, int, long, time)
            value      -- The value of the data element
        """
        if name not in self._datas:
            data_obj = None
            if typename == 'b':
                data_obj = BooleanParameter(parent=self)
            elif typename == 'cl':
                data_obj = ColorParameter(parent=self)
            elif typename == 's':
                data_obj = StringParameter(parent=self)
            elif typename == 'd':
                data_obj = DateParameter(parent=self)
            elif typename == 'dt':
                data_obj = DateTimeParameter(parent=self)
            elif typename == 'db':
                data_obj = DoubleParameter(parent=self)
            elif typename == 'dr':
                data_obj = DurationParameter(parent=self)
            elif typename == 'i':
                data_obj = IntParameter(parent=self)
            elif typename == 'l':
                data_obj = LongParameter(parent=self)
            elif typename == 't':
                data_obj = TimeParameter(parent=self)
            elif typename == 'e':
                data_obj = TimeParameter(parent=self)
                data_obj['t'] = enum_type
            else:
                raise ValueError(
                    '{} typename is not a known type'.format(typename))

            data_obj['n'] = name
            if typename == 'cl':
                data_obj.set_color(value)
            else:
                data_obj['v'] = value

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
            datas = [i for i in self.iterables if isinstance(i, BaseParameter)]
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
            if isinstance(data, BaseParameter):
                datas.append(data)
        return datas

    def set_datas(self, datas):
        """
        Set or replace all data elements. The given elements must be in a
        list or set where each item is a data element
        (numeric, string, boolean, dateTime, timeSpan or enum)

        Arguments:
            datas -- A series of data elements.
        """
        self.del_datas()
        for data in datas:
            enum_type = data['t'] if 't' in data else None
            self.add_data(
                name=data['n'],
                typename=data._get_typename(),
                value=data['v'],
                enum_type=enum_type)

    def del_datas(self):
        """Remove all data elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, BaseParameter)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)


class RequestNode(ElementBase):
    """ Node element in a request """
    namespace = namespace
    name = 'nd'
    plugin_attrib = name
    interfaces = set(['id', 'src', 'pt'])


class ControlSetResponse(ElementBase, NodeHandler):
    namespace = namespace
    name = 'resp'
    plugin_attrib = name
    interfaces = set(['nodes', 'datas'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
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
        self._nodes = set([node['id'] for node in self['nodes']])
        self._datas = set([data['n'] for data in self['datas']])

    def add_data(self, name):
        """
        Add a new ResponseParameter element.

        Arguments:
            name   -- Name of the parameter
        """
        if name not in self._datas:
            self._datas.add(name)
            data = ResponseParameter(parent=self)
            data['n'] = name
            self.iterables.append(data)
            return data
        return None

    def del_data(self, name):
        """
        Remove a single ResponseParameter element.

        Arguments:
            name  -- The data element name to remove.
        """
        if name in self._datas:
            datas = [i for i in self.iterables if isinstance(
                i, ResponseParameter)]
            for data in datas:
                if data['n'] == name:
                    self.xml.remove(data.xml)
                    self.iterables.remove(data)
                    return True
        return False

    def get_datas(self):
        """ Return all ResponseParameter elements. """
        datas = set()
        for data in self['substanzas']:
            if isinstance(data, ResponseParameter):
                datas.add(data)
        return datas

    def set_datas(self, datas):
        """
        Set or replace all data elements. The given elements must be in a
        list or set of ResponseParameter elements

        Arguments:
            datas -- A series of data element names.
        """
        self.del_datas()
        for data in datas:
            self.add_data(name=data['n'])

    def del_datas(self):
        """Remove all ResponseParameter elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, ResponseParameter)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)


class Error(ElementBase):
    namespace = namespace
    name = 'paramError'
    plugin_attrib = name
    interfaces = set(['var', 'text'])

    def get_text(self):
        """Return then contents inside the XML tag."""
        return self.xml.text

    def set_text(self, value):
        """Set then contents inside the XML tag.

        Arguments:
            value -- string
        """

        self.xml.text = value
        return self

    def del_text(self):
        """Remove the contents inside the XML tag."""
        self.xml.text = ''
        return self


class ResponseParameter(ElementBase):
    """
    Parameter element in ControlSetResponse.
    """
    namespace = namespace
    name = 'p'
    plugin_attrib = name
    interfaces = set(['n'])


class BaseParameter(ElementBase):
    """
    Parameter element in SetCommand. This is a base class,
    all instances of parameters added to SetCommand must be of types:
        BooleanParameter
        ColorParameter
        StringParameter
        DateParameter
        DateTimeParameter
        DoubleParameter
        DurationParameter
        IntParameter
        LongParameter
        TimeParameter
        EnumParameter
    """
    namespace = namespace
    name = 'Parameter'
    plugin_attrib = name
    interfaces = set(['n', 'v'])

    def _get_typename(self):
        return self.name


class BooleanParameter(BaseParameter):
    """
    Field data of type boolean.
    Note that the value is expressed as a string.
    """
    name = 'b'
    plugin_attrib = name


class ColorParameter(BaseParameter):
    """
    Field data of type color.
    Note that the value is expressed as a string.
    """
    name = 'cl'
    plugin_attrib = name

    def set_color(self, color):
        if re.match('^([0-9a-fA-F]{6})|([0-9a-fA-F]{8})$', color) is not None:
            self['v'] = color
        else:
            raise ValueError('Color must be 3 or 4 byte hexadecimal value.')


class StringParameter(BaseParameter):
    """
    Field data of type string.
    """
    name = 's'
    plugin_attrib = name


class DateParameter(BaseParameter):
    """
    Field data of type date.
    Note that the value is expressed as a string.
    """
    name = 'd'
    plugin_attrib = name


class DateTimeParameter(BaseParameter):
    """
    Field data of type dateTime.
    Note that the value is expressed as a string.
    """
    name = 'dt'
    plugin_attrib = name


class DoubleParameter(BaseParameter):
    """
    Field data of type double.
    Note that the value is expressed as a string.
    """
    name = 'db'
    plugin_attrib = name


class DurationParameter(BaseParameter):
    """
    Field data of type duration.
    Note that the value is expressed as a string.
    """
    name = 'dr'
    plugin_attrib = name


class IntParameter(BaseParameter):
    """
    Field data of type int.
    Note that the value is expressed as a string.
    """
    name = 'i'
    plugin_attrib = name


class LongParameter(BaseParameter):
    """
    Field data of type long (64-bit int).
    Note that the value is expressed as a string.
    """
    name = 'l'
    plugin_attrib = name


class TimeParameter(BaseParameter):
    """
    Field data of type time.
    Note that the value is expressed as a string.
    """
    name = 't'
    plugin_attrib = name


class EnumParameter(BaseParameter):
    """
    Enumeration parameter
    """
    name = 'e'
    plugin_attrib = name
    interfaces = set(['n', 'v', 't'])


register_stanza_plugin(Iq, ControlSet)
register_stanza_plugin(Message, ControlSet)

register_stanza_plugin(ControlSet, RequestNode, iterable=True)

register_stanza_plugin(ControlSet, BooleanParameter, iterable=True)
register_stanza_plugin(ControlSet, ColorParameter, iterable=True)
register_stanza_plugin(ControlSet, StringParameter, iterable=True)
register_stanza_plugin(ControlSet, DateParameter, iterable=True)
register_stanza_plugin(ControlSet, DateTimeParameter, iterable=True)
register_stanza_plugin(ControlSet, DoubleParameter, iterable=True)
register_stanza_plugin(ControlSet, DurationParameter, iterable=True)
register_stanza_plugin(ControlSet, IntParameter, iterable=True)
register_stanza_plugin(ControlSet, LongParameter, iterable=True)
register_stanza_plugin(ControlSet, TimeParameter, iterable=True)

register_stanza_plugin(Iq, ControlSetResponse)
register_stanza_plugin(ControlSetResponse, Error)
register_stanza_plugin(ControlSetResponse, RequestNode, iterable=True)
register_stanza_plugin(ControlSetResponse, ResponseParameter, iterable=True)
