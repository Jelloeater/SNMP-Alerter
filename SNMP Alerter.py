# !/usr/bin/env python2.7
"""A python project for monitoring network resources
"""
import json
import os
import sys

import logging
import argparse
from time import sleep
import email_controller

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "1.5"
__email__ = "jelloeater@gmail.com"

LOG_FILENAME = "SNMP_monitor.log"

import logging
import os

#CHANGE SETTINGS HERE
class settingsVars:
    # IP 10.0.21.10:161
    # SNMP2c
    # Read: admin
    # the MIB/OID to read out the number of AP is (Normally 27)
    # 1.3.6.1.4.1.9.9.618.1.8.4.0
    # And the number of clients is
    # 1.3.6.1.4.1.9.9.618.1.8.12.0

    servers_to_monitor = ['10.0.21.10']
    OIDs_to_monitor = [['1.3.6.1.4.1.9.9.618.1.8.4.0',27],['1.3.6.1.4.1.9.9.618.1.8.12.0',400]]
    community = 'admin'
    port = 161
    send_email_to = 'jschoepfer@connectedtechnology.com'

class events:
    last_sent_email = ''
    last_failure = ''

    @staticmethod
    def last_email_sent():
        #TODO Needs to compute when the last e-mail was sent
        return 1

    @staticmethod
    def last_failure():
        #TODO Needs to return the last time a service has failed, might be tricky
        return 2

def main():
    """ Take arguments and direct program """
    parser = argparse.ArgumentParser(description="A Network Stats Database Report Generator"
                                                 " (http://github.com/Jelloeater/NetworkMonitor)",
                                     epilog="Please specify action")

    multi_server_group = parser.add_argument_group('Multi Server Mode')
    multi_server_group.add_argument("-m",
                                    "--monitor",
                                    help="Multi server watch mode",
                                    action="store_true")

    parser.add_argument("-d",
                        "--delay",
                        action="store",
                        type=int,
                        default=600,
                        help="Wait x second between checks (10 min)")

    parser.add_argument("-a",
                        "--alert_timeout",
                        action="store",
                        type=int,
                        default=60,
                        help="Wait x minutes between alerts (1 hr)")

    parser.add_argument("-t",
                        "--host_timeout",
                        action="store",
                        type=int,
                        default=10,
                        help="Wait x seconds for failure (10)")

    parser.add_argument("--debug",
                        action="store_true",
                        help="Debug Mode Logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.DEBUG)
        logging.debug(sys.path)
        logging.debug(args)
        logging.debug('Debug Mode Enabled')
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.WARNING)

    mode = modes(sleep_delay=args.delay, alert_timeout=args.alert_timeout, host_timeout=args.host_timeout)
    # Create new mode object for flow, I'll buy that :)

    if len(sys.argv) == 1:  # Displays help and lists servers (to help first time users)
        parser.print_help()
        sys.exit(1)

    if args.monitor:
        mode.monitor_servers()


class modes(object):  # Uses new style classes
    def __init__(self, sleep_delay, alert_timeout, host_timeout):
        self.sleep_delay = sleep_delay
        self.alert_timeout = alert_timeout
        self.host_timeout = host_timeout
        # Load last


    def sleep(self):
        try:
            sleep(self.sleep_delay)
        except KeyboardInterrupt:
            print("Bye Bye.")
            sys.exit(0)

    def monitor_servers(self):
        print("Monitor servers")
        print("Press Ctrl-C to quit")

        while True:
            self.server_list = settingsVars.servers_to_monitor
            # Gets server list on each refresh, in-case of updates
            logging.debug(self.server_list)
            # Send each row of monitor_list to logic gate
            for i in self.server_list:
                pass
                #TODO Need to check if OID value is okay

                # server_logger(i, sleep_delay=self.sleep_delay, alert_timeout=self.alert_timeout,
                #               host_timeout=self.host_timeout).check_server_status()

            last_email = events.last_email_sent()
            last_fail = events.last_failure()
            logging.debug(
                'Last e-mail sent: ' + str(last_email) + '  Timeout: ' + str(self.alert_timeout) +
                '  Last Failure: ' + str(last_fail))

            if events.last_email_sent() > self.alert_timeout > events.last_failure():
                # Are we spamming alerts?
                # Check if any servers have gone down in the the last X minutes
                # If any have gone down, send report
                if email_controller.test_login():
                    logging.info('SENDING REPORT')
                    email_controller.generate_report()
            else:
                logging.info('E-mail timeout still cooling off')

            self.sleep()


if __name__ == "__main__":
    main()

