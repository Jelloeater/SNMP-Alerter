#
# Notification Originator
#
# Send SNMP notification using the following options:
#
# * SNMPv1
# * with community name 'public'
# * over IPv4/UDP
# * using Twisted framework for network transport
# * to a Manager at 127.0.0.1:162
# * send TRAP notification
# * with TRAP ID 'coldStart' specified as an OID
# * include managed objects information:
# * overriding Uptime value with 12345
# * overriding Agent Address with '127.0.0.1'
# * overriding Enterprise OID with 1.3.6.1.4.1.20408.4.1.1.2
# * include managed object information '1.3.6.1.2.1.1.1.0' = 'my system'
#
from twisted.internet import reactor
from pysnmp.entity import engine, config
from pysnmp.carrier.twisted.dgram import udp
from pysnmp.entity.rfc3413 import context
from pysnmp.entity.rfc3413.twisted import ntforg
from pysnmp.proto import rfc1902

# Create SNMP engine instance
snmpEngine = engine.SnmpEngine()

# SNMPv1 setup

# SecurityName <-> CommunityName mapping
config.addV1System(snmpEngine, 'my-area', 'public')

# Specify security settings per SecurityName (SNMPv1 -> 0)
config.addTargetParams(snmpEngine, 'my-creds', 'my-area', 'noAuthNoPriv', 0)

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
    snmpEngine, 'my-nms-1',
    udp.domainName, ('127.0.0.1', 162),
    'my-creds',
    tagList='all-my-managers'
)

# Specify what kind of notification should be sent (TRAP or INFORM),
# to what targets (chosen by tag) and what filter should apply to
# the set of targets (selected by tag)
config.addNotificationTarget(
    snmpEngine, 'my-notification', 'my-filter', 'all-my-managers', 'trap'
)

# Allow NOTIFY access to Agent's MIB by this SNMP model (1), securityLevel
# and SecurityName
config.addContext(snmpEngine, '')
config.addVacmUser(snmpEngine, 1, 'my-area', 'noAuthNoPriv', (), (), (1,3,6))

# Create default SNMP context where contextEngineId == SnmpEngineId
snmpContext = context.SnmpContext(snmpEngine)

# Create Notification Originator App instance. 
ntfOrg = ntforg.NotificationOriginator(snmpContext)
 
# Prepare notification to be sent yielding Twisted deferred object
ntforg.NotificationOriginator(snmpContext).sendNotification(
    snmpEngine,
    # Notification targets
    'my-notification',
    # TRAP OID: Generic Trap #6 (enterpriseSpecific) and Specific Trap 432
    '1.3.6.1.4.1.20408.4.1.1.2.0.432',
    # additional var-binds holding SNMPv1 TRAP details
    (
        # Uptime value with 12345
        (rfc1902.ObjectName('1.3.6.1.2.1.1.3.0'),
         rfc1902.TimeTicks(12345)),
        # Agent Address with '127.0.0.1'
        (rfc1902.ObjectName('1.3.6.1.6.3.18.1.3.0'),
         rfc1902.IpAddress('127.0.0.1')),
        # Enterprise OID with 1.3.6.1.4.1.20408.4.1.1.2
        (rfc1902.ObjectName('1.3.6.1.6.3.1.1.4.3.0'),
         rfc1902.ObjectName('1.3.6.1.4.1.20408.4.1.1.2')),
        # managed object '1.3.6.1.2.1.1.1.0' = 'my system'
        (rfc1902.ObjectName('1.3.6.1.2.1.1.1.0'),
         rfc1902.OctetString('my system'))
    )
)

print('Notification is scheduled to be sent')

# Schedule Twisted mainloop shutdown shortly
reactor.callWhenRunning(lambda: reactor.stop())

# Run Twisted main loop
reactor.run()
