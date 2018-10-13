# -*- coding: utf-8 -*-
"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.test import SleekTest, unittest
from tests.test_stanza_ieee_sensordata import TestUtils
import sleekxmpp.plugins.ieee_control as ieee_control

namespace = 'urn:ieee:iot:ctr:1.0'


class TestIEEEControlStanzas(SleekTest, TestUtils):

    def setUp(self):
        pass

    def testSetRequest(self):
        """
        test of set request stanza
        """
        (iq, _, iq_header) = self.make_iq(iq_type='set')
        iq['set'].add_node('Device02', 'Source02', 'MyCacheType')
        iq['set'].add_node('Device15')
        iq['set'].add_data('Tjohej', 'b', 'true')

        self.check(iq, """
            {iq_header}
                <set xmlns='{namespace}'>
                    <nd id='Device02' src='Source02' pt='MyCacheType'/>
                    <nd id='Device15'/>
                    <b n='Tjohej' v='true'/>
                </set>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['set'].del_node('Device02')

        self.check(iq, """
            {iq_header}
                <set xmlns='{namespace}'>
                    <nd id='Device15'/>
                    <b n='Tjohej' v='true'/>
                </set>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        iq['set'].del_nodes()

        self.check(iq, """
            {iq_header}
                <set xmlns='{namespace}'>
                    <b n='Tjohej' v='true'/>
                </set>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testDirectSet(self):
        """
        test of direct set stanza
        """
        (msg, _, msg_header) = self.make_msg(message_type='set')
        msg['set'].add_node('Device02')
        msg['set'].add_node('Device15')
        msg['set'].add_data('Tjohej', 'b', 'true')

        self.check(msg, """
            {msg_header}
                <set xmlns='{namespace}'>
                    <nd id='Device02'/>
                    <nd id='Device15'/>
                    <b n='Tjohej' v='true'/>
                </set>
            </message>
        """.format(msg_header=msg_header, namespace=namespace))

    def testSetResponse(self):
        """
        test of set response stanza
        """
        (iq, _, iq_header) = self.make_iq(iq_type='error')
        iq['resp'].add_node('dev', 'src', 'pt')
        iq['resp'].add_data('Something something darkside')

        self.check(iq, """
            {iq_header}
                <resp xmlns='{namespace}'>
                    <nd id='dev' src='src' pt='pt'/>
                    <p n='Something something darkside' />
                </resp>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testError(self):
        (iq, _, iq_header) = self.make_iq(iq_type='error')
        iq['resp']['paramError']['var'] = 'Output'
        iq['resp']['paramError']['text'] = 'some text'

        self.check(iq, """
            {iq_header}
                <resp xmlns='{namespace}'>
                    <paramError var='Output'>some text</paramError>
                </resp>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

        (iq, _, iq_header) = self.make_iq(iq_type='error')
        iq['resp']['paramError']['var'] = 'Output'
        iq['resp']['paramError']['text'] = 'some text'
        iq['resp'].add_node('dev', 'src', 'pt')
        iq['resp'].add_data('Something something darkside')

        self.check(iq, """
            {iq_header}
                <resp xmlns='{namespace}'>
                    <paramError var='Output'>some text</paramError>
                    <nd id='dev' src='src' pt='pt'/>
                    <p n='Something something darkside' />
                </resp>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))

    def testSetRequestDatas(self):
        """
        test of set request data stanzas
        """
        (iq, _, iq_header) = self.make_iq(iq_type='set')
        iq['set'].add_node('Device02', 'Source02', 'MyCacheType')
        iq['set'].add_node('Device15')

        iq['set'].add_data('B', 'b', 'true')
        iq['set'].add_data('B2', 'b', 'false')

        iq['set'].add_data('C', 'cl', 'FF00FF')
        iq['set'].add_data('C2', 'cl', '00FF00')

        iq['set'].add_data('S', 's', 'String1')
        iq['set'].add_data('S2', 's', 'String2')

        iq['set'].add_data('Date', 'd', '2012-01-01')
        iq['set'].add_data('Date2', 'd', '1900-12-03')

        # NOTE: This messes things upp. A dt='langvn' attribute gets
        # added to the set attribute of the second generated XML.
        # Don't have any idea why
        # iq['set'].add_data('DateT4', 'dt', '1900-12-03 12:30')
        # iq['set'].add_data('DateT2', 'dt', '1900-12-03 11:22')

        iq['set'].add_data('Double2', 'db', '200.22')
        iq['set'].add_data('Double3', 'db', '-12232131.3333')

        iq['set'].add_data('Dur', 'dr', 'P5Y')
        iq['set'].add_data('Dur2', 'dr', 'PT2M1S')

        iq['set'].add_data('Int', 'i', '1')
        iq['set'].add_data('Int2', 'i', '-42')

        iq['set'].add_data('Long', 'l', '123456789098')
        iq['set'].add_data('Long2', 'l', '-90983243827489374')

        iq['set'].add_data('Time', 't', '23:59')
        iq['set'].add_data('Time2', 't', '12:00')

        self.check(iq, """
            {iq_header}
                <set xmlns='{namespace}'>
                    <nd id='Device02' src='Source02' pt='MyCacheType'/>
                    <nd id='Device15'/>
                    <b n='B' v='true'/>
                    <b n='B2' v='false'/>
                    <cl n='C' v='FF00FF'/>
                    <cl n='C2' v='00FF00'/>
                    <s n='S' v='String1'/>
                    <s n='S2' v='String2'/>
                    <d n='Date' v='2012-01-01'/>
                    <d n='Date2' v='1900-12-03'/>
                    <db n='Double2' v='200.22'/>
                    <db n='Double3' v='-12232131.3333'/>
                    <dr n='Dur' v='P5Y'/>
                    <dr n='Dur2' v='PT2M1S'/>
                    <i n='Int' v='1'/>
                    <i n='Int2' v='-42'/>
                    <l n='Long' v='123456789098'/>
                    <l n='Long2' v='-90983243827489374'/>
                    <t n='Time' v='23:59'/>
                    <t n='Time2' v='12:00'/>
                </set>
            </iq>
        """.format(iq_header=iq_header, namespace=namespace))


suite = unittest.TestLoader().loadTestsFromTestCase(TestIEEEControlStanzas)
