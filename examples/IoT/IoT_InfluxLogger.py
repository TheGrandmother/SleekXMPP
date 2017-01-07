import os
import logging
from influxdb import InfluxDBClient

class Logger:
    """An API for storing and retrieving History Information in an influx database"""
    def __init__(self,username='',password='',dbname='',dburl=''):
        self.client=None
        self.dburl=dburl
        self.port=port
        self.username=username
        self.password=password
        self.dbname=dbname
        
    def connect_client(self)
        """
        """
        self.client = InfluxDBClient(self.dburl, self.port, self.username, self.password, self.dbname)
        
    def LocalStore(self, jid, timestamp, node, typename, field, value, unit):
        """
        """
        json_body = [{
            "measurement": node+"/"+field,
            "tags": {
                "jid": jid,
                "type": typename,
                "unit": unit
            },
            "time": timestamp,
            "fields": {
                "value": value
            }
        }]
        if not self.client:
            self.connect_client()
            
        self.client.client.write_points(json_body)
        
    def LocalRetrieve(self, jid, field, fromTime, toTime):
        """Retrieves History from influx Storage"""
        #todo
        timestamp = []
        node = []
        typename = []
        name = []
        value = []
        unit = []
        #SELECT data from influx
        #    for line in f:
        #        data = line.split('; ')
        #        if data[0] > fromTime and data[0] < toTime:
        #            timestamp.append(data[0])
        #            node.append(data[1])
        #            typename.append(data[2])
        #            name.append(data[3])
        #            value.append(data[4])
        #            unit.append(data[5].split('\n')[0])
        return (timestamp, node, typename, name, value, unit)
