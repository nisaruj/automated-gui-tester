#!/usr/bin/env python3
from tester.application import DynamicTestingApplication
from tester.app_controller import AppController
from tester.rules.rules import initialize_rules
from tester.rules.visual_state import VisualState, VisualStateGraph, ETVisualState
from collections import defaultdict
import threading
import time
import logging
import matplotlib.pyplot as plt
import logging
import argparse
import os
from tester.exceptions import DynamicTestError, PaidAppError
from dotenv import load_dotenv, find_dotenv
import sys


# def on_perform(app_controller: AppController, step):
#     logging.debug(f"Step {step}")
#     print('Fetching state')
#     current_state = VisualState(app_controller)
#     print('Fetched state')
#     states.add_transition(current_state)
#     print(states.nodes())
#     states.show()
#     time.sleep(1)


load_dotenv(find_dotenv())

parser = argparse.ArgumentParser()

parser.add_argument('device_name', metavar='device_name',
                    type=str, help='Device UDID or IP address')
parser.add_argument('app_id', metavar='app_id', type=str,
                    help='Application identifier')
parser.add_argument('proxy_host', metavar='proxy_host',
                    type=str, help='Proxy host')

parser.add_argument('--version', metavar='version', type=str,
                    help='Android version', default="7.0")
parser.add_argument('--proxy_port', metavar='proxy_port',
                    type=int, help='Proxy port', default=8080)
parser.add_argument('--system_port', metavar='system_port',
                    type=int, help='System port', default=8200)
parser.add_argument('--appium_port', metavar='appium_port',
                    type=int, help='Appium port', default=4723)

parser.add_argument('--si', metavar="skip_install", type=bool,
                    help="Skip the installation process", default=False)


if __name__ == '__main__':
    args = parser.parse_args()

    os.system('mkdir log_tester')
    logging.basicConfig(format='[%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(
                                filename=f"log_tester/{args.app_id}", mode="w"),
                            logging.StreamHandler()
                        ])

    try:
        app = DynamicTestingApplication(
            udid=args.device_name,
            version=args.version,
            proxy_host=args.proxy_host,
            system_port=args.system_port,
            proxy_port=args.proxy_port,
            appium_port=args.appium_port,
            # Linux user: plz change this line!
            mitm_path=os.environ.get("MITM_PATH"),
        )

        '''In case Appium needs proper env paths'''
        app.set_env_path(
            android_sdk_root=os.environ.get("ANDROID_SDK_ROOT"),
            java_home=os.environ.get("JAVA_HOME")
        )

        action_count = 30
        app.set_action_count(action_count)

        rules = initialize_rules()

        # states = VisualStateGraph()
        # plt.show()

        def on_perform(app_controller: AppController, step):
            for rule in rules:
                try:
                    if rule.match(app_controller):
                        print(rule.name())
                        rule.action(app_controller)
                except KeyboardInterrupt:
                    return
                except:
                    logging.error('Rule', rule.name(),
                                  'error, try to posepone...')

        app.foreach(on_perform)

        app.test(
            args.app_id,
            install_type='playstore',
        )
    except PaidAppError as exception:
        logging.error('Paid app is not supported')
        sys.exit(exception.exit_code)
        raise PaidAppError
    except:
        logging.error('Unexpected error while performing dynamic test')
        sys.exit(exception.exit_code)
        raise DynamicTestError
