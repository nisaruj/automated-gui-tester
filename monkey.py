#!/usr/bin/env python3
from tester.application import DynamicTestingApplication
from tester.app_controller import AppController
import time
import logging
import argparse
import os
from tester.exceptions import DynamicTestError, PaidAppError
from dotenv import load_dotenv, find_dotenv
import sys
import re


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


if __name__ == '__main__':
    args = parser.parse_args()

    os.system('mkdir log_tester')
    logging.basicConfig(format='[%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO, 
                        handlers=[
                            logging.FileHandler(filename=f"log_tester/{args.app_id}", mode="w"),
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
            mitm_path=os.environ.get("MITM_PATH"),  # Linux user: plz change this line!
        )

        '''In case Appium needs proper env paths'''
        app.set_env_path(
            android_sdk_root=os.environ.get("ANDROID_SDK_ROOT"),
            java_home=os.environ.get("JAVA_HOME")
        )

        action_count = 20
        app.set_action_count(action_count)

        def on_perform(app_controller: AppController, step):
            try:
                app_controller.random_touch()
                app_controller.click_random_elements()
            except:
                pass

        app.foreach(on_perform)

        app.test(
            args.app_id,
            install_type='playstore',
            reset_state=True,
        )

        # Read log_appium and extract appWaitActivity
        log_pointer = open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'log_appium', args.app_id + '.log'))
        log = log_pointer.readlines()
        log_pointer.close()

        pattern = "Found package: '[a-zA-Z0-9_\.]+' and fully qualified activity name : '([a-zA-Z0-9_\.]+)'"
        activities = set()

        for line in log:
            activity = re.search(pattern, line)
            if activity is not None:
                activities.add(activity.group(1))

        # Rerun app.test
        while len(activities) > 0:
            activity = activities.pop()
            app.test(
                args.app_id,
                install_type='playstore',
                reset_state=True,
                activity=activity,
            )
    except Exception as exception:
        logging.error('Unexpected error while performing dynamic test', exception)
        sys.exit(exception.exit_code)
