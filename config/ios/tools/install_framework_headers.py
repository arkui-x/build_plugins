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
      description='Removes existing files and installs the specified headers' +
                  'at the given location.')

  parser.add_argument('--headers',
    nargs='+', help='The headers to install at the location.', required=True)
  parser.add_argument('--location', type=str, required=True)

  args = parser.parse_args()

  # Remove old headers.
  try:
    shutil.rmtree(os.path.normpath(args.location))
  except OSError as e:
    # Ignore only "not found" errors.
    if e.errno != errno.ENOENT:
      raise e

  # Create the directory to copy the files to.
  if not os.path.isdir(args.location):
    os.makedirs(args.location)

  # Copy all files specified in the args.
  for header_file in args.headers:
    shutil.copyfile(header_file,
      os.path.join(args.location, os.path.basename(header_file)))



if __name__ == '__main__':
  sys.exit(main())
