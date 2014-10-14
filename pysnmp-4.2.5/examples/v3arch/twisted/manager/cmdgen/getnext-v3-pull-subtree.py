#
# GETNEXT Command Generator
#
# Send a series of SNMP GETNEXT requests
#     with SNMPv3 with user 'usr-none-none', no auth and no privacy protocols
#     over IPv4/UDP
#     using Twisted framework for network transport
#     to an Agent at 195.218.195.228:161
#     for an OID in string form
#     stop whenever received OID goes out of initial prefix (it may be a table)
#
# This script performs similar to the following Net-SNMP command:
#
# $ snmpwalk -v3 -l noAuthNoPriv -u usr-none-none -ObentU 195.218.195.228:161  1.3.6.1.2.1.1 
#
from twisted.internet import reactor, defer
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413.twisted import cmdgen
from pysnmp.proto import rfc1902, rfc1905
from pysnmp.carrier.twisted.dgram import udp

# Initial OID prefix
initialOID = rfc1902.ObjectName('1.3.6.1.2.1.1')

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

#
# SNMPv3/USM setup
#

# user: usr-none-none, no auth, no priv
config.addV3User(
    snmpEngine, 'usr-none-none',
)
config.addTargetParams(snmpEngine, 'my-creds', 'usr-none-none', 'noAuthNoPriv')

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
                errorIndex and varBinds[int(errorIndex)-1][0] or '?'
            )
        )
    else:
        for varBindRow in varBindTable:
            for oid, val in varBindRow:
                if initialOID.isPrefixOf(oid):
                    print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
                else:
                    reactor.stop()
                    return False # signal dispatcher to stop

        # Stop reactor when we are done walking (optional)
        for oid, val in varBindRow:
            if not val.isSameTypeWith(rfc1905.endOfMibView):
                break
        else:
            reactor.stop()
            return

        # Re-create deferred for next GETNEXT iteration
        df = defer.Deferred()
        df.addCallback(cbFun)
        return df  # This also indicates that we wish to continue walking

    # Stop reactor on SNMP error (optional)
    reactor.stop()

# Prepare request to be sent yielding Twisted deferred object
df = cmdgen.NextCommandGenerator().sendReq(
    snmpEngine,
    'my-router',
    ( (initialOID, None), )
)

# Register error/response receiver function at deferred
df.addCallback(cbFun)

# Run Twisted main loop
reactor.run()
