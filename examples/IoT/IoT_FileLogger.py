import os
import logging

# Used by the IoT_HistoryLogger to store data in local file storage

class Logger:
    """An API for storing and retrieving History Information"""
    def __init__(self,basedir='store'):
        self.basedir=basedir
        
    def LocalStore(self, jid, timestamp, node, typename, field, value, unit):
        """Stores Timestamped Values of Fields of a Jid in Files as a Log for History"""
        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)
        if not os.path.exists(self.basedir+'/'+jid.node):
            os.makedirs(self.basedir+'/'+jid.node)

        os.chdir(self.basedir+'/'+jid.node)

        info = timestamp+'; '+node+'; '+typename+'; '+field+'; '+value+'; '+unit+'\n'

        with open(field+'.log', 'a') as f:
            f.write(info)

        os.chdir('../..')
        return

    def LocalRetrieve(self, jid, field, fromTime, toTime):
        """Retrieves History from Local Storage"""
        os.chdir(self.basedir+'/'+jid.split('@')[0])
        timestamp = []
        node = []
        typename = []
        name = []
        value = []
        unit = []
        with open(field+'.log', 'r') as f:
            for line in f:
                logging.debug("file data line " + str(line))
                data = line.split('; ')
                if data[0] > fromTime and data[0] < toTime:
                    timestamp.append(data[0])
                    node.append(data[1])
                    typename.append(data[2])
                    name.append(data[3])
                    value.append(data[4])
                    unit.append(data[5].split('\n')[0])
        os.chdir('../..')
        return (timestamp, node, typename, name, value, unit)
