# -*- coding: utf-8 -*-

from random import randint
from sleekxmpp.test import unittest, SleekTest
import sleekxmpp.plugins.ieee_sensordata


namespace = 'urn:ieee:iot:sd:1.0'


class TestIEEESensorDataStanzas(SleekTest):

    def make_iq(self, iq_type='get', iq_from=None, iq_to=None, iq_id=None):
        iq = self.Iq()
        iq['type'] = iq_type
        if iq_from is not None:
            iq['from'] = iq_from
        else:
            iq['from'] = 'client@example.com/{}'.format(randint(0, 100))

        if iq_from is not None:
            iq['to'] = iq_to
        else:
            iq['to'] = 'device@example.com/{}'.format(randint(0, 100))

        if iq_from is not None:
            iq['id'] = iq_id
        else:
            iq['id'] = str(randint(0, 100))

        params = {'iq_type': iq['type'], 'iq_from': iq['from'],
                  'iq_to': iq['to'], 'iq_id': iq['id']}
        iq_header = """
            <iq type='{iq_type}'
                from='{iq_from}'
                to='{iq_to}'
                id='{iq_id}'>
        """.format(**params)

        return (iq,
                params,
                iq_header)

    def make_msg(self, message_type='normal', message_from=None, message_to=None, message_id=None):
        message = self.Message()
        message['type'] = message_type
        if message_from is not None:
            message['to'] = message_from
        else:
            message['to'] = 'client@example.com/{}'.format(randint(0, 100))

        if message_from is not None:
            message['from'] = message_to
        else:
            message['from'] = 'device@example.com/{}'.format(randint(0, 100))

        if message_from is not None:
            message['id'] = message_id
        else:
            message['id'] = str(randint(0, 100))

        params = {
            'message_type': message['type'], 'message_from': message['from'],
            'message_to': message['to'], 'message_id': message['id']}
        message_header = """
            <message type='{message_type}'
                from='{message_from}'
                to='{message_to}'
                id='{message_id}'>
        """.format(**params)

        return (message,
                params,
                message_header)

    def setUp(self):
        pass

    def testRequest(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        (iq, _, iq_header) = self.make_iq()
        iq['req']['id'] = '42'
        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='42'>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testRequestNodes(self):
        """
        test of request nodes stanza
        """
        (iq, _, iq_header) = self.make_iq()
        iq['req']['id'] = '2'
        iq['req']['m'] = 'true'

        iq['req'].add_node('Device02', 'Source02', 'partition')
        iq['req'].add_node('Device44')

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='2' m='true'>
                    <nd id='Device02' src='Source02' pt='partition'/>
                    <nd id='Device44'/>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['req'].del_node('Device02')

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='2' m='true'>
                    <nd id='Device44'/>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['req'].del_node('Device44')

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='2' m='true'>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testRequestField(self):
        """
        test of request field stanza
        """
        (iq, _, iq_header) = self.make_iq()
        iq['req']['id'] = '1'

        iq['req'].add_field('Top temperature')
        iq['req'].add_field('Bottom temperature')

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='1'>
                    <f n='Top temperature'/>
                    <f n='Bottom temperature'/>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['req'].del_field('Top temperature')

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='1'>
                    <f n='Bottom temperature'/>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['req'].del_fields()

        self.check(iq, """
            {iq_header}
                <req xmlns='{namespace}' id='1'>
                </req>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testAccepted(self):
        (iq, _, iq_header) = self.make_iq()
        iq['accepted']['id'] = '2'

        self.check(iq, """
            {iq_header}
                <accepted xmlns='{namespace}' id='2'/>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testStarted(self):
        (iq, _, iq_header) = self.make_iq()
        iq['started']['id'] = '2'

        self.check(iq, """
            {iq_header}
                <started xmlns='{namespace}' id='2'/>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testCancel(self):
        (iq, _, iq_header) = self.make_iq()
        iq['cancel']['id'] = '2'

        self.check(iq, """
            {iq_header}
                <cancel xmlns='{namespace}' id='2'/>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testStartedAsMessage(self):
        (msg, _, msg_header) = self.make_msg()

        msg['started']['id'] = '1'

        self.check(msg, """
            {msg_header}
                <started xmlns='{namespace}' id='1'/>
            </message>
        """.format(namespace=namespace, msg_header=msg_header))

    def testDone(self):
        (msg, _, msg_header) = self.make_msg()

        msg['done']['id'] = '1'

        self.check(msg, """
            {msg_header}
                <done xmlns='{namespace}' id='1'/>
            </message>
        """.format(namespace=namespace, msg_header=msg_header))

    def testResponse(self):
        (iq, _, iq_header) = self.make_iq()
        iq['resp']['id'] = '1'

        self.check(iq, """
            {iq_header}
                <resp xmlns='{namespace}' id='1'>
                </resp>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testResponseFields(self):
        (msg, _, msg_header) = self.make_msg()

        msg['resp']['id'] = '1'
        node = msg['resp'].add_node('Device02')
        ts = node.add_timestamp('2013-03-07T16:24:30')

        data = ts.add_data('q', 'Temperature', '-12.42', unit='K')
        data['m'] = 'true'
        data['ar'] = 'true'

        self.check(msg, """
            {msg_header}
                <resp xmlns='{namespace}' id='1'>
                    <nd id='Device02'>
                        <ts v='2013-03-07T16:24:30'>
                            <q n='Temperature' m='true' ar='true' v='-12.42' u='K'/>
                        </ts>
                    </nd>
                </resp>
            </message>
        """.format(msg_header=msg_header, namespace=namespace))

        node = msg['resp'].add_node('EmptyDevice')
        node = msg['resp'].add_node('Device04')
        ts = node.add_timestamp('EmptyTimestamp')

        self.check(msg, """
            {msg_header}
                <resp xmlns='{namespace}' id='1'>
                    <nd id='Device02'>
                        <ts v='2013-03-07T16:24:30'>
                            <q n='Temperature' m='true' ar='true' v='-12.42' u='K'/>
                        </ts>
                    </nd>
                    <nd id='EmptyDevice'/>
                    <nd id='Device04'>
                        <ts v='EmptyTimestamp'/>
                    </nd>
                </resp>
            </message>
        """.format(msg_header=msg_header, namespace=namespace))

        node = msg['resp'].add_node('Device77')
        ts = node.add_timestamp('2013-05-03T12:00:01')

        data = ts.add_data('q',
                           'Temperature', '-12.42', unit='K')
        data['h'] = 'true'

        data = ts.add_data('q', 'Speed',
                           '312.42', unit='km/h')
        data['h'] = 'false'

        data = ts.add_data('s',
                           'Temperature name', 'Bottom oil')
        data['h'] = 'true'

        data = ts.add_data('s',
                           'Speed name', 'Top speed')
        data['h'] = 'false'

        data = ts.add_data('dt', 'T1',
                           '1979-01-01T00:00:00')
        data['h'] = 'true'

        data = ts.add_data('dt', 'T2',
                           '2000-01-01T01:02:03')
        data['h'] = 'false'

        data = ts.add_data('dr', 'TS1', 'P5Y')
        data['ms'] = 'true'

        data = ts.add_data('dr', 'TS2', 'PT2M1S')
        data['me'] = 'false'

        data = ts.add_data('e', 'Top color',
                           'red', data_type='string')
        data['iv'] = 'true'

        data = ts.add_data('e', 'Bottom color',
                           'black', data_type='string')
        data['pf'] = 'false'

        data = ts.add_data('b',
                           'Temperature real', 'false')
        data['h'] = 'true'

        data = ts.add_data('b', 'Speed real', 'true')
        data['h'] = 'false'

        self.check(msg, """
            {msg_header}
                <resp xmlns='{namespace}' id='1'>
                    <nd id='Device02'>
                        <ts v='2013-03-07T16:24:30'>
                            <q n='Temperature' m='true' ar='true' v='-12.42' u='K'/>
                        </ts>
                    </nd>
                    <nd id='EmptyDevice'/>
                    <nd id='Device04'>
                        <ts v='EmptyTimestamp'/>
                    </nd>
                    <nd id='Device77'>
                        <ts v='2013-05-03T12:00:01'>
                            <q n='Temperature' h='true' v='-12.42' u='K'/>
                            <q n='Speed' h='false' v='312.42' u='km/h'/>
                            <s n='Temperature name' h='true' v='Bottom oil'/>
                            <s n='Speed name' h='false' v='Top speed'/>
                            <dt n='T1' h='true' v='1979-01-01T00:00:00'/>
                            <dt n='T2' h='false' v='2000-01-01T01:02:03'/>
                            <dr n='TS1' ms='true' v='P5Y'/>
                            <dr n='TS2' me='false' v='PT2M1S'/>
                            <e n='Bottom color' pf='false' v='black' t='string'/>
                            <e n='Top color' iv='true' v='red' t='string'/>
                            <b n='Temperature real' h='true' v='false'/>
                            <b n='Speed real' h='false' v='true'/>
                        </ts>
                    </nd>
                </resp>
            </message>
        """.format(msg_header=msg_header, namespace=namespace))

    def testTimestamp(self):
        (msg, _, msg_header) = self.make_msg()

        msg['resp']['id'] = '1'

        node = msg['resp'].add_node("Device02")
        node = msg['resp'].add_node("Device03")

        node.add_timestamp("2013-03-07T16:24:30")
        node.add_timestamp("2013-03-07T16:24:31")

        self.check(msg, """
            {msg_header}
                <resp xmlns='{namespace}' id='1'>
                    <nd id='Device02'/>
                    <nd id='Device03'>
                        <ts v='2013-03-07T16:24:30'/>
                        <ts v='2013-03-07T16:24:31'/>
                    </nd>
                </resp>
            </message>
        """.format(msg_header=msg_header, namespace=namespace))


suite = unittest.TestLoader().loadTestsFromTestCase(TestIEEESensorDataStanzas)
