#!/usr/bin/env python3
# coding=utf-8


import os
import sys
import argparse
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util.file_utils import read_json_file
from scripts.util.build_utils import zip_dir, temp_dir


def archive_unstripped_lib(unstripped_zip_file):
    unstripped_lib_dirs = [
        'aosp_clang_x86_64/lib.unstripped/aosp_clang_x86_64',
        'aosp_clang_arm64_release/lib.unstripped/aosp_clang_arm64_release',
        'aosp_clang_arm_release/lib.unstripped/aosp_clang_arm_release',
        'aosp_clang_arm64_debug/lib.unstripped/aosp_clang_arm64_debug',
        'aosp_clang_arm_debug/lib.unstripped/aosp_clang_arm_debug',
        'aosp_clang_arm64_profile/lib.unstripped/aosp_clang_arm64_profile',
        'aosp_clang_arm_profile/lib.unstripped/aosp_clang_arm_profile',
        'aosp_clang_arm64_release/lib.unstripped/aosp_clang_arm64_release',
        'ios_clang_arm64_sim/unstripped_dylib',
        'ios_clang_x64_sim/unstripped_dylib',
        'ios_clang_arm64_release/unstripped_dylib',
        'ios_clang_arm64_profile/unstripped_dylib',
        'ios_clang_arm64_debug/unstripped_dylib'
    ]

    # package sdk
    if os.path.exists(unstripped_zip_file):
        os.remove(unstripped_zip_file)
    with temp_dir() as tmp_dir:
        for unstripped_lib in unstripped_lib_dirs:
            if unstripped_lib.startswith('aosp'):
                cmd = ['cp', '-r', unstripped_lib, tmp_dir]
            else:
                cmd = ['rsync', '-rR', unstripped_lib, tmp_dir]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            proc.communicate()
        zip_dir(unstripped_zip_file, tmp_dir, zip_prefix_path='unstripped_lib')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-file', required=True)
    args = parser.parse_args()

    archive_unstripped_lib(args.output_file)


if __name__ == '__main__':
    sys.exit(main())
