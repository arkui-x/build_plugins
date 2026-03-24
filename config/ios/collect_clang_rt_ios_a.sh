#!/usr/bin/env bash
# Copyright (c) 2026 Huawei Device Co., Ltd.
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


set -e

# Usage:
#   collect_clang_rt_ios_a.sh <xcode_dev_dir> <out_lib_path>
# It copies the best-match clang runtime builtins library:
#   ${xcode_dev_dir}/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/<ver>/lib/darwin/libclang_rt.ios.a
# into <out_lib_path>.

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <xcode_dev_dir> <out_lib_path>" >&2
  exit 1
fi

xcode_dev_dir="$1"
out_lib="$2"

if [[ -z "$xcode_dev_dir" || -z "$out_lib" ]]; then
  echo "Missing args." >&2
  exit 1
fi

_abs() {
  local p="$1"
  if [[ "$p" != /* ]]; then
    p="$(pwd)/${p#./}"
  fi
  local d
  d="$(dirname "$p")"
  p="$(cd "$d" 2>/dev/null && pwd)/$(basename "$p")"
  echo "$p"
}

out_lib="$(_abs "$out_lib")"

if [[ ! -d "$xcode_dev_dir" ]]; then
  echo "xcode_dev_dir not found: $xcode_dev_dir" >&2
  exit 1
fi

clang_root="${xcode_dev_dir}/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang"
if [[ ! -d "$clang_root" ]]; then
  echo "clang_root not found: $clang_root" >&2
  exit 1
fi

out_dir="$(dirname "$out_lib")"
mkdir -p "$out_dir"

best=""

# Pick the highest semver-like clang directory that actually contains libclang_rt.ios.a.
# clang directories may include: "17", "17.0.0", ...
for d in "$clang_root"/*; do
  [[ -d "$d" ]] || continue
  ver="$(basename "$d")"
  candidate="${d}/lib/darwin/libclang_rt.ios.a"
  if [[ -f "$candidate" ]]; then
    if [[ -z "$best" ]]; then
      best="$ver"
    else
      # Prefer full versions (e.g. 17.0.0) over partial ones (e.g. 17).
      # Then use sort -V for semver-ish ordering.
      best_dir="$clang_root/$best"
      best_candidate="$best_dir/lib/darwin/libclang_rt.ios.a"
      if [[ "$best" == *.* && "$ver" != *.* ]]; then
        continue
      fi
      if [[ "$best" != *.* && "$ver" == *.* ]]; then
        best="$ver"
        continue
      fi
      # Both are either partial or full; compare by version string.
      best="$(
        printf "%s\n%s\n" "$best" "$ver" | sort -V | tail -n 1
      )"
    fi
  fi
done

if [[ -z "$best" ]]; then
  echo "Could not find libclang_rt.ios.a under: $clang_root" >&2
  exit 1
fi

src="${clang_root}/${best}/lib/darwin/libclang_rt.ios.a"
if [[ ! -f "$src" ]]; then
  echo "Resolved source missing: $src" >&2
  exit 1
fi

cp -f "$src" "$out_lib"
echo "Copied $src -> $out_lib" >&2

