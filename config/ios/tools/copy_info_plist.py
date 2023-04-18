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

import subprocess

import argparse
import sys
# import git_revision
import os

def GetClangVersion(bitcode) :
  clang_executable = str(os.path.join("..", "..", "prebuilts", "clang","ohos", "darwin-x64", "bin", "clang++"))
  if bitcode:
    clang_executable = "clang++"
  version = subprocess.check_output([clang_executable, "--version"])
  return version.splitlines()[0]

def main():

  parser = argparse.ArgumentParser(
      description='Copies the Info.plist and adds extra fields to it like the git hash of the engine')

  parser.add_argument('--source', help='Path to Info.plist source template', type=str, required=True)
  parser.add_argument('--destination', help='Path to destination Info.plist', type=str, required=True)
  parser.add_argument('--bitcode', help='Built with bitcode', action='store_true')
  parser.add_argument('--minversion', help='Minimum device OS version like "9.0"', type=str)
  parser.add_argument('--name', help='name of the framework', type=str)

  args = parser.parse_args()

  text = open(args.source).read()
  # engine_path = os.path.join(os.getcwd(), "..", "..", "flutter")
  # revision = git_revision.GetRepositoryVersion(engine_path)
  bitcode = args.bitcode is not None;
  clang_version = GetClangVersion(bitcode)
  text = text.format(framework_name = args.name, revision = "1.0.0", clang_version = clang_version, min_version = args.minversion)

  with open(args.destination, "w") as outfile:
    outfile.write(text)

if __name__ == "__main__":
  main()
