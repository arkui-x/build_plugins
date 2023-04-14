#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import errno
import os
import subprocess
import sys 
import errno

sys.path.insert(1, '../../build_plugins/scripts')
from pyutil.file_util import symlink

# This script returns the path to the SDK of the given type. Pass the type of
# SDK you want, which is typically 'iphone' or 'iphonesimulator'.

def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument('--symlink',
                      help='Whether to create a symlink in the buildroot to the SDK.')
  parser.add_argument('--sdk',
                      choices=['iphoneos', 'iphonesimulator'],
                      help='Which SDK to find.')
  args = parser.parse_args()

  command =  [
    'xcodebuild',
    '-version',
    '-sdk',
    args.sdk,
    'Path'
  ]

  sdk_output = subprocess.check_output(command).decode('utf-8').strip()
  if args.symlink:
    symlink_target = os.path.join(args.symlink, 'SDKs', os.path.basename(sdk_output))
    symlink(sdk_output, symlink_target)
    frameworks_location = os.path.join(sdk_output, '..', '..', 'Library', 'Frameworks')
    frameworks_symlink = os.path.join(args.symlink, 'Library', 'Frameworks')
    symlink(frameworks_location, frameworks_symlink)

    sdk_output = symlink_target

  print(sdk_output)
  return 0

if __name__ == '__main__':
  if sys.platform != 'darwin':
    raise Exception('This script only runs on Mac') 
  sys.exit(main(sys.argv)) 
