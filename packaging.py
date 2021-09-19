#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt
import os
import subprocess
import sys
import time
import json
import configs as constant_configs
from configs import Config as packaging_config
import tools


def clean():
    print("")
    tools.notice_print("------ clean ------")
    start = time.time()
    if packaging_config.is_workspace_project:
        clean_command = 'xcodebuild clean -workspace %s -scheme %s' % (
            constant_configs.get_xcode_workspace_path(), constant_configs.get_product_scheme())
    else:
        clean_command = 'xcodebuild clean -project %s -scheme %s' % (
            constant_configs.get_xcode_project_path(), constant_configs.get_product_scheme())

    clean_command_run = subprocess.Popen(clean_command, shell=True)
    clean_command_run.wait()
    end = time.time()
    # Code码
    clean_result_code = clean_command_run.returncode
    if clean_result_code != 0:
        tools.fail_print("clean失败, 用时:%.2f秒" % (end - start))
        constant_configs.save_packaging_log(
            ipa_path='', start_time=start, end_time=end, error_message='clean失败')
        tools.end_program(1)
    else:
        tools.success_print("clean成功, 用时:%.2f秒" % (end - start))


def archive():
    print("")
    tools.notice_print("------ archive ------")

    start = time.time()
    if packaging_config.is_workspace_project:
        archive_command = 'xcodebuild -workspace %s -scheme %s -allowProvisioningUpdates -archivePath %s/%s.xcarchive archive' % (
            constant_configs.get_xcode_workspace_path(), constant_configs.get_product_scheme(), constant_configs.build_directory, constant_configs.get_product_scheme())
    else:
        archive_command = 'xcodebuild -project %s -scheme %s -allowProvisioningUpdates -archivePath %s/%s.xcarchive archive' % (
            constant_configs.get_xcode_project_path(), constant_configs.get_product_scheme(), constant_configs.build_directory, constant_configs.get_product_scheme())
        
    archive_command_run = subprocess.Popen(archive_command, shell=True)
    archive_command_run.wait()
    end = time.time()
    # return code
    archive_result_code = archive_command_run.returncode
    if archive_result_code != 0:
        tools.fail_print("archive失败, 用时:%.2f秒" % (end - start))
        constant_configs.save_packaging_log(
            start_time=start, end_time=end, error_message='archive失败')
        tools.end_program(1)
    else:
        tools.success_print("archive成功, 用时:%.2f秒" % (end - start))


def export_ipa(plistPath, export_path):
    print("")
    tools.notice_print("\n------ export %s ipa  ------" %
                       (packaging_config.distribution_method.value))

    start = time.time()

    export_command = 'xcodebuild -exportArchive -allowProvisioningUpdates -archivePath %s/%s.xcarchive -exportPath %s -exportOptionsPlist %s' % (
        constant_configs.build_directory, constant_configs.get_product_scheme(), export_path, plistPath)
    export_command_run = subprocess.Popen(export_command, shell=True)
    export_command_run.wait()
    end = time.time()
    # Code码
    export_result_code = export_command_run.returncode
    if export_result_code != 0:
        tools.fail_print("export失败, 用时:%.2f秒" % (end - start))
        constant_configs.save_packaging_log(
            start_time=start, end_time=end, error_message='export失败')
        tools.end_program(1)
    else:
        tools.success_print("export成功, 用时:%.2f秒" % (end - start))


def upload_to_pgy(ipaPath, update_message):
    print("")
    tools.notice_print("------ 上传ipa至蒲公英 ------")
    start = time.time()
    result = os.popen("curl -F 'file=@%s' -F '_api_key=%s' -F 'buildInstallType=1' -F 'buildUpdateDescription=%s'  %s" %
                      (ipaPath, packaging_config.pgy_api_key, update_message, constant_configs.pgy_upload_url), mode='r', buffering=-1).readline()
    print(result)

    info = json.loads(result)
    if info.get('code') == 0:
        qr_code_url = info.get('data').get('buildQRCodeURL')
        qr_code_img_path = constant_configs.save_qr_code(qr_code_url)
        app_pgy_download_url = 'https://www.pgyer.com/' + \
            info.get('data').get('buildShortcutUrl')
        # 打开浏览器
        tools.open_browser(app_pgy_download_url)
        
        end = time.time()
        tools.success_print("上传蒲公英成功, 用时:%.2f秒" % (end - start))
        return (True, app_pgy_download_url, qr_code_img_path)
    else:
        end = time.time()
        tools.fail_print("上传蒲公英失败, 用时:%.2f秒" % (end - start))
        return (False, info.get('code'))


def validate_ipa(ipa_path):
    start = time.time()
    tools.notice_print("------ 开始验证ipa文件 ------")
    constant_configs.prepare_app_store_upload()

    if packaging_config.upload_app_store_account_type == 1:
        validate_ipa_commond = 'xcrun altool --validate-app -f %s -t ios -u %s -p %s --output-format json --show-progress --verbose' % (
            ipa_path, packaging_config.apple_account_user, packaging_config.apple_account_password)

    elif packaging_config.upload_app_store_account_type == 2:
        validate_ipa_commond = 'xcrun altool --validate-app -t ios -f %s --apiKey %s --apiIssuer %s --output-format json --show-progress --verbose' % (
            ipa_path, packaging_config.apple_account_apiKey, packaging_config.apple_account_apiIssuer)

    validate_ipa_commond_run = subprocess.Popen(
        [validate_ipa_commond], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in iter(validate_ipa_commond_run.stdout.readline, b''):
        pre = tools.color_text('>>>', color=tools.PrintColors.OKBLUE)
        print("%s %s" % (pre, line))

        # print(validate_ipa_commond_run.communicate())
    validate_ipa_commond_run.wait()
    validate_result_code = validate_ipa_commond_run.returncode
    print(validate_result_code)
    end = time.time()
    if validate_result_code != 0:
        tools.fail_print("ipa文件验证成失败, 用时:%.2f秒" % (end - start))
        constant_configs.save_packaging_log(
            start_time=start, end_time=end, error_message='ipa文件验证成失败')
        tools.end_program(1)
    else:
        tools.success_print("ipa文件验证成功, 用时:%.2f秒" % (end - start))


def upload_ipa_to_app_store(ipa_path):
    tools.notice_print("------ 开始上传到AppStore ------")
    start = time.time()
    constant_configs.prepare_app_store_upload()
    
    if packaging_config.upload_app_store_account_type == 1:
        upload_appstore_commond = 'xcrun altool --upload-app -f %s -t ios -u %s -p %s --output-format json --show-progress --verbose' % (
            ipa_path, packaging_config.apple_account_user, packaging_config.apple_account_password)

    elif packaging_config.upload_app_store_account_type == 2:        
        upload_appstore_commond = 'xcrun altool --upload-app -t ios -f %s --apiKey %s --apiIssuer %s --output-format json --show-progress --verbose' % (
            ipa_path, packaging_config.apple_account_apiKey, packaging_config.apple_account_apiIssuer)

    upload_appstore_commond_run = subprocess.Popen(
        [upload_appstore_commond], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in iter(upload_appstore_commond_run.stdout.readline, b''):
        pre = tools.color_text('>>>', color=tools.PrintColors.OKBLUE)
        print("%s %s" % (pre, line))

    # print(validate_ipa_commond_run.communicate())
    upload_appstore_commond_run.wait()
    upload_result_code = upload_appstore_commond_run.returncode
    print(upload_result_code)
    end = time.time()
    if upload_result_code != 0:
        tools.fail_print("上传App Store Connect失败, 用时:%.2f秒" % (end - start))
        constant_configs.save_packaging_log(
            start_time=start, end_time=end, error_message='上传App Store Connect失败')
        tools.end_program(1)
    else:
        tools.success_print("上传App Store Connect成功, 用时:%.2f秒" %
                        (end - start))
        tools.open_browser(constant_configs.testflights_url)
        
        
def export():
    print('')
    tools.notice_print('------ prepare export %s ipa, scheme: %s  ------' %
                       (packaging_config.distribution_method.value, constant_configs.get_product_scheme()))

    plistPath = constant_configs.create_export_options_plist_file()
    export_path = constant_configs.get_export_path()
    
    export_ipa(plistPath=plistPath, export_path=export_path)
    ipa_path = constant_configs.get_exported_ipa_path()
    return ipa_path
    
    
def start_packaging():
    constant_configs.prepare_packaging_dir()
    
    if packaging_config.add_build_number_enable: 
        tools.add_build_number(project_pbxproj_path=constant_configs.get_xcode_project_pbxproj_path(), 
                               target_name=constant_configs.get_target_name(),
                               project_pbxproj_dir=constant_configs.get_xcode_project_path())
        
    clean()
    archive()

    ipa_path = export()
    # pgy
    if packaging_config.upload_pgy_enable:
        pgy_result = upload_to_pgy(ipaPath=ipa_path, update_message=packaging_config.app_update_message)
        
        if pgy_result[0]:
            if packaging_config.send_email_enable:
                tools.send_email(email_host=packaging_config.email_host,
                                email_sender=packaging_config.email_sender_user,
                                email_psw=packaging_config.email_sender_psw,
                                email_receivers=packaging_config.email_receivers, 
                                app_name=constant_configs.get_product_scheme(),
                                ipa_path=ipa_path,
                                download_url=pgy_result[1], 
                                update_message=packaging_config.app_update_message, 
                                qr_code_img_path=pgy_result[2])

    # app store connect
    if packaging_config.upload_app_sotre_enable:
        print('')
        tools.notice_print('------ prepare upload to app store connect ------')

        if packaging_config.distribution_method != constant_configs.DistributionMethodType.AppStoreConnect:
            packaging_config.distribution_method = constant_configs.DistributionMethodType.AppStoreConnect
            ipa_path = export()

        validate_ipa(ipa_path=ipa_path)
        if not constant_configs.python_script_debug_enable:
            upload_ipa_to_app_store(ipa_path=ipa_path)
        
    version = tools.get_exported_ipa_info(ipa_path)
    
    if packaging_config.add_build_number_enable:
        tools.commit_add_build_change_to_git(
            project_pbxproj_path=constant_configs.get_xcode_project_pbxproj_path(), ipa_builded_num=version[1])

    return ipa_path

            
def prepare():
    constant_configs.prepare_config()
    
    version = tools.get_xcode_project_info(
        project_pbxproj_path=constant_configs.get_xcode_project_pbxproj_path(), target_name=constant_configs.get_target_name())
    tools.notice_print("""
项目信息: 
xcworkspace: %s,
xcodeproj: %s,
version: %s (%s)
命令行参数:
-h <help> -s <scheme> -m <message> -ab <addBuildNumber> -pgy <pgy> -as <appstore> -dm <distributionMethod>
    """ % (constant_configs.get_xcode_workspace_path(), constant_configs.get_xcode_project_path(), version[0], version[1]))
    try:
        opts, args = getopt.getopt(sys.argv[1:], '-h:-s:-m:-ab:-pgy:-as:-dm:', [
                                   'help', 'scheme=', 'message=', 'addBuildNumber=', 'pgy=', 'appstore=','distributionMethod='])
    except getopt.GetoptError:
        tools.fail_print("参数错误")
        print('''
packaging.py -h <help> -s <scheme> -m <message> -ab <addBuildNumber> -pgy <pgy> -as <appstore> -dm <distributionMethod>
-h      help
-s      scheme: xcode project schemes
-m      message: app update message.
-ab     addBuildNumber: a boolean value, weather auto increase build number or not. yes will +1, no do nothing.
-pgy    pgy: a boolean value, weather upload ipa to pgy or not. 
-as    appstore: a boolean value, weather upload ipa to appstore or not.
-dm     distributionMethod: development, app-store, ad-hoc, default is development for upload pgy, app-store for upload App Store Connect.
        ''')
        tools.end_program(2)

    scheme = ''
    message = ''
    add_build_number = ''
    pgy = ''
    appstore = ''
    distribution_method = ''
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print('''
packaging.py -h <help> -s <scheme> -m <message> -ab <addBuildNumber> -pgy <pgy> -as <appstore> -dm <distributionMethod>
-h      help
-s      scheme: xcode project schemes
-m      message: app update message.
-ab     addBuildNumber: a boolean value, weather auto increase build number or not. yes will +1, no do nothing.
-pgy    pgy: a boolean value, weather upload ipa to pgy or not. 
-as    appstore: a boolean value, weather upload ipa to appstore or not.
-dm     distributionMethod: development, app-store, ad-hoc, default is development for upload pgy, app-store for upload App Store Connect.
            ''')
            tools.end_program(2)

        if opt_name in ('-s', '--scheme'):
            scheme = opt_value
            print(scheme)
            for index, value in enumerate(packaging_config.project_scheme_list):
                if value == scheme:
                    packaging_config.project_scheme_index = index
                    
        if opt_name in ('-m', '--message'):
            message = opt_value
            print(message)

            packaging_config.app_update_message = message

        if opt_name in ('-ab', '--addBuildNumber'):
            add_build_number = opt_value
            print(add_build_number)
            packaging_config.add_build_number_enable = tools.to_bool(
                add_build_number)

        if opt_name in ('-pgy', '--pgy'):
            pgy = opt_value
            print(pgy)
            packaging_config.upload_pgy_enable = tools.to_bool(pgy)

        if opt_name in ('-as', '--appstore'):
            appstore = opt_value
            print(appstore)
            packaging_config.upload_app_sotre_enable = tools.to_bool(appstore)

        if opt_name in ('-dm', '--distributionMethod'):
            distribution_method = opt_value
            print(distribution_method)
            packaging_config.distribution_method = constant_configs.DistributionMethodType(
                distribution_method)

    # 命令行未添加scheme参数
    if not str(scheme).strip():
        scheme = ''
        for index, value in enumerate(packaging_config.project_scheme_list):
            scheme += ' '+str(index+1)+'.'+value+'\n'
       
        scheme = input(tools.color_text(
            "*请选择要打包的scheme:\n%s" % (scheme), tools.PrintColors.HEADER))
        if scheme == '':
            tools.notice_print(
                '输入回车则表示使用config.json中project_scheme_index: %s' % packaging_config.project_scheme_index)
        elif not scheme.isdigit():
            tools.fail_print("Invalid input, please select the index of scheme")
            tools.end_program(2)
        else:
            scheme = int(scheme)
            if scheme < 1 or scheme > len(packaging_config.project_scheme_list):
                tools.fail_print(
                    "Invalid input, please select the index of scheme")
                tools.end_program(2)
        
            packaging_config.project_scheme_index = scheme-1
        
    # 命令行未添加message参数
    if not message.strip():
        # 更新内容
        print(tools.color_text("*请输入更新内容:", tools.PrintColors.HEADER))
        '''使用input()函数读取多行输入，不抹掉回车换行符'''
        stopword = ''  # 输入停止符
        message = ''
        for line in iter(input, stopword):  # 输入为空行，表示输入结束
          message += line + '\n'

        if not message.strip():
            message = packaging_config.project_name + ' update'
            
        packaging_config.app_update_message = message

    # 命令行未添加pgy参数
    if not pgy.strip():
        pgy = input(tools.color_text(
            "*是否上传到蒲公英? (Y/N):", tools.PrintColors.HEADER))
        if pgy == '':
            tools.notice_print(
                '输入回车则表示使用config.json中upload_pgy_enable: %s' % packaging_config.upload_pgy_enable)
        else:
            pgy = tools.to_bool(pgy)
            packaging_config.upload_pgy_enable = pgy

    # 命令行未添加appstore参数
    if not appstore.strip():
        appstore = input(tools.color_text(
            "*是否上传到App Store Connect? (Y/N):", tools.PrintColors.HEADER))
        if appstore == '':
            tools.notice_print(
                '输入回车则表示使用config.json中upload_app_sotre_enable: %s' % packaging_config.upload_app_sotre_enable)
        else:
            appstore = tools.to_bool(appstore)
            packaging_config.upload_app_sotre_enable = appstore
        
    # 命令行未添加addBuildNumber参数
    if not add_build_number.strip():
        add_build_number = input(tools.color_text(
            "*是否要增加build号?(Y/N):", tools.PrintColors.HEADER))
        if add_build_number == '':
            tools.notice_print(
                '输入回车则表示使用config.json中add_build_number_enable: %s' % packaging_config.add_build_number_enable)
        else:
            packaging_config.add_build_number_enable = tools.to_bool(
            add_build_number)

    if len(distribution_method) == 0:
        if packaging_config.upload_pgy_enable:
            packaging_config.distribution_method = constant_configs.DistributionMethodType.Development
        elif packaging_config.upload_app_sotre_enable:
            packaging_config.distribution_method = constant_configs.DistributionMethodType.AppStoreConnect
        
if __name__ == '__main__':
    
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    prepare()
    ipa_path = start_packaging()
    if constant_configs.python_script_debug_enable:
        constant_configs.save_packaging_config()
        
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    constant_configs.save_packaging_log(start_time=start_time,end_time=end_time)
    tools.end_program(0)

