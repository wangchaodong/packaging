#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum
import json
import os
import plistlib
import subprocess
import time
import tools
import requests

python_script_debug_enable = True #是否开启debug模式 用于测试脚本

pwd = os.getcwd() #当前文件的路径

ios_project_path = os.path.abspath(os.path.dirname(pwd) + os.path.sep + ".") #ios项目路径,默认为当前文件的父路径, 如果修改请填写项目绝对路径

system_home_dir = os.path.expanduser('~') # home路径
build_directory = os.path.join(pwd, 'build')    # 打包输出的文件夹

auth_key_dir_name = 'private_keys'
auth_key_copy_dir = os.path.join(pwd, auth_key_dir_name)
auth_key_destination = '~/private_keys/'
auth_key_file_name = 'AuthKey_L9U77J8554.p8'

pgy_upload_url = 'https://www.pgyer.com/apiv2/app/upload'
testflights_url = 'https://appstoreconnect.apple.com/apps'

qr_code_img_path = os.path.join(build_directory, 'qrCode.jpg')

packaging_log_path = os.path.join(pwd, 'packaging.log')

@enum.unique
class DistributionMethodType(enum.Enum):
    Development = 'development'
    AppStoreConnect = 'app-store'
    AdHoc = 'ad-hoc'
        

class Config(object):
    project_name: str
    project_scheme_list: list
    project_scheme_index: int
        
    apple_account_team_id: str
    development_provisioning_profiles: dict
    distribution_provisioning_profiles: dict
    distribution_method: DistributionMethodType

    upload_pgy_enable: bool
    pgy_api_key: str

    upload_app_sotre_enable: bool
    upload_app_store_account_type: int # 1 使用apple账号  2 使用apiKey
    apple_account_user: str
    apple_account_password: str
    apple_account_apiKey: str
    apple_account_apiIssuer: str
    
    send_email_enable: bool
    email_host: str
    email_sender_user: str
    email_sender_psw: str
    email_receivers: list
    
    add_build_number_enable: bool
    log_enable: bool
    
    app_update_message = ''

    xcodeproj_path = None
    xcworkspace_path = None
    is_workspace_project = True


def get_product_scheme():
    return Config.project_scheme_list[Config.project_scheme_index]


def get_export_options_plist_path():
    plist_path = os.path.join(
        build_directory, Config.distribution_method.value+'_ExportOptions.plist')
    return plist_path


def get_signing_certificate():
    if Config.distribution_method == DistributionMethodType.Development:
        return 'Apple Development'
    elif Config.distribution_method == DistributionMethodType.AppStoreConnect:
        return 'Apple Distribution'
    elif Config.distribution_method == DistributionMethodType.AdHoc:
        return 'Apple Distribution'

def get_provisioning_profile():
    if Config.distribution_method == DistributionMethodType.Development:
        return Config.development_provisioning_profiles
    elif Config.distribution_method == DistributionMethodType.AppStoreConnect:
        return Config.distribution_provisioning_profiles
    elif Config.distribution_method == DistributionMethodType.AdHoc:
        return Config.distribution_provisioning_profiles


def get_export_path():
    export_path = os.path.join(build_directory, Config.distribution_method.value)

    if export_path in os.listdir(build_directory):
        print("%s exists" % (export_path))
    else:
        print("create dir %s" % (export_path))
        subprocess.call('mkdir %s' % (export_path), shell=True)
        time.sleep(1)
        
    return export_path


def get_xcode_workspace_path():
    if Config.xcworkspace_path is None:
        path = search_project_file(
            ios_project_path, '%s.xcworkspace' % (Config.project_name))
        Config.xcworkspace_path = path
        return os.path.join(path)
    else:
        return os.path.join(Config.xcworkspace_path)
    

def get_xcode_project_path():
    if Config.xcodeproj_path is None:
        path = search_project_file(
            ios_project_path, '%s.xcodeproj' % (Config.project_name))
        Config.xcodeproj_path = path
        return os.path.join(path)
    else:
        return os.path.join(Config.xcodeproj_path)
    

def get_xcode_project_pbxproj_path():
    return os.path.join(get_xcode_project_path(), 'project.pbxproj')


def search_project_file(path, target):
    target_path = ''
    for root, dirs, fs in os.walk(path):
        for d in dirs:
            if d == target:
                target_path = os.path.join(root, d)
                return target_path
        for f in fs:
            if f == target:
                target_path = os.path.join(root, f)
                return target_path
    if target_path == '':
        tools.fail_print('没有找到%s文件' % (target))
    return target_path
            
def get_target_name():
    return Config.project_name #默认target name和project name一致


def get_exported_ipa_path():
    ipa_path = os.path.join(
        build_directory, '%s/%s.ipa' % (Config.distribution_method.value, Config.project_name))
    return ipa_path


def prepare_config():
    config_path = os.path.join(pwd, 'config.json')
    with open(config_path, 'r') as config_file:
        config_json_dic = json.load(config_file)
        
        Config.project_name = config_json_dic['project_name']
        Config.project_scheme_list = config_json_dic['project_scheme_list']
        Config.project_scheme_index = config_json_dic['project_scheme_index']
        
        Config.apple_account_team_id = config_json_dic['apple_account_team_id']
        Config.development_provisioning_profiles = config_json_dic['development_provisioning_profiles']
        Config.distribution_provisioning_profiles = config_json_dic['distribution_provisioning_profiles']
        Config.distribution_method = DistributionMethodType(config_json_dic['distribution_method'])
        
        Config.upload_pgy_enable = config_json_dic['upload_pgy_enable']
        Config.pgy_api_key = config_json_dic['pgy_api_key']
        
        Config.upload_app_sotre_enable = config_json_dic['upload_app_sotre_enable']
        Config.upload_app_store_account_type = config_json_dic['upload_app_store_account_type']
        Config.apple_account_user = config_json_dic['apple_account_user']
        Config.apple_account_password = config_json_dic['apple_account_password']
        Config.apple_account_apiKey = config_json_dic['apple_account_apiKey']
        Config.apple_account_apiIssuer = config_json_dic['apple_account_apiIssuer']
        
        Config.send_email_enable = config_json_dic['send_email_enable']
        Config.email_host = config_json_dic['email_host']
        Config.email_sender_user = config_json_dic['email_sender_user']
        Config.email_sender_psw = config_json_dic['email_sender_psw']
        Config.email_receivers = config_json_dic['email_receivers']
        
        Config.add_build_number_enable = config_json_dic['add_build_number_enable']
        Config.log_enable = config_json_dic['log_enable']

    if get_xcode_workspace_path() != '':
        Config.is_workspace_project = True
    else:
        Config.is_workspace_project = False
        if get_xcode_project_path() != '':
            tools.fail_print('没有找到%s.xcodeproj文件, 请将脚本文件放到项目目录下')
            
    # check project_scheme_list
    if len(Config.project_scheme_list) == 0:
        tools.warn_print("project_scheme_list未配置,正在获取project的schemes...")   
        list_project_command_run = subprocess.Popen(
            'xcodebuild -list -project %s -json' % (get_xcode_project_path()), shell=True, stdout = subprocess.PIPE, stdin = subprocess.PIPE)
        stdout, stderr = list_project_command_run.communicate()
        project_info = stdout.decode('utf-8')
        project_dict = json.loads(project_info)
        print('projec info:\n %s' % (project_dict))
        Config.project_scheme_list = project_dict['project']['schemes']
        print('project_scheme_lis:\n%s' % (Config.project_scheme_list))
        list_project_command_run.wait()
        save_packaging_config()
        
    
def save_packaging_config():
    dic = {
        "project_name": Config.project_name,
        "project_scheme_list": Config.project_scheme_list,
        "project_scheme_index": Config.project_scheme_index,
        "apple_account_team_id": Config.apple_account_team_id,
        "development_provisioning_profiles": Config.development_provisioning_profiles,
        "distribution_provisioning_profiles": Config.distribution_provisioning_profiles,
        "distribution_method": Config.distribution_method.value,
        "upload_pgy_enable": Config.upload_pgy_enable,
        "pgy_api_key": Config.pgy_api_key,
        "upload_app_sotre_enable": Config.upload_app_sotre_enable,
        "upload_app_store_account_type": Config.upload_app_store_account_type,
        "apple_account_user": Config.apple_account_user,
        "apple_account_password": Config.apple_account_password,
        "apple_account_apiKey": Config.apple_account_apiKey,
        "apple_account_apiIssuer": Config.apple_account_apiIssuer,
        "send_email_enable": Config.send_email_enable,
        "email_host": Config.email_host,
        "email_sender_user": Config.email_sender_user,
        "email_sender_psw": Config.email_sender_psw,
        "email_receivers": Config.email_receivers,
        "add_build_number_enable": Config.add_build_number_enable,
        "log_enable": Config.log_enable,
    }
    
    tools.warn_print('back up configs')
    json_str = json.dumps(dic, ensure_ascii=False, indent=4)  # 缩进4字符
    config_path = os.path.join(pwd, 'config.json')
    with open(config_path, 'w+') as config_file:
        config_file.truncate(0)
        config_file.write(json_str)
        config_file.close()

def create_export_options_plist_file():
    plist_value = {
        'method': Config.distribution_method.value,
        'destination': 'export',
        'teamID': Config.apple_account_team_id,
        'stripSwiftSymbols': True,
        'compileBitcode': True,
        'thinning': '<none>',
        'signingCertificate': get_signing_certificate(),
        'signingStyle': 'automatic',
        'provisioningProfiles': get_provisioning_profile(),
    }
    
    plist_path = get_export_options_plist_path()
    print('ExportOptions.plist:\n'+plist_path+'\n')
    print(plist_value)
    with open(plist_path, 'wb') as fp:
        plistlib.dump(plist_value, fp)
    return plist_path

def prepare_packaging_dir():
    tools.notice_print('prepare build dir: ' + build_directory)
    subprocess.call(['rm', '-rf', '%s' % (build_directory)])
    time.sleep(1)
    subprocess.call(['mkdir', '-p', '%s' % (build_directory)])
    time.sleep(1)

def prepare_app_store_upload():
    if Config.upload_app_store_account_type == 1:
        if len(Config.apple_account_user) == 0 or len(Config.apple_account_password) == 0:
            tools.warn_print(
                '上传App Store Connect需要 账号/密码 或者 apiKey/apiIssuer, upload_app_store_account_type值为 1 或者 2, 请在config.json中填写相关信息')
            tools.end_program(2)

    elif Config.upload_app_store_account_type == 2:
        if len(Config.apple_account_apiKey) == 0 or len(Config.apple_account_apiIssuer) == 0:
            tools.warn_print(
                '上传App Store Connect需要 账号/密码 或者 apiKey/apiIssuer, upload_app_store_account_type值为 1 或者 2, 请在config.json中填写相关信息')
            tools.end_program(2)
            
        prepare_authkey_dir()
    else:
        tools.warn_print(
            '上传App Store Connect需要 账号/密码 或者 apiKey/apiIssuer, upload_app_store_account_type值为 1 或者 2, 请在config.json中填写相关信息')
        tools.end_program(2)
        
def prepare_authkey_dir():
    if auth_key_file_name not in os.listdir(auth_key_copy_dir): 
        tools.warn_print(
            '使用apiKey/apiIssuer来上传App Store Connect时需要配置*.p8文件, 请先将*.p8文件复制到private_keys目录下, 具体详情可参考: https://developer.apple.com/documentation/appstoreconnectapi/creating_api_keys_for_app_store_connect_api')
        tools.end_program(2)
        
    if auth_key_dir_name in os.listdir(system_home_dir):
        print("%s exists" % (auth_key_destination))
    else:
        print("create dir: %s" % (auth_key_destination))
        subprocess.call('cd ~ && mkdir %s' %
                        (auth_key_destination), shell=True)
        time.sleep(1)

    key_dir = os.path.expanduser(auth_key_destination)

    if auth_key_file_name in os.listdir(key_dir):
        print("%s/%s file exists" % (auth_key_destination, auth_key_file_name))
    else:
        print("copy file: %s/%s" % (auth_key_destination, auth_key_file_name))
        subprocess.call('cp -r %s %s' %
                        (auth_key_copy_dir, auth_key_destination), shell=True)
        time.sleep(1)


def save_qr_code(qr_code_url):
    r = requests.get(qr_code_url)
    with open(qr_code_img_path, 'wb') as f:
        f.write(r.content)                      
    return qr_code_img_path


def save_packaging_log(start_time='', end_time='', error_message=''):
    if Config.log_enable:
        version = tools.get_xcode_project_info(
            project_pbxproj_path=get_xcode_project_pbxproj_path(), target_name=get_target_name())
        log = {
            "strat_time": start_time,
            "end_time": end_time,
            "erro_message": error_message,
            "app_name" : Config.project_name,
            "scheme" : get_product_scheme(),
            "update_message" : Config.app_update_message,
            "version": version[0]+'('+version[1]+')',
            "upload_to_pgy" : Config.upload_pgy_enable,
            "upload_to_app_store" : Config.upload_app_sotre_enable,
            "auto_add_build" : Config.add_build_number_enable,
            'signingCertificate': get_signing_certificate(),
            "distribution_method": Config.distribution_method.value,
            "ipa_path" : get_exported_ipa_path(),      
            "xcodeproj_path": get_xcode_project_path(),
            "xcworkspace_path": get_xcode_workspace_path()
        }
        json_str = json.dumps(log, ensure_ascii=False, indent=4)
        with open(packaging_log_path, "w+") as log_file:
            log_file.truncate(0)
            log_file.write(json_str)
            log_file.close()
