import os
import sys
import socket

# This can be used when you are in a test environment and need to make paths right
sys.path=[os.path.join(os.path.dirname(__file__), '../..')]+sys.path
sys.path=[os.path.join(os.path.dirname(__file__), '../../../influxdb-python')]+sys.path

import logging
import unittest
import distutils.core
import datetime

from glob import glob
from os.path import splitext, basename, join as pjoin
from optparse import OptionParser
from optparse import Option, OptionValueError
from urllib import urlopen

import sleekxmpp
# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input
    
from sleekxmpp.plugins.xep_0323.device import Device as SensorDevice
from IoT_FileLogger import Logger as Logger
#from IoT_Logger import FileLogger as Logger
#from IoT_Logger import InfluxLogger as Logger
#from sleekxmpp.exceptions import IqError, IqTimeout

class MultipleOption(Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            values.ensure_value(dest, []).append(value)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)
            

class IoT_HistoryLogger(sleekxmpp.ClientXMPP):

    """
    A simple IoT device client that asks another JID for values and stores it laclally based on Xep 323
    """
    
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0323')
        # self.register_plugin('xep_0325') we don't need to write to devices
        self.register_plugin('xep_0199') # XMPP ping

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("changed_status",self.manage_status)

        #Some local status variables to use
        self.device = None
        self.logger = Logger()
        self.client_jids=[]
        self.received = set()
        self.controlField = None
        self.controlValue = None
        self.controlType = None
        self.delayValue = None
        self.toggle = 0
        self.fieldsRegistered = False

    def add_client_jid(self, client_jid):
        self.client_jids.append(client_jid)
        
    def addDevice(self, device):
        self.device=device
        
    def datacallback(self,from_jid,result,nodeId=None,timestamp=None,fields=None,error_msg=None):
        """
        This method will be called back to when you ask another IoT device for data with the xep_0323
        fields example
        [{'typename': 'numeric', 'unit': 'C', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'temperature', 'value': '13.5'},
        {'typename': 'numeric', 'unit': 'mb', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'barometer', 'value': '1015.0'},
        {'typename': 'numeric', 'unit': '%', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'humidity', 'value': '78.0'}]
        """
        
        if error_msg:
            logging.error('we got problem when recieving data %s', error_msg)
            return
        
        if result=='accepted':
            # first stage after we ask for value the device is preparing data for us
            logging.debug("we got accepted from %s",from_jid)            
        elif result=='fields':
            # second stage we now recieve one or more messages with values on the fields
            logging.info("we got fields from %s on node %s",from_jid,nodeId)
            if self.device.nodeId!=nodeId:
                logging.warn("ooops nodeId %s differ %s try resetting local"%(self.device.nodeId,nodeId))
                self.device.nodeId=nodeId
            if not self.fieldsRegistered:
                self.fieldsRegistered = True
                for field in fields:
                    if field.has_key('unit'):
                        xmpp.device._add_field(name=field['name'], typename=field['typename'], unit=field['unit'])
                    else:
                        xmpp.device._add_field(name=field['name'], typename=field['typename'], unit='')
            for field in fields:
                # Storing in local Logger
                if field.has_key('unit'):
                    self.logger.LocalStore(from_jid, timestamp, nodeId, field['typename'], field['name'], field['value'], field['unit'])
                else:
                    self.logger.LocalStore(from_jid, timestamp, nodeId, field['typename'], field['name'], field['value'], '')
                info="(%s %s %s) " % (nodeId,field['name'],field['value'])
                if field.has_key('unit'):
                    info+="%s " % field['unit']
                if field.has_key('flags'):
                    info+="["
                    for flag in field['flags'].keys():
                        info+=flag + ","
                    info+="]"
                logging.info(info)
        elif result=='done':
            # this is the final stage we have now recieved all data from the other device. The session is closed
            logging.debug("we got  done from %s",from_jid)
        
    def printRoster(self):
        logging.debug('-' * 72)
        logging.debug('Roster for %s' % self.boundjid.bare)
        groups = self.client_roster.groups()
        for group in groups:
            logging.debug('%s' % group)
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    logging.debug(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    logging.debug(' %s [%s]' % (jid, sub))
                    
                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    if res==self.boundjid.resource:
                        res=res+"(myself)"
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    logging.debug('   - %s (%s)' % (res, show))
                    if pres['status']:
                        logging.debug('       %s' % pres['status'])

    def manage_status(self, event):
        logging.debug("got a status update" + str(event.getFrom()))
        self.printRoster()
        
    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        # tell your preffered friend that you are alive 
        self.send_message(mto='jabberjocke@jabber.se', mbody=self.boundjid.bare +' is now online use xep_323 stanza to talk to me')

        logging.info('We are a client start asking %s for values' % str(self.client_jids))
        self.schedule('end', self.delayValue, self.askClientForValue, repeat=True, kwargs={})

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['body'].startswith('hi'):
                logging.info("got normal chat message" + str(msg))
                internetip=urlopen('http://icanhazip.com').read()
                localip=socket.gethostbyname(socket.gethostname())
                msg.reply("I am " + self.boundjid.full + " and I am on localIP " +localip +" and on internet " + internetip).send()
            elif msg['body'].startswith('?'):
                logging.debug('got a question ' + str(msg))
                self.device.refresh([])
                logging.debug('momentary values' + str(self.device.momentary_data))
                msg.reply(str(self.device.momentary_data)).send()
            elif msg['body'].startswith('T'):
                logging.debug('got a toggle ' + str(msg))
                if self.device.relay:
                    self.device.relay=False
                else:
                    self.device.srelay=True
            elif msg['body'].find('=')>0:
                logging.debug('got a control' + str(msg))
                (variable,value)=msg['body'].split('=')
                logging.debug('setting %s to %s' % (variable,value))
            else:
                logging.debug('message dropped ' +  msg['body'])
        else:
            logging.debug("got unknown message type %s", str(msg['type']))

    def askClientForValue(self):
        for a_jid in self.client_jids:
            connections=self.client_roster.presence(a_jid)
            all_connection_items=connections.items()
            if len(self.client_jids)==1 and a_jid==self.boundjid.bare and len(all_connection_items)==1:
                #we re asking our self for data and there is only one of me
                logging.warning("there is nobody to call for data for on "+ self.a_jid)
                return
            logging.info('IoT will call for data to '+ a_jid)
            for res, pres in connections.items():
                # ask every session on the jid for data
                if res!=self.boundjid.resource:
                    logging.debug("asking : %s / %s"%(a_jid,res))
                    #ignoring myself if we are 
                    if self.controlField:
                        session=self['xep_0323'].request_data(self.boundjid.full,a_jid+"/"+res,self.datacallback, fields=[self.controlField],flags={"momentary":"true"})
                    else:
                        session=self['xep_0323'].request_data(self.boundjid.full,a_jid+"/"+res,self.datacallback, flags={"momentary":"true"})
            
class TheDevice(SensorDevice):
    """
    Xep 323 SensorDevice
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you
    """
    def __init__(self,nodeId):
        SensorDevice.__init__(self,nodeId)
        self.logger = Logger() 

    def get_history(self, session, fields, from_flag, to_flag, callback):
        """
        looks in storage for the history and returns a series with te history
        """
        time_block = []
        for field in fields:
            timestamp, node, typename, name, value, unit = self.logger.LocalRetrieve(opts.jid, field, from_flag, to_flag)
            for i in range(len(timestamp)):
                ts_block = {}
                field_block = [];
                field_block.append({"name": name[i],
                                    "type": typename[i], 
                                    "unit": unit[i],
                                    "dataType": None,
                                    "value": value[i], 
                                    "flags": {'historical': 'true', 'automaticReadout': 'true'}})
                ts_block["timestamp"] = timestamp[i]
                ts_block["fields"] = field_block
                time_block.append(ts_block)
        logging.info('History ready calling callback nodeid %s data %s'%(self.nodeId,str(time_block)))
        callback(session, result="done", nodeId=self.nodeId, timestamp_block=time_block);
        return
        
if __name__ == '__main__':
    """
    To Run and call your self :
    python IoT_HistoryLogger.py -j device1@xmpp.xmpp-iot.org -p passwd --phost proxy.iiit.ac.in --pport 8080 --delay 10 --debug

    # call anotherjid@xmpp.xmpp-iot.org (must be part of roster and online)
    python IoT_HistoryLogger.py -j device1@xmpp.xmpp-iot.org -p passwd --phost proxy.iiit.ac.in --pport 8080 --delay 10 --debug -g anotherjid@xmpp.xmpp-iot.org

    # calling several jids
    python IoT_HistoryLogger.py -j device1@xmpp.xmpp-iot.org -p passwd --phost proxy.iiit.ac.in --pport 8080 --delay 10 --debug -g anotherjid@xmpp.xmpp-iot.org -g yetanother@xmpp.xmpp-iot.org ...
    
    """

    optp = OptionParser(option_class=MultipleOption)

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)


    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-g", "--getsensorjid", dest="getsensorjid",action="extend",type="string",
                    help="Device jid to call for data on can be a list of jids", default = None)
    optp.add_option("--phost", dest="proxy_host",
                    help="Proxy hostname", default = None)
    optp.add_option("--pport", dest="proxy_port",
                    help="Proxy port", default = None)
    optp.add_option("--puser", dest="proxy_user",
                    help="Proxy username", default = None)
    optp.add_option("--ppass", dest="proxy_pass",
                    help="Proxy password", default = None)

    optp.add_option("--delay", dest="delayvalue",
                    help="secondsdelay between reads", default=30)
    
    opts, args = optp.parse_args()

     # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = raw_input("Password: ")
        
    xmpp = IoT_HistoryLogger(opts.jid,opts.password)
    xmpp.delayValue=int(opts.delayvalue)
    logging.debug("DELAY " + str(int(opts.delayvalue)) + "  " + str(xmpp.delayValue))
    
    if opts.proxy_host:
        xmpp.use_proxy = True
        xmpp.proxy_config = {
            'host' : opts.proxy_host,
            'port' : int(opts.proxy_port),
            'username' : opts.proxy_user,
            'password' : opts.proxy_pass}
    
    logging.debug("will try to call another device for data")
    myDevice = TheDevice("dummy");
    xmpp.device=myDevice
    xmpp['xep_0323'].register_node(nodeId="ctcpump", device=myDevice, commTimeout=10);
    logging.debug(str((opts.getsensorjid)))
    logging.debug(str(type(opts.getsensorjid)))
                  
    if opts.getsensorjid!=None and type(opts.getsensorjid)==type([]):
        logging.debug(str(opts.getsensorjid))
        for jid in opts.getsensorjid:
            xmpp.add_client_jid(jid)
    elif opts.getsensorjid:
        # asking another jid for values
        xmpp.add_client_jid(opts.getsensorjid)
    else:
        # Default to asking another instanse of myself 
        xmpp.add_client_jid(opts.jid)
    xmpp.connect()
    xmpp.process(block=True)
    logging.debug("ready ending")
