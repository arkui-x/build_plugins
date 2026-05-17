#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

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
  parser.add_argument('--xcode', action='store_true')
  parser.add_argument('--clang-version',
                      action='store_true',
                      help='Print the Xcode clang runtime directory version (e.g. 17.0.0).')
  parser.add_argument('--developer_dir',
                      help='Xcode Contents/Developer directory (used with --clang-version).')
  args = parser.parse_args()

  command =  [
    'xcodebuild',
    '-version',
    '-sdk',
    args.sdk,
    'Path'
  ]

  if args.xcode:
    command = ['xcodebuild', '-version']

  if args.clang_version:
    dev_dir = args.developer_dir
    if not dev_dir:
      dev_dir = subprocess.check_output(['xcode-select', '-p']).decode('utf-8').strip()
    clang_root = os.path.join(
        dev_dir,
        'Toolchains',
        'XcodeDefault.xctoolchain',
        'usr',
        'lib',
        'clang')
    entries = []
    try:
      entries = os.listdir(clang_root)
    except FileNotFoundError:
      raise Exception('clang root not found: %s' % clang_root)

    # Prefer full semantic versions like 17.0.0.
    def parse_semver(v):
      parts = v.split('.')
      # Normalize "17" -> (17,0,0) if needed.
      parts = (parts + ['0', '0'])[:3]
      return tuple(int(p) for p in parts)

    full = []
    partial = []
    for e in entries:
      if e.count('.') == 2 and all(x.isdigit() for x in e.split('.')):
        full.append(e)
      elif e.isdigit():
        partial.append(e)

    candidates = full if full else partial
    if not candidates:
      raise Exception('No clang versions found under %s' % clang_root)

    best = max(candidates, key=parse_semver)
    print(best)
    return 0

  sdk_output = subprocess.check_output(command).decode('utf-8').strip()

  if args.symlink:
    symlink_target = os.path.join(args.symlink, 'SDKs', os.path.basename(sdk_output))
    symlink(sdk_output, symlink_target)
    frameworks_location = os.path.join(sdk_output, '..', '..', 'Library', 'Frameworks')
    frameworks_symlink = os.path.join(args.symlink, 'Library', 'Frameworks')
    symlink(frameworks_location, frameworks_symlink)

    sdk_output = symlink_target

  if args.xcode:
    sdk_output = int(sdk_output.split()[1].split('.')[0])
    print('%d' % sdk_output)
  else:
    print(sdk_output)
  return 0

if __name__ == '__main__':
  if sys.platform != 'darwin':
    raise Exception('This script only runs on Mac') 
  sys.exit(main(sys.argv)) 
