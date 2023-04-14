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
import shutil
import subprocess
import sys

def main():
  parser = argparse.ArgumentParser(
      description='Creates an XCFramework consisting of the specified universal frameworks')

  parser.add_argument('--frameworks',
    nargs='+', help='The framework paths used to create the XCFramework.', required=True)
  parser.add_argument('--name', help='Name of the XCFramework', type=str, required=True)
  parser.add_argument('--location', help='Output directory', type=str, required=True)

  args = parser.parse_args()

  create_xcframework(args.location, args.name, args.frameworks)

def create_xcframework(location, name, frameworks):
  output_dir = os.path.abspath(location)
  output_xcframework = os.path.join(output_dir, '%s.xcframework' % name)

  print("output_xcframework:"+output_xcframework)
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  if os.path.exists(output_xcframework):
    # Remove old xcframework.
    shutil.rmtree(output_xcframework)

  # xcrun xcodebuild -create-xcframework -framework foo/baz.framework -framework bar/baz.framework -output output/
  command = ['xcrun',
    'xcodebuild',
    '-quiet',
    '-create-xcframework']

  for framework in frameworks:
    command.extend(['-framework', os.path.abspath(framework)])

  command.extend(['-output', output_xcframework])
  print(command)
  subprocess.check_call(command, stdout=open(os.devnull, 'w'))

if __name__ == '__main__':
  sys.exit(main())
