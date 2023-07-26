#!/usr/bin/env python3
# coding=utf-8


import os
import sys
import argparse
import shutil
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util.file_utils import read_json_file
from scripts.util.build_utils import extract_all, zip_dir


def create_xcframework(sdk_zip_file, sdk_unzip_dir, sdk_install_config):
    cmd = ['unzip', sdk_zip_file]
    proc = subprocess.Popen(cmd, cwd=sdk_unzip_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    proc.communicate()
    sdk_install_config = read_json_file(sdk_install_config)
    for sdk_install_info in sdk_install_config:
        label = sdk_install_info.get('label')
        install_dir = os.path.join(sdk_unzip_dir, sdk_install_info.get('install_dir'))
        if 'ios-arm64-simulator' in install_dir and install_dir.endswith('.framework'):
            framework_name = os.path.basename(install_dir)
            dylib_name = framework_name.replace('.framework', '')
            arm64_sim_fwk_dir = os.path.dirname(install_dir)
            framework_dir = os.path.dirname(arm64_sim_fwk_dir)
            x86_64_sim_fwk_dir = os.path.join(framework_dir, 'ios-x86_64-simulator')
            arm64_release_fwk_dir = os.path.join(framework_dir, 'ios-arm64-release')
            arm64_debug_fwk_dir = os.path.join(framework_dir, 'ios-arm64')
            arm64_profile_fwk_dir = os.path.join(framework_dir, 'ios-arm64-profile')
            arm64_x86_64_sim_fwk_dir = os.path.join(framework_dir, 'ios-arm64_x86_64-simulator')

            arm64_sim_fwk = os.path.join(arm64_sim_fwk_dir, framework_name)
            x86_64_sim_fwk = os.path.join(x86_64_sim_fwk_dir, framework_name)
            arm64_x86_64_sim_fwk = os.path.join(arm64_x86_64_sim_fwk_dir, framework_name)
            arm64_release_fwk = os.path.join(arm64_release_fwk_dir, framework_name)
            arm64_debug_fwk = os.path.join(arm64_debug_fwk_dir, framework_name)
            arm64_profile_fwk = os.path.join(arm64_profile_fwk_dir, framework_name)

            arm64_release_xcfwk = arm64_release_fwk.replace('-arm64', '').replace('framework', 'xcframework')
            arm64_debug_xcfwk = arm64_debug_fwk.replace('-arm64', '').replace('framework', 'xcframework')
            arm64_profile_xcfwk = arm64_profile_fwk.replace('-arm64', '').replace('framework', 'xcframework')

            # merge x86_64 simulator and arm64 simulator
            shutil.copytree(arm64_sim_fwk, arm64_x86_64_sim_fwk, dirs_exist_ok=True)
            proc1 = subprocess.Popen(['lipo', '-create', '{}/{}'.format(arm64_sim_fwk, dylib_name),
                             '{}/{}'.format(x86_64_sim_fwk, dylib_name), '-output',
                             '{}/{}'.format(arm64_x86_64_sim_fwk, dylib_name)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            proc1.communicate()
            if proc1.returncode:
                raise Exception('merge framework error: {}', proc1.stderr)

            # create arm64_x86_64 simulator
            if os.path.exists(arm64_release_xcfwk):
                shutil.rmtree(arm64_release_xcfwk)
            proc2 = subprocess.Popen(['xcodebuild', '-create-xcframework', '-framework', arm64_release_fwk,
                                     '-framework', arm64_x86_64_sim_fwk, '-output', arm64_release_xcfwk],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            proc2.communicate()
            if proc2.returncode:
                raise Exception('create xcframework error: {}', proc2.stderr)

            if os.path.exists(arm64_x86_64_sim_fwk):
                shutil.rmtree(arm64_x86_64_sim_fwk)

    # package sdk
    if os.path.exists(sdk_zip_file):
        os.remove(sdk_zip_file)
    zip_dir(sdk_zip_file, sdk_unzip_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file', required=True)
    parser.add_argument('--host-os', required=True)
    parser.add_argument('--sdk-out-dir', required=True)
    parser.add_argument('--arch', required=True)
    parser.add_argument('--sdk-version', required=True)
    parser.add_argument('--release-type', required=True)
    args = parser.parse_args()

    current_dir = os.getcwd()
    sdk_zip_file = os.path.join(current_dir, args.sdk_out_dir, 'darwin/arkui-x-darwin-{}-{}-{}.zip'
                               .format(args.arch, args.sdk_version, args.release_type))
    sdk_unzip_dir = 'sdk_unzip_dir'
    os.makedirs(sdk_unzip_dir, exist_ok=True)

    if args.host_os == 'mac':
        create_xcframework(sdk_zip_file, sdk_unzip_dir, args.input_file)


if __name__ == '__main__':
    sys.exit(main())
