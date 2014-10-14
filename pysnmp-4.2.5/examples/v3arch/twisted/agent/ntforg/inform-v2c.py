#
# Notification Originator
#
# Send SNMP INFORM notification using the following options:
#
# * SNMPv2c
# * with community name 'public'
# * over IPv4/UDP
# * using Twisted framework for network transport
# * send INFORM notification
# * to a Manager at 127.0.0.1:162
# * with TRAP ID 'coldStart' specified as an OID
# * include managed objects information:
#   1.3.6.1.2.1.1.1.0 = 'Example Notificator'
#   1.3.6.1.2.1.1.5.0 = 'Notificator Example'
#
from twisted.internet import reactor
from pysnmp.entity import engine, config
from pysnmp.carrier.twisted.dgram import udp
from pysnmp.entity.rfc3413 import context
from pysnmp.entity.rfc3413.twisted import ntforg
from pysnmp.proto import rfc1902

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

# SNMPv2c setup

# SecurityName <-> CommunityName mapping
config.addV1System(snmpEngine, 'my-area', 'public')

# Specify security settings per SecurityName (SNMPv2c -> 1)
config.addTargetParams(snmpEngine, 'my-creds', 'my-area', 'noAuthNoPriv', 1)

# Transport setup

#
# Setup transport endpoint and bind it with security settings yielding
# a target name. Since Notifications could be sent to multiple Managers
# at once, more than one target entry may be configured (and tagged).
#

# UDP/IPv4
config.addTransport(
    snmpEngine,
    udp.domainName,
    udp.UdpTwistedTransport().openClientMode()
)
config.addTargetAddr(
    snmpEngine, 'my-nms',
    udp.domainName, ('127.0.0.1', 162),
    'my-creds',
    tagList='all-my-managers'
)

# Specify what kind of notification should be sent (TRAP or INFORM),
# to what targets (chosen by tag) and what filter should apply to
# the set of targets (selected by tag)
config.addNotificationTarget(
    snmpEngine, 'my-notification', 'my-filter', 'all-my-managers', 'inform'
)

# Allow NOTIFY access to Agent's MIB by this SNMP model (2), securityLevel
# and SecurityName
config.addContext(snmpEngine, '')
config.addVacmUser(snmpEngine, 2, 'my-area', 'noAuthNoPriv', (), (), (1,3,6))

# Create default SNMP context where contextEngineId == SnmpEngineId
snmpContext = context.SnmpContext(snmpEngine)

# Create Notification Originator App instance. 
ntfOrg = ntforg.NotificationOriginator(snmpContext)
 
# Error/confirmation receiver
def cbFun(cbCtx):
    (errorIndication, errorStatus, errorIndex, varBinds) = cbCtx
    print('Notification status - %s' % (
        errorIndication and errorIndication or 'delivered'
      )
    )
    # Optionally stop Twisted reactor
    reactor.stop()

# Prepare request to be sent yielding Twisted deferred object
df = ntfOrg.sendNotification(
    snmpEngine,
    # Notification targets
    'my-notification',
    # Trap OID (SNMPv2-MIB::coldStart)
    (1,3,6,1,6,3,1,1,5,1),
    # ( (oid, value), ... )
    ( ((1,3,6,1,2,1,1,1,0), rfc1902.OctetString('Example Notificator')),
      ((1,3,6,1,2,1,1,5,0), rfc1902.OctetString('Notificator Example')) )
)

# Register error/response receiver function at deferred
df.addCallback(cbFun)

print('Notification is scheduled to be sent')

# Run Twisted main loop
reactor.run()
