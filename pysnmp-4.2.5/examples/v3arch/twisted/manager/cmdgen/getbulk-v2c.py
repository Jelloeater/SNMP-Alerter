#
# GETBULK Command Generator
#
# Send a series of SNMP GETBULK requests
#     with SNMPv2c, community 'public'
#     using Twisted framework for network transport
#     over IPv4/UDP
#     to an Agent at 195.218.195.228:161
#     with values non-repeaters = 0, max-repetitions = 25
#     for two OIDs in tuple form
#     stop on end-of-mib condition for both OIDs
#
# This script performs similar to the following Net-SNMP command:
#
# $ snmpbulkwalk -v2c -c public -C n0 -C r25 -ObentU 195.218.195.228 1.3.6.1.2.1.1 1.3.6.1.4.1.1
#
from twisted.internet import reactor, defer
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413.twisted import cmdgen
from pysnmp.proto import rfc1905
from pysnmp.carrier.twisted.dgram import udp

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

#
# SNMPv2c setup
#

# SecurityName <-> CommunityName mapping
config.addV1System(snmpEngine, 'my-area', 'public')

# Specify security settings per SecurityName (SNMPv1 - 0, SNMPv2c - 1)
config.addTargetParams(snmpEngine, 'my-creds', 'my-area', 'noAuthNoPriv', 1)

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
    (errorIndication, errorStatus, errorIndex, varBindTable) = cbCtx
    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex)-1][0] or '?'
            )
        )
    else:
        for varBindRow in varBindTable:
            for oid, val in varBindRow:
                print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))

        # Stop reactor when we are done walking (optional)
        for oid, val in varBindRow:
            if not val.isSameTypeWith(rfc1905.endOfMibView):
                break
        else:
            reactor.stop()
            return

        # Re-create deferred for next GETBULK iteration
        df = defer.Deferred()
        df.addCallback(cbFun)

        return df  # This also indicates that we wish to continue walking

    # Stop reactor on SNMP error (optional)
    reactor.stop()

# Prepare request to be sent yielding Twisted deferred object
df = cmdgen.BulkCommandGenerator().sendReq(
    snmpEngine,
    'my-router',
    0, 25,   # non-repeaters, max-repetitions
    ( ('1.3.6.1.2.1.1', None), ('1.3.6.1.4.1.1', None) )
)

# Register error/response receiver function at deferred
df.addCallback(cbFun)

# Run Twisted main loop
reactor.run()
