import sys
import os

sys.path.append(os.getcwd() + '/pysnmp-4.2.5')
sys.path.append(os.getcwd() + '/pyasn1-0.1.7')

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time


def get_v2_oid():

    # Protocol version to use
    # pMod = api.protoModules[api.protoVersion1]
    pMod = api.protoModules[api.protoVersion2c]
    # Build PDU
    reqPDU = pMod.GetRequestPDU()
    pMod.apiPDU.setDefaults(reqPDU)
    pMod.apiPDU.setVarBinds(
        reqPDU, (('1.3.6.1.2.1.1.1.0', pMod.Null('')),)
    )
    # Build message
    reqMsg = pMod.Message()
    pMod.apiMessage.setDefaults(reqMsg)
    pMod.apiMessage.setCommunity(reqMsg, 'public')
    pMod.apiMessage.setPDU(reqMsg, reqPDU)
    startedAt = time()

    def cbRecvFun(transport_dispatcher, transportDomain, transportAddress,
                  wholeMsg, reqPDU=reqPDU):
        while wholeMsg:
            rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
            rspPDU = pMod.apiMessage.getPDU(rspMsg)
            # Match response to request
            if pMod.apiPDU.getRequestID(reqPDU) == pMod.apiPDU.getRequestID(rspPDU):
                # Check for SNMP errors reported
                errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                if errorStatus:
                    print(errorStatus.prettyPrint())
                else:
                    OID_Values = []
                    for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                        OID_Values.append([oid,val])
                        print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
                transport_dispatcher.jobFinished(1)

        return wholeMsg

    transportDispatcher = AsynsockDispatcher()
    transportDispatcher.registerRecvCbFun(cbRecvFun)
    # UDP/IPv4
    transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openClientMode()
    )
    # Pass message to dispatcher
    transportDispatcher.sendMessage(
        encoder.encode(reqMsg), udp.domainName, ('192.168.1.1', 161)
    )
    transportDispatcher.jobStarted(1)
    # Dispatcher will finish as job#1 counter reaches zero
    transportDispatcher.runDispatcher()
    transportDispatcher.closeDispatcher()
    print("EOP")

get_v2_oid()
