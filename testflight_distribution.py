#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#doc https://developer.apple.com/documentation/appstoreconnectapi
# https://github.com/Ponytech/appstoreconnectapi

import os
import platform
import requests
import time
import json
from authlib.jose import jwt
import smtplib
from email.mime.text import MIMEText
import tools
import configs as constant_configs
from configs import Config as packaging_config

constant_configs.prepare_config()

ISSUER_ID = packaging_config.apple_account_apiIssuer
KEY_ID = packaging_config.apple_account_apiKey

# 20 minutes timestamp
EXPIRATION_TIME = int(round(time.time() + (20.0 * 60.0)))

PRIVATE_KEY = open(os.path.join(constant_configs.auth_key_dir_name,
                   packaging_config.auth_key_file_name), 'rb').read()

is_run_in_local = True
log_enable = True
log_dir = 'log/'
external_testing_name = "iKuddle-Preview"

header = {
    "alg": "ES256",
    "kid": KEY_ID,
    "typ": "JWT"
}

payload = {
    "iss": ISSUER_ID,
    "exp": EXPIRATION_TIME,
    "aud": "appstoreconnect-v1"
}

# prepare jwt token
token = jwt.encode(header, payload, PRIVATE_KEY)
JWT = 'Bearer ' + token.decode()
HEAD = {'Authorization': JWT, 'Content-Type': 'application/json'}
PARAMS = {'limit': 200}

api_list_beta_groups = 'https://api.appstoreconnect.apple.com/v1/betaGroups'
api_list_build = 'https://api.appstoreconnect.apple.com/v1/builds'


def get_testflight_latest_builds():
    print('get_testflight_latest_builds')
    r = requests.get(api_list_build, params=PARAMS, headers=HEAD)
    print(r.json())
    results = json.loads(r.text)
    if log_enable:
        file_path = os.path.join(log_dir, 'api_list_build.json')
        with open(file_path, 'w') as json_file:
            json_file.write(json.dumps(r.json(), indent=4))
            json_file.close()
    if r.status_code != 200:
        print('get_testflight_latest_builds error: ' +
              results['errors']['status']+' '+results['errors']['code']+' '+results['errors'][0]['detail'])
        exit(1)
    if results['data'] == []:
        print('no builds in testflight')
        exit(1)

    latest_builds = results['data'][0]

    if latest_builds['attributes']['processingState'] == 'VALID':
        print('latest build processingState: VALID')
        latest_build_id = latest_builds['id']
        version = latest_builds['attributes']['version']
        print('latest build id: '+latest_build_id)
        beta_group_id, had_added_build = get_testflight_beta_group(
            latest_build_id)
        if had_added_build:
            print('latest build had added to beta group')
            submit_app_for_beta_review(latest_build_id)
        else:
            add_builds_to_external_group(
                latest_build_id, beta_group_id, version)
    else:
        if is_run_in_local:
            print('latest build processingState: INVALID, wait 30 seconds to retry')
            time.sleep(30)
            get_testflight_latest_builds()
        else:
            print('latest build processingState: INVALID')
            exit(1)


def get_testflight_beta_group(latest_build_id):
    print('get_testflight_beta_group')
    r = requests.get(api_list_beta_groups, params=PARAMS, headers=HEAD)
    print(r.json())
    if log_enable:
        file_path = os.path.join(log_dir, 'api_list_beta_groups.json')
        with open(file_path, 'w') as json_file:
            json_file.write(json.dumps(r.json(), indent=4))
            json_file.close()

    results = json.loads(r.text)
    if r.status_code != 200:
        print('get_testflight_beta_group error: ' +
              results['errors']['status']+' '+results['errors']['code']+' '+results['errors'][0]['detail'])
        exit(1)

    for group in results['data']:
        if group['attributes']['name'] == external_testing_name:
            print('group_id:'+group['id'])
            beta_group_id = group['id']
            builds_related_url = group['relationships']['builds']['links']['related']
            had_added_build = get_beta_group_related_builds(
                builds_related_url, latest_build_id)
            return beta_group_id, had_added_build


def get_beta_group_related_builds(builds_related_url, latest_build_id):
    print('get_beta_group_related_builds')
    r = requests.get(builds_related_url, params=PARAMS, headers=HEAD)
    print(r.json())
    results = json.loads(r.text)
    if r.status_code != 200:
        print('get_beta_group_related_builds error: ' +
              results['errors']['status']+' '+results['errors']['code']+' '+results['errors'][0]['detail'])
        exit(1)

    had_added_build = False
    for builds in results['data']:
        if builds['id'] == latest_build_id:
            had_added_build = True

    if log_enable:
        file_path = os.path.join(log_dir, 'beta_groups_related_builds.json')
        with open(file_path, 'w') as json_file:
            json_file.write(json.dumps(r.json(), indent=4))
            json_file.close()

    return had_added_build


def add_builds_to_external_group(build_id, group_id, version):
    print('add_builds_to_external_group')
    url = 'https://api.appstoreconnect.apple.com/v1/betaGroups/%s/relationships/builds' % group_id

    post_data = {'data': [{'id': build_id, 'type': 'builds'}]}
    r = requests.post(url, data=json.dumps(post_data), headers=HEAD)
    print(r.status_code)

    if r.status_code == 204:
        print('add_builds_to_external_group: success')
        submit_app_for_beta_review(build_id=build_id)
        # send email notification
        email_subject = 'iKuddle-iOS Builds %s Distributed Successfully' % (
            version)
        message = 'Testflight new build version: '+version + \
            ' has been added to external testing group.'
        email_content = """
    <head>
    iKuddle iOS TestFlight Builds Distributed Successfully!
    </head>
    <p>
    message: %s <br>
    
    platform: %s <br>
    system user: %s <br>
    </p>
    """ % (message, platform.platform(), platform.node())

        tools.send_email(email_host=packaging_config.email_host,
                         email_port=packaging_config.email_port,
                         email_sender=packaging_config.email_sender_user,
                         email_psw=packaging_config.email_sender_psw,
                         email_receivers=packaging_config.email_receivers,
                         email_subject=email_subject,
                         email_content=email_content)

    else:
        print('add_builds_to_external_group: failed')
        # only got response's error message
        if log_enable:
            file_path = os.path.join(
                log_dir, 'add_builds_to_external_group.json')
            with open(file_path, 'w') as json_file:
                json_file.write(json.dumps(r.json(), indent=4))
                json_file.close()


def submit_app_for_beta_review(build_id):
    print('submit_app_for_beta_review')
    url = 'https://api.appstoreconnect.apple.com/v1/betaAppReviewSubmissions'
    post_data = {
        'data': {
            'relationships':
                {
                    'build':
                    {
                        'data':
                        {
                            'type': 'builds',
                            'id': build_id
                        }
                    }
                },
            'type': 'betaAppReviewSubmissions'
        }
    }
    r = requests.post(url, data=json.dumps(post_data), headers=HEAD)
    print(r.json())


if __name__ == '__main__':
    get_testflight_latest_builds()
