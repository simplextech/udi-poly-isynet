#!/usr/bin/env python
"""
This is a NodeServer template for Polyglot v2 written in Python2/3
by Einstein.42 (James Milne) milne.james@gmail.com
"""
from functools import partial

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import time
import PyISY
import re

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'ISY-Net Controller'
        self.poly.onConfig(self.process_config)
        self.user = None
        self.password = None
        self.ipaddress = None
        self.port = None
        self.isy = None

    def start(self):
        LOGGER.info('Started ISY-Net NodeServer')
        self.removeNoticesAll()
        if self.check_params():
            self.isy = PyISY.ISY(self.ipaddress, '80', self.user, self.password)
            if self.isy.connected:
                LOGGER.info('ISY Connected: True')
                self.isy.auto_update = True
                self.discover()
            else:
                LOGGER.info('ISY Connected: False')

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        for nid in self.isy.nodes.nids:
            if re.match(r'^ZW', nid):
                # print(self.isy.nodes[nid].type)
                r_name = self.isy.nodes[nid].name
                r_address = nid
                # print(self.isy.nodes[nid].uom)
                r_uom = self.isy.nodes[nid].uom
                r_prec = self.isy.nodes[nid].prec
                # r_parent = self.isy.nodes[nid].parent_node
                # r_pnode = self.isy.nodes[nid].parent_node
                # r_parent = r_pnode.nid
                r_type = self.isy.nodes[nid].type
                devtype_cat = self.isy.nodes[nid].devtype_cat
                # print('DevType Cat: ' + devtype_cat)
                # print('Type: ' + str(r_type))

                m_name = str(r_name)
                m_address = str(r_address).lower()

                if self.isy.nodes[nid].parent_node is not None:
                    r_pnode = self.isy.nodes[nid].parent_node
                    r_parent = r_pnode.nid
                    m_parent = str(r_parent).lower()
                    # print('Emeter Parent: ' + m_parent)
                else:
                    m_parent = None

                if devtype_cat == '121':
                    # print(m_name, nid, r_uom, r_prec, m_parent)
                    if m_parent is None:
                        self.addNode(SwitchNode(self, m_address, m_address, m_name))
                        # self.subscribe(nid)
                    else:
                        self.addNode(SwitchNode(self, m_parent, m_address, m_name))
                    self.subscribe(nid)
                if devtype_cat == '143':
                    # print(m_name, nid, r_uom, r_prec, m_parent)
                    if m_parent is None:
                        self.addNode(EmeterNode(self, m_address, m_address, m_name))
                        # self.subscribe(nid)
                    else:
                        self.addNode(EmeterNode(self, m_parent, m_address, m_name))
                    self.subscribe(nid)
                if devtype_cat == '140':
                    # print(m_name, nid, r_uom, r_prec, m_parent)
                    if m_parent is None:
                        self.addNode(TStatNode(self, m_address, m_address, m_name))
                        # self.subscribe(nid)
                    else:
                        self.addNode(TStatNode(self, m_parent, m_address, m_name))
                    self.subscribe(nid)

    def val_split(self, val):
        return list(val)

    def val_prec(self, val, nid):
        # poly_node = str(nid).lower()
        r_node = self.isy.nodes[nid]
        # r_uom = r_node.uom
        r_prec = int(r_node.prec)
        raw_val = str(val)
        split_val = self.val_split(raw_val)

        print('Precision: ' + str(r_prec))
        # if r_prec == 1:
        #     _int = split_val[0:-r_prec]
        #     _sep = ''
        #     _v = _sep.join(_int)
        #     _d = '0'
        #     if _v is '':
        #         _v = '0'
        #     if _d is '':
        #         _d = '0'
        #     _val = '{0}.{1}'.format(_v, _d)
        # elif r_prec > 1:
        #     _int = split_val[0:-r_prec]
        #     _dec = split_val[-r_prec:]
        #     _sep = ''
        #     _v = _sep.join(_int)
        #     _d = _sep.join(_dec)
        #     if _v is '':
        #         _v = '0'
        #     if _d is '':
        #         _d = '0'
        #     _val = '{0}.{1}'.format(_v, _d)
        # else:
        #     _val = raw_val
        if r_prec:
            if r_prec > 1:
                _int = split_val[0:-r_prec]
                _dec = split_val[-r_prec:]
            else:
                _int = split_val[0:-1]
                _dec = split_val[-1:]
            _sep = ''
            _v = _sep.join(_int)
            _d = _sep.join(_dec)
            if _v is '':
                _v = '0'
            if _d is '':
                # _d = '0'
                _d = '0' * r_prec
            _val = '{0}.{1}'.format(_v, _d)
        else:
            _val = raw_val

        return _val

    def notify(self, e, nid):
        LOGGER.info('Notification Received')
        # print(e)
        poly_node = str(nid).lower()
        r_node = self.isy.nodes[nid]
        r_uom = r_node.uom
        # r_prec = int(r_node.prec)
        raw_val = str(e.handles)

        if r_uom == '78':
            if raw_val == '255':
                _val = '100'
            else:
                _val = raw_val
            self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)
        # elif r_uom == '67':
        #     _val = raw_val
        #     self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)
        elif raw_val is not '':
            _val = self.val_prec(raw_val, nid)
        else:
            _val = '0'
        self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)

    def on_control(self, event, nid):
        # print(self, event)
        # print(help(event))
        # print(nid, event.nval, event.uom, event.prec, event.event)
        # print(nid, event, event.nval, event.uom, event.prec)

        poly_node = str(nid).lower()
        # r_node = self.isy.nodes[nid]
        r_uom = event.uom
        # r_prec = int(event.prec)
        raw_val = str(event.nval)
        r_event = event.event

        # if int(raw_val) > 1:
        #     _val = self.val_prec(raw_val, nid)
        # else:
        #     _val = '0'
        _val = self.val_prec(raw_val, nid)

        if r_event == 'TPW':
            self.nodes[poly_node].setDriver('TPW', _val, uom=r_uom)
        if r_event == 'CC':
            self.nodes[poly_node].setDriver('CC', _val, uom=r_uom)
        if r_event == 'CV':
            self.nodes[poly_node].setDriver('CV', _val, uom=r_uom)
        if r_event == 'CLISPC':
            self.nodes[poly_node].setDriver('CLISPC', _val, uom=r_uom)
        if r_event == 'CLISPH':
            self.nodes[poly_node].setDriver('CLISPH', _val, uom=r_uom)
        if r_event == 'CLIMD':
            _val = raw_val
            self.nodes[poly_node].setDriver('CLIMD', _val, uom=r_uom)
        if r_event == 'CLIHCS':
            _val = raw_val
            self.nodes[poly_node].setDriver('CLIHCS', _val, uom=r_uom)

    def subscribe(self, nid):
        print('Subscribing to: ' + nid)
        isy_node = self.isy.nodes[nid]
        isy_node.status.subscribe('changed', partial(self.notify, nid=nid))
        control_handler = isy_node.controlEvents.subscribe(partial(self.on_control, nid=nid))
        # print(control_handler)

    def delete(self):
        """
        Example
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        # LOGGER.info("process_config: Enter config={}".format(config))
        # LOGGER.info("process_config: Exit")
        pass

    def check_params(self):
        default_user = "YourUserName"
        default_password = "YourPassword"
        default_ipaddress = "127.0.0.1"
        default_port = "80"

        if 'user' in self.polyConfig['customParams']:
            self.user = self.polyConfig['customParams']['user']
        else:
            self.user = default_user
            LOGGER.error('check_params: user not defined in customParams, please add it.  Using {}'.format(self.user))

        if 'password' in self.polyConfig['customParams']:
            self.password = self.polyConfig['customParams']['password']
        else:
            self.password = default_password
            LOGGER.error('check_params: password not defined in customParams, please add it.  '
                         'Using {}'.format(self.password))

        if 'ipaddress' in self.polyConfig['customParams']:
            self.ipaddress = self.polyConfig['customParams']['ipaddress']
        else:
            self.ipaddress = default_ipaddress
            LOGGER.error('check_params: ip address not defined in customParams, please add it.  '
                         'Using {}'.format(self.ipaddress))

        if 'port' in self.polyConfig['customParams']:
            self.port = self.polyConfig['customParams']['port']
        else:
            self.port = default_port
            LOGGER.error('check_params: port not defined in customParams, please add it.  Using {}'.format(self.port))

        # Make sure they are in the params
        self.addCustomParam({'password': self.password, 'user': self.user,
                             'ipaddress': self.ipaddress, 'port': self.port })

        # Add a notice if they need to change the user/password from the default.
        if self.user == default_user or self.password == default_password or self.ipaddress == default_ipaddress:
            self.addNotice('Please set proper user, password and IP address/port in configuration page, '
                           'and restart this nodeserver')
            return False
        else:
            return True

    def remove_notice_test(self,command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        # 'REMOVE_NOTICES_ALL': remove_notices_all,
        # 'REMOVE_NOTICE_TEST': remove_notice_test
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class SwitchNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(SwitchNode, self).__init__(controller, primary, address, name)
        self.isy = self.controller.isy

    def start(self):
        nid = str(self.address).upper()
        st = self.isy.nodes[nid].status
        if st == 255:
            st = 100
        self.setDriver('ST', str(st))
        pass

    def setOn(self, command):
        nid = str(self.address).upper()
        self.isy.nodes[nid].on()
        self.setDriver('ST', 100)

    def setOff(self, command):
        nid = str(self.address).upper()
        self.isy.nodes[nid].off()
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78}]

    id = 'SWITCH'
    commands = {
                    'DON': setOn, 'DOF': setOff
                }


class EmeterNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(EmeterNode, self).__init__(controller, primary, address, name)
        self.isy = self.controller.isy

    def start(self):
        nid = str(self.address).upper()
        st = self.isy.nodes[nid].status
        # if st == 255:
        #     st = 100
        self.setDriver('ST', str(st))
        pass

    # def setOn(self, command):
    #     nid = str(self.address).upper()
    #     self.isy.nodes[nid].on()
    #     self.setDriver('ST', 100)
    #
    # def setOff(self, command):
    #     nid = str(self.address).upper()
    #     self.isy.nodes[nid].off()
    #     self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 73},
        {'driver': 'TPW', 'value': 0, 'uom': 33},
        {'driver': 'CC', 'value': 0, 'uom': 1},
        {'driver': 'CV', 'value': 0, 'uom': 72},
    ]

    id = 'EMETER'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class TStatNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(TStatNode, self).__init__(controller, primary, address, name)
        self.isy = self.controller.isy

    def start(self):
        nid = str(self.address).upper()
        n_uom = self.isy.nodes[nid].uom
        raw_val = self.isy.nodes[nid].status
        _val = self.controller.val_prec(raw_val, nid)
        self.setDriver('ST', _val, uom=n_uom)

    def set_heat_point(self, command):
        nid = str(self.address).upper()
        val = command.get('value')
        self.isy.nodes[nid].send_cmd('CLISPH', val, uom='17')

    def set_cool_point(self, command):
        nid = str(self.address).upper()
        val = command.get('value')
        self.isy.nodes[nid].send_cmd('CLISPC', val, uom='4')

    def set_mode(self, command):
        nid = str(self.address).upper()
        val = command.get('value')
        self.isy.nodes[nid].send_cmd('CLIMD', val, uom='67')

    # def setOn(self, command):
    #     nid = str(self.address).upper()
    #     self.isy.nodes[nid].on()
    #     self.setDriver('ST', 100)
    #
    # def setOff(self, command):
    #     nid = str(self.address).upper()
    #     self.isy.nodes[nid].off()
    #     self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 17},
        {'driver': 'CLIMD', 'value': 0, 'uom': 67},
        {'driver': 'CLISPC', 'value': 0, 'uom': 4},
        {'driver': 'CLISPH', 'value': 0, 'uom': 17},
        {'driver': 'CLIHCS', 'value': 0, 'uom': 66},
    ]

    id = 'TSTAT'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                    'CLISPH': set_heat_point,
                    'CLISPC': set_cool_point,
                    'CLIMD': set_mode
                }


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('ISYNet')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)