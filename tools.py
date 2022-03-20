#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tools
import subprocess
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import webbrowser
import zipfile
import plistlib
import re
import smtplib
from pbxproj import XcodeProject


class PrintColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


def success_print(text):
    print(color_text(text=text, color=PrintColors.OKGREEN))


def warn_print(text):
    print(color_text(text=text, color=PrintColors.WARNING))


def fail_print(text):
    print(color_text(text=text, color=PrintColors.FAIL))


def notice_print(text):
    print(color_text(text=text, color=PrintColors.OKCYAN))


def color_text(text: str, color: PrintColors):
    return f'{color}%s{PrintColors.ENDC}' % (text)


def to_bool(value):
    if str(value).lower() in ("yes", "YES", "Yes", "y", "true", "True", "t", "1", "Y"):
        return True
    if str(value).lower() in ("no", "n", "false", "False", "FALSE", "f", "0", "0.0", "", "none", "[]", "{}", "N"):
        return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))


def open_browser(url):
    webbrowser.open(url, new=1, autoraise=True)


def send_email(email_host, email_port, email_sender, email_psw, email_receivers, email_subject, email_content, email_attachments):
    print("")
    notice_print("------ 发送邮件 ------")

    mail_host = email_host
    #用户名
    mail_user = email_sender
    #密码(部分邮箱为授权码)
    mail_pass = email_psw
    #邮件发送方邮箱地址
    sender = email_sender
    #邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = email_receivers

    message = MIMEMultipart('related')  # 邮件类型，如果要加图片等附件，就得是这个
    #邮件主题
    message['Subject'] = email_subject
    #发送方信息
    message['From'] = sender
    #接受方信息
    message['To'] = ", ".join(receivers)
    #邮件内容设置
    txt_msg = MIMEText(email_content, 'html', 'utf-8')
    message.attach(txt_msg)
    if email_attachments is not None:
        for attachment_file_name, attachment in email_attachments.items():
            #构造附件
            att = MIMEText(attachment, 'base64', 'utf-8')
            #附件设置内容类型，方便起见，设置为二进制流
            att["Content-Type"] = 'application/octet-stream'
            #设置附件头，添加文件名
            att["Content-Disposition"] = 'attachment; filename="%s"' % attachment_file_name
            message.attach(att)

    #登录并发送邮件
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, email_port)
        #登录到服务器
        smtpObj.login(mail_user, mail_pass)
        #发送
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        #退出
        smtpObj.quit()
        success_print('send email success')
    except smtplib.SMTPException as e:
        fail_print('send email error', e)  # 打印错误


def analyze_ipa_plist(ipa_path):
    #解析App plist信息
    ipa_file = zipfile.ZipFile(ipa_path)
    plist_path = find_ipa_plist_path(ipa_file)
    plist_data = ipa_file.read(plist_path)
    plist_root = plistlib.loads(plist_data)
    return plist_root


def get_exported_ipa_info(ipa_path):
    plist_root = analyze_ipa_plist(ipa_path)
    short_version = plist_root['CFBundleShortVersionString']
    build_version = plist_root['CFBundleVersion']
    return (short_version, build_version)


def find_ipa_plist_path(zip_file):
    name_list = zip_file.namelist()
    pattern = re.compile(r'Payload/[^/]*.app/Info.plist')
    for path in name_list:
        m = pattern.match(path)
        if m is not None:
            return m.group()


def get_xcode_project_info(project_pbxproj_path, target_name):
    project = XcodeProject.load(project_pbxproj_path)
    root_object_pointer = project["rootObject"]
    objects = project["objects"]
    root_object = objects[root_object_pointer]
    target_pointers = root_object["targets"]
    for target_pointer in target_pointers:
        target_object = objects[target_pointer]
        if target_object["name"] == target_name:
            buildConfiguration_list_pointer = target_object["buildConfigurationList"]
            buildConfiguration_list_object = objects[buildConfiguration_list_pointer]
            buildConfiguration_pointers = buildConfiguration_list_object["buildConfigurations"]
            for buildConfiguration_pointer in buildConfiguration_pointers:
                build_configuration_object = objects[buildConfiguration_pointer]
                build_settings = build_configuration_object["buildSettings"]
                marketing_version = build_settings["MARKETING_VERSION"]
                current_project_version = build_settings["CURRENT_PROJECT_VERSION"]
    return (marketing_version, current_project_version)


def add_xcode_project_version(project_pbxproj_path, target_name, marketing_version, current_project_version):
    project = XcodeProject.load(project_pbxproj_path)
    project.backup()
    root_object_pointer = project["rootObject"]
    objects = project["objects"]
    root_object = objects[root_object_pointer]
    target_pointers = root_object["targets"]
    for target_pointer in target_pointers:
        target_object = objects[target_pointer]
        if target_object["name"] == target_name:
            buildConfiguration_list_pointer = target_object["buildConfigurationList"]
            buildConfiguration_list_object = objects[buildConfiguration_list_pointer]
            buildConfiguration_pointers = buildConfiguration_list_object["buildConfigurations"]
            for buildConfiguration_pointer in buildConfiguration_pointers:
                build_configuration_object = objects[buildConfiguration_pointer]
                build_settings = build_configuration_object["buildSettings"]
                build_settings["MARKETING_VERSION"] = marketing_version
                build_settings["CURRENT_PROJECT_VERSION"] = current_project_version

    project.save()


def remove_project_pbxproj_backup_file(project_pbxproj_dir):
    for root, dirs, files in os.walk(project_pbxproj_dir, topdown=False):
        for name in files:
            if name.endswith('.backup',):
                os.remove(os.path.join(root, name))


def add_build_number(project_pbxproj_path, target_name, project_pbxproj_dir):
    version = get_xcode_project_info(
        project_pbxproj_path=project_pbxproj_path, target_name=target_name)
    marketing_version = version[0]
    build = version[1]
    tools.notice_print('当前version: %s (%s)' % (marketing_version, build))
    build = int(build) + 1

    add_xcode_project_version(
        project_pbxproj_path=project_pbxproj_path,
        target_name=target_name,
        marketing_version=marketing_version,
        current_project_version=build)
    tools.notice_print('修改后version: %s (%s)' % (marketing_version, build))
    remove_project_pbxproj_backup_file(project_pbxproj_dir=project_pbxproj_dir)

    # commit_add_build_change_to_git(project_pbxproj_path=project_pbxproj_path, ipa_builded_num=build)

    return build


def commit_add_build_change_to_git(project_pbxproj_path, ipa_builded_num, github_repo_url, github_access_token):
    tools.notice_print('修改了build, 提交build commit')
    print('git status:')
    subprocess.call('git status', shell=True)
    print('git add:')
    subprocess.call('git add %s' % (project_pbxproj_path), shell=True)
    print('git commit:')
    subprocess.call("git commit %s -m 'mod: build %s'" %
                    (project_pbxproj_path, ipa_builded_num), shell=True)
    print('')
    tools.success_print("已提交commit message: 'mod: build %s'" %
                        (ipa_builded_num))
    if github_repo_url is not None and github_access_token is not None:
        temp = github_repo_url.split('//')
        comman_url = temp[0] + '//' + github_access_token + '@' + temp[1]
        push_comman = 'git push ' + comman_url
        subprocess.call(push_comman, shell=True)
        tools.success_print("git push success")


def end_program(type):
    if type == 0:
        os.system('say "automatic packaging has successfully finished"')
        exit(0)
    elif type == 1:
        fail_print('automatic packaging end with some error, check log to fix it')
        os.system('say "automatic packaging end with some error"')
        exit(1)
    else:
        exit(0)
