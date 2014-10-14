#
# SET Command Generator
#
# Send a SNMP SET request
#     with SNMPv1, community 'private'
#     using Twisted framework for network transport
#     over IPv4/UDP
#     to an Agent at 195.218.195.228:161
#     for OIDs in tuple form and an integer and string-typed values
#
# This script performs similar to the following Net-SNMP command:
#
# $ snmpset -v1 -c private -ObentU 195.218.195.228:161 1.3.6.1.2.1.1.9.1.3.1 s 'my value'  1.3.6.1.2.1.1.9.1.4.1 t 123 
#
from twisted.internet import reactor, defer
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413.twisted import cmdgen
from pysnmp.proto import rfc1902
from pysnmp.carrier.twisted.dgram import udp

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

#
# SNMPv1 setup
#

# SecurityName <-> CommunityName mapping
config.addV1System(snmpEngine, 'my-area', 'private')

# Specify security settings per SecurityName (SNMPv1 - 0, SNMPv2c - 1)
config.addTargetParams(snmpEngine, 'my-creds', 'my-area', 'noAuthNoPriv', 0)

#
# Setup transport endpoint and bind it with security settings yielding
# a target name
#

# UDP/IPv4
config.addTransport(
    snmpEngine,
    udp.domainName,
    udp.UdpTwistedTransport().openClientMode()
)
config.addTargetAddr(
    snmpEngine, 'my-router',
    udp.domainName, ('195.218.195.228', 161),
    'my-creds'
)

# Error/response receiver
def cbFun(cbCtx):
    (errorIndication, errorStatus, errorIndex, varBinds) = cbCtx
    if errorIndication:
        print(errorIndication)
    # SNMPv1 response may contain noSuchName error *and* SNMPv2c exception,
    # so we ignore noSuchName error here
    elif errorStatus and errorStatus != 2:
        print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1][0] or '?'
            )
        )
    else:
        for oid, val in varBinds:
            print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))

    reactor.stop()

# Prepare request to be sent yielding Twisted deferred object
df = cmdgen.SetCommandGenerator().sendReq(
    snmpEngine,
    'my-router',
    ( ((1,3,6,1,2,1,1,9,1,3,1), rfc1902.OctetString('my value')),
      ((1,3,6,1,2,1,1,9,1,4,1), rfc1902.Integer(123)) )
)

# Register error/response receiver function at deferred
df.addCallback(cbFun)

# Run Twisted main loop
reactor.run()
