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
"""
Import the polyglot interface module. This is in pypy so you can just install it
normally. Replace pip with pip3 if you are using python3.

Virtualenv:
pip install polyinterface

Not Virutalenv:
pip install polyinterface --user

*I recommend you ALWAYS develop your NodeServers in virtualenv to maintain
cleanliness, however that isn't required. I do not condone installing pip
modules globally. Use the --user flag, not sudo.
"""

LOGGER = polyinterface.LOGGER
"""
polyinterface has a LOGGER that is created by default and logs to:
logs/debug.log
You can use LOGGER.info, LOGGER.warning, LOGGER.debug, LOGGER.error levels as needed.
"""

class Controller(polyinterface.Controller):
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.

    Class Variables:
    self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
    self.name: String name of the node
    self.address: String Address of Node, must be less than 14 characters (ISY limitation)
    self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
    self.added: Boolean Confirmed added to ISY as primary node
    self.config: Dictionary, this node's Config

    Class Methods (not including the Node methods):
    start(): Once the NodeServer config is received from Polyglot this method is automatically called.
    addNode(polyinterface.Node, update = False): Adds Node to self.nodes and polyglot/ISY. This is called
        for you on the controller itself. Update = True overwrites the existing Node data.
    updateNode(polyinterface.Node): Overwrites the existing node data here and on Polyglot.
    delNode(address): Deletes a Node from the self.nodes/polyglot and ISY. Address is the Node's Address
    longPoll(): Runs every longPoll seconds (set initially in the server.json or default 10 seconds)
    shortPoll(): Runs every shortPoll seconds (set initially in the server.json or default 30 seconds)
    query(): Queries and reports ALL drivers for ALL nodes to the ISY.
    getDriver('ST'): gets the current value from Polyglot for driver 'ST' returns a STRING, cast as needed
    runForever(): Easy way to run forever without maxing your CPU or doing some silly 'time.sleep' nonsense
                  this joins the underlying queue query thread and just waits for it to terminate
                  which never happens.
    """
    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(Controller, self).__init__(polyglot)
        self.name = 'Template Controller'
        self.poly.onConfig(self.process_config)
        self.isy = None

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a discovery method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        LOGGER.info('Started Template NodeServer')
        self.removeNoticesAll()
        # self.addNotice({'hello': 'Hello Friends!'})
        self.check_params()

        self.isy = PyISY.ISY('192.168.1.69', '80', 'admin', 'admin')

        if self.isy.connected:
            LOGGER.info('ISY Connected: True')
            self.isy.auto_update = True
            self.discover()
        else:
            LOGGER.info('ISY Connected: False')
        # self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def shortPoll(self):
        """
        Optional.
        This runs every 10 seconds. You would probably update your nodes either here
        or longPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def longPoll(self):
        """
        Optional.
        This runs every 30 seconds. You would probably update your nodes either here
        or shortPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def query(self):
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Example
        Do discovery here. Does not have to be called discovery. Called from example
        controller start method and from DISCOVER command recieved from ISY as an exmaple.
        """
        self.addNode(TemplateNode(self, self.address, 'templateaddr', 'Template Node Name'))

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
        poly_node = str(nid).lower()
        r_node = self.isy.nodes[nid]
        r_uom = r_node.uom
        r_prec = int(r_node.prec)
        raw_val = str(val)
        split_val = self.val_split(raw_val)

        print('Precision: ' + str(r_prec))
        if r_prec == 1:
            _int = split_val[0:-r_prec]
            _sep = ''
            _v = _sep.join(_int)
            _d = '0'
            if _v is '':
                _v = '0'
            _val = '{0}.{1}'.format(_v, _d)
        elif r_prec > 1:
            _int = split_val[0:-r_prec]
            _dec = split_val[-r_prec:]
            _sep = ''
            _v = _sep.join(_int)
            _d = _sep.join(_dec)
            if _v is '':
                _v = '0'
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
        r_prec = int(r_node.prec)
        raw_val = str(e.handles)



        # if r_prec > 1:
        #     _val = self.val_prec(raw_val, nid)
        #     self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)

        # if r_uom == '73':
        #     split_val = self.val_split(raw_val)
        #     _int = split_val[0:-r_prec]
        #     _dec = split_val[-r_prec:]
        #     _sep = ''
        #     _v = _sep.join(_int)
        #     _d = _sep.join(_dec)
        #     _val = '{0}.{1}'.format(_v, _d)
        #     self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)

        if r_uom == '78':
            if raw_val == '255':
                _val = '100'
            else:
                _val = raw_val
            self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)
        elif int(raw_val) > 1:
            _val = self.val_prec(raw_val, nid)
        else:
            _val = '0'
        self.nodes[poly_node].setDriver('ST', _val, uom=r_uom)

    def on_control(self, event, nid):
        # print(self, event)
        # print(help(event))
        # print(nid, event.nval, event.uom, event.prec, event.event)
        print(nid, event, event.nval, event.uom, event.prec)

        poly_node = str(nid).lower()
        # r_node = self.isy.nodes[nid]
        r_uom = event.uom
        r_prec = int(event.prec)
        raw_val = str(event.nval)
        r_event = event.event

        # if r_prec > 1:
        #     _val = self.val_prec(raw_val, nid)
        #     # split_val = self.val_split(raw_val)
        #     # _int = split_val[0:-r_prec]
        #     # _dec = split_val[-r_prec:]
        #     # _sep = ''
        #     # _v = _sep.join(_int)
        #     # _d = _sep.join(_dec)
        #     # _val = '{0}.{1}'.format(_v, _d)
        # else:
        #     _val = raw_val

        if int(raw_val) > 1:
            _val = self.val_prec(raw_val, nid)
        else:
            _val = '0'

        if r_event == 'TPW':
            self.nodes[poly_node].setDriver('TPW', _val, uom=r_uom)
        if r_event == 'CC':
            self.nodes[poly_node].setDriver('CC', _val, uom=r_uom)
        if r_event == 'CV':
            self.nodes[poly_node].setDriver('CV', _val, uom=r_uom)
        if r_event == 'CLIMD':
            self.nodes[poly_node].setDriver('CLIMD', _val, uom=r_uom)
        if r_event == 'CLISPC':
            self.nodes[poly_node].setDriver('CLISPC', _val, uom=r_uom)
        if r_event == 'CLISPH':
            self.nodes[poly_node].setDriver('CLISPH', _val, uom=r_uom)

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
        """
        This is an example if using custom Params for user and password and an example with a Dictionary
        """
        # self.addNotice('Hello Friends! (with key)','hello')
        # self.addNotice('Hello Friends! (without key)')
        default_user = "YourUserName"
        default_password = "YourPassword"
        if 'user' in self.polyConfig['customParams']:
            self.user = self.polyConfig['customParams']['user']
        else:
            self.user = default_user
            LOGGER.error('check_params: user not defined in customParams, please add it.  Using {}'.format(self.user))
            st = False

        if 'password' in self.polyConfig['customParams']:
            self.password = self.polyConfig['customParams']['password']
        else:
            self.password = default_password
            LOGGER.error('check_params: password not defined in customParams, please add it.  Using {}'.format(self.password))
            st = False

        # Make sure they are in the params
        self.addCustomParam({'password': self.password, 'user': self.user, 'some_example': '{ "type": "TheType", "host": "host_or_IP", "port": "port_number" }'})

        # Add a notice if they need to change the user/password from the default.
        if self.user == default_user or self.password == default_password:
            # This doesn't pass a key to test the old way.
            self.addNotice('Please set proper user and password in configuration page, and restart this nodeserver')
        # This one passes a key to test the new way.
        self.addNotice('This is a test','test')

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

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.
    The id must match the nodeDef id="controller"
    In the nodedefs.xml
    """
    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all,
        'REMOVE_NOTICE_TEST': remove_notice_test
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
        {'driver': 'ST', 'value': 0, 'uom': 17},
        {'driver': 'CLIMD', 'value': 0, 'uom': 67},
        {'driver': 'CLISPC', 'value': 0, 'uom': 4},
        {'driver': 'CLISPH', 'value': 0, 'uom': 17},
        {'driver': 'CLIHCS', 'value': 0, 'uom': 66},
    ]

    id = 'TSTAT'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class TemplateNode(polyinterface.Node):
    """
    This is the class that all the Nodes will be represented by. You will add this to
    Polyglot/ISY with the controller.addNode method.

    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY

    Class Methods:
    start(): This method is called once polyglot confirms the node is added to ISY.
    setDriver('ST', 1, report = True, force = False):
        This sets the driver 'ST' to 1. If report is False we do not report it to
        Polyglot/ISY. If force is True, we send a report even if the value hasn't changed.
    reportDrivers(): Forces a full update of all drivers to Polyglot/ISY.
    query(): Called when ISY sends a query request to Polyglot for this specific node
    """
    def __init__(self, controller, primary, address, name):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        """
        super(TemplateNode, self).__init__(controller, primary, address, name)

    def start(self):
        """
        Optional.
        This method is run once the Node is successfully added to the ISY
        and we get a return result from Polyglot. Only happens once.
        """
        self.setDriver('ST', 1)
        pass

    def setOn(self, command):
        """
        Example command received from ISY.
        Set DON on TemplateNode.
        Sets the ST (status) driver to 1 or 'True'
        """
        self.setDriver('ST', 1)

    def setOff(self, command):
        """
        Example command received from ISY.
        Set DOF on TemplateNode
        Sets the ST (status) driver to 0 or 'False'
        """
        self.setDriver('ST', 0)

    def query(self):
        """
        Called by ISY to report all drivers for this node. This is done in
        the parent class, so you don't need to override this method unless
        there is a need.
        """
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'templatenodeid'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                    'DON': setOn, 'DOF': setOff
                }
    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('Template')
        """
        Instantiates the Interface to Polyglot.
        The name doesn't really matter unless you are starting it from the
        command line then you need a line Template=N
        where N is the slot number.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
