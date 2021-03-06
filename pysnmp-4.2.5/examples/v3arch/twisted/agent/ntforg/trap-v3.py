#
# Notification Originator
#
# Send SNMP TRAP notification using the following options:
#
# * SNMPv3
# * with user 'usr-md5-des', auth: MD5, priv DES
# * over IPv4/UDP
# * using Twisted framework for network transport
# * send TRAP notification
# * to a Manager at 127.0.0.1:162
# * with TRAP ID 'warmStart' specified as an OID
# * include managed object information 1.3.6.1.2.1.1.5.0 = 'system name'
#
from twisted.internet import reactor
from pysnmp.entity import engine, config
from pysnmp.carrier.twisted.dgram import udp
from pysnmp.entity.rfc3413 import context
from pysnmp.entity.rfc3413.twisted import ntforg
from pysnmp.proto import rfc1902

# Create SNMP engine instance with specific (and locally unique)
# SnmpEngineId -- it must also be known to the receiving party
# and configured at its VACM users table.
snmpEngine = engine.SnmpEngine(
    snmpEngineID=rfc1902.OctetString(hexValue='8000000001020304')
)

# SNMPv3/USM setup

# Add USM user
config.addV3User(
    snmpEngine, 'usr-md5-des',
    config.usmHMACMD5AuthProtocol, 'authkey1',
    config.usmDESPrivProtocol, 'privkey1'
)
config.addTargetParams(snmpEngine, 'my-creds', 'usr-md5-des', 'authPriv')

# Transport setup

# Setup transport endpoint and bind it with security settings yielding
# a target name
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
    snmpEngine, 'my-notification', 'my-filter', 'all-my-managers', 'trap'
)

# Allow NOTIFY access to Agent's MIB by this SNMP model (3), securityLevel
# and SecurityName
config.addContext(snmpEngine, '')
config.addVacmUser(snmpEngine, 3, 'usr-md5-des', 'authPriv', (), (), (1,3,6))

# Create default SNMP context where contextEngineId == SnmpEngineId
snmpContext = context.SnmpContext(snmpEngine)

# Create Notification Originator App instance. 
ntfOrg = ntforg.NotificationOriginator(snmpContext)
 
# Build and submit notification message to dispatcher
ntfOrg.sendNotification(
    snmpEngine,
    # Notification targets
    'my-notification',
    # Trap OID (SNMPv2-MIB::coldStart)
    (1,3,6,1,6,3,1,1,5,1),
    # ( (oid, value), ... )
    ( ((1,3,6,1,2,1,1,5,0), rfc1902.OctetString('system name')), )
)

print('Notification is scheduled to be sent')

# Schedule Twisted mainloop shutdown shortly
reactor.callWhenRunning(lambda: reactor.stop())

# Run Twisted main loop
reactor.run()
