def get_oid(server='demo.snmplabs.com', OID='1.3.6.1.2.1.1.5.0', community='public', port = 161):

    from pysnmp.entity.rfc3413.oneliner import cmdgen

    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((server, port)),
        cmdgen.MibVariable(OID)
    )

    # Check for errors and print out results
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
            )
            )
        else:
            for name, val in varBinds:
                return val.prettyPrint()