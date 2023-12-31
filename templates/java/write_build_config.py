#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Writes a build_config file.

The build_config file for a target is a json file containing information about
how to build that target based on the target's dependencies. This includes
things like: the javac classpath, the list of AOSP resources dependencies,
etc. It also includes the information needed to create the build_config for
other targets that depend on that one.

AOSP build scripts should not refer to the build_config directly, and the
build specification should instead pass information in using the special
file-arg syntax (see build_utils.py:expand_file_args). That syntax allows passing
of values in a json dict in a file and looks like this:
  --python-arg=@FileArg(build_config_path:javac:classpath)

Note: If paths to input files are passed in this way, it is important that:
  1. inputs/deps of the action ensure that the files are available the first
  time the action runs.
  2. Either (a) or (b)
    a. inputs/deps ensure that the action runs whenever one of the files changes
    b. the files are added to the action's depfile

NOTE: All paths within .build_config files are relative to $OUTPUT_CHROMIUM_DIR.

This is a technical note describing the format of .build_config files.
Please keep it updated when changing this script. For extraction and
visualization instructions, see build/aosp/docs/build_config.md

------------- BEGIN_MARKDOWN ---------------------------------------------------
The .build_config file format
===

# Introduction

This document tries to explain the format of `.build_config` generated during
the AOSP build of Chromium. For a higher-level explanation of these files,
please read
[build/asop/docs/build_config.md](build/aosp/docs/build_config.md).

# The `deps_info` top-level dictionary:

All `.build_config` files have a required `'deps_info'` key, whose value is a
dictionary describing the target and its dependencies. The latter has the
following required keys:

## Required keys in `deps_info`:

* `deps_info['type']`: The target type as a string.

    The following types are known by the internal GN build rules and the
    build scripts altogether:

    * [java_binary](#target_java_binary)
    * [java_annotation_processor](#target_java_annotation_processor)
    * [junit_binary](#target_junit_binary)
    * [java_library](#target_java_library)
    * [aosp_assets](#target_aosp_assets)
    * [aosp_resources](#target_aosp_resources)
    * [aosp_app](#target_aosp_app)
    * [dist_jar](#target_dist_jar)
    * [dist_aar](#target_dist_aar)
    * [resource_rewriter](#target_resource_rewriter)
    * [group](#target_group)

    See later sections for more details of some of these.

* `deps_info['path']`: Path to the target's `.build_config` file.

* `deps_info['name']`: Nothing more than the basename of `deps_info['path']`
at the moment.

* `deps_info['deps_configs']`: List of paths to the `.build_config` files of
all *direct* dependencies of the current target.

    NOTE: Because the `.build_config` of a given target is always generated
    after the `.build_config` of its dependencies, the `write_build_config.py`
    script can use chains of `deps_configs` to compute transitive dependencies
    for each target when needed.

## Optional keys in `deps_info`:

The following keys will only appear in the `.build_config` files of certain
target types:

* `deps_info['requires_aosp']`: True to indicate that the corresponding
code uses AOSP-specific APIs, and thus cannot run on the host within a
regular JVM. May only appear in Java-related targets.

* `deps_info['supports_aosp']`:
May appear in Java-related targets, and indicates that
the corresponding code doesn't use Java APIs that are not available on
AOSP. As such it may run either on the host or on an AOSP device.

* `deps_info['assets']`:
Only seen for the [`aosp_assets`](#target_aosp_assets) type. See below.

* `deps_info['package_name']`: Java package name associated with this target.

    NOTE: For `aosp_resources` targets,
    this is the package name for the corresponding R class. For `aosp_app`
    targets, this is the corresponding package name. This does *not* appear for
    other target types.

* `deps_info['manifest']`:
Path to an AndroidManifest.xml file related to the current target.

# Top-level `resources` dictionary:

This dictionary only appears for a few target types that can contain or
relate to AOSP resources (e.g. `aosp_resources` or `aosp_app`):

* `resources['dependency_zips']`:
List of `deps_info['resources_zip']` entries for all `aosp_resources`
dependencies for the current target.

* `resource['extra_package_names']`:
Always empty for `aosp_resources` types. Otherwise,
the list of `deps_info['package_name']` entries for all `aosp_resources`
dependencies for the current target. Computed automatically by
`write_build_config.py`.

* `resources['extra_r_text_files']`:
Always empty for `aosp_resources` types. Otherwise, the list of
`deps_info['r_text']` entries for all `aosp_resources` dependencies for
the current target. Computed automatically.


# `.build_config` target types description:

## <a name="target_group">Target type `group`</a>:

This type corresponds to a simple target that is only used to group
dependencies. It matches the `java_group()` GN template. Its only top-level
`deps_info` keys are `supports_aosp` (always True), and `deps_configs`.


## <a name="target_aosp_resources">Target type `aosp_resources`</a>:

This type corresponds to targets that are used to group AOSP resource files.
For example, all `aosp_resources` dependencies of an `aosp_app` will
end up packaged into the final APP by the build system.

It uses the following keys:

* `deps_info['resource_dirs']`:
List of paths to the source directories containing the resources for this
target. This key is optional, because some targets can refer to prebuilt
`.aar` archives.


* `deps_info['resources_zip']`:
*Required*. Path to the `.resources.zip` file that contains all raw/uncompiled
resource files for this target (and also no `R.txt`, `R.java` or `R.class`).

    If `deps_info['resource_dirs']` is missing, this must point to a prebuilt
    `.aar` archive containing resources. Otherwise, this will point to a
    zip archive generated at build time, wrapping the content of
    `deps_info['resource_dirs']` into a single zip file.

* `deps_info['package_name']`:
Java package name that the R class for this target belongs to.

* `deps_info['manifest']`:
Optional. Path to the top-level manifest file associated with these
resources (if not provided, an empty manifest will be used to generate R.txt).

* `deps_info['r_text']`:
Provide the path to the `R.txt` file that describes the resources wrapped by
this target. Normally this file is generated from the content of the resource
directories or zip file, but some targets can provide their own `R.txt` file
if they want.

* `deps_info['srcjar_path']`:
Path to the `.srcjar` file that contains the auto-generated `R.java` source
file corresponding to the content of `deps_info['r_text']`. This is *always*
generated from the content of `deps_info['r_text']` by the
`build/aosp/gyp/process_resources.py` script.


## <a name="target_aosp_assets">Target type `aosp_assets`</a>:

This type corresponds to targets used to group AOSP assets, i.e. liberal
files that will be placed under `//assets/` within the final APP.

These use an `deps_info['assets']` key to hold a dictionary of values related
to assets covered by this target.

* `assets['sources']`:
The list of all asset source paths for this target. Each source path can
use an optional `:<zipPath>` suffix, where `<zipPath>` is the final location
of the assets (relative to `//assets/`) within the APP.

* `assets['outputs']`:
Optional. Some of the sources might be renamed before being stored in the
final //assets/ sub-directory. When this happens, this contains a list of
all renamed output file paths

    NOTE: When not empty, the first items of `assets['sources']` must match
    every item in this list. Extra sources correspond to non-renamed sources.

    NOTE: This comes from the `asset_renaming_destinations` parameter for the
    `aosp_assets()` GN template.

* `assets['disable_compression']`:
Optional. Will be True to indicate that these assets should be stored
uncompressed in the final APP. For example, this is necessary for locale
.pak files used by the System WebView feature.

* `assets['treat_as_locale_paks']`:
Optional. Will be True to indicate that these assets are locale `.pak` files
(containing localized strings for C++). These are later processed to generate
a special ``.build_config`.java` source file, listing all supported Locales in
the current build.


## <a name="target_java_library">Target type `java_library`</a>:

This type is used to describe target that wrap Java bytecode, either created
by compiling sources, or providing them with a prebuilt jar.

* `deps_info['unprocessed_jar_path']`:
Path to the original .jar file for this target, before any kind of processing
through Proguard or other tools. For most targets this is generated
from sources, with a name like `$target_name.javac.jar`. However, when using
a prebuilt jar, this will point to the source archive directly.

* `deps_info['jar_path']`:
Path to a file that is the result of processing
`deps_info['unprocessed_jar_path']` with various tools.

* `deps_info['interface_jar_path']:
Path to the interface jar generated for this library. This corresponds to
a jar file that only contains declarations. Generated by running the `ijar`
tool on `deps_info['jar_path']`

* `deps_info['dex_path']`:
Path to the `.dex` file generated for this target, from `deps_info['jar_path']`
unless this comes from a prebuilt `.aar` archive.

* `deps_info['is_prebuilt']`:
True to indicate that this target corresponds to a prebuilt `.jar` file.
In this case, `deps_info['unprocessed_jar_path']` will point to the source
`.jar` file. Otherwise, it will be point to a build-generated file.

* `deps_info['java_sources_file']`:
Path to a single `.sources` file listing all the Java sources that were used
to generate the library (simple text format, one `.jar` path per line).

* `deps_info['owned_resource_dirs']`:
List of all resource directories belonging to all resource dependencies for
this target.

* `deps_info['owned_resource_zips']`:
List of all resource zip files belonging to all resource dependencies for this
target.

* `deps_info['owned_resource_srcjars']`:
List of all .srcjar files belonging to all resource dependencies for this
target.

* `deps_info['javac']`:
A dictionary containing information about the way the sources in this library
are compiled. Appears also on other Java-related targets. See the [dedicated
section about this](#dict_javac) below for details.

* `deps_info['javac_full_classpath']`:
The classpath used when performing bytecode processing. Essentially the
collection of all `deps_info['unprocessed_jar_path']` entries for the target
and all its dependencies.

* `deps_info['javac_full_interface_classpath']`:
The classpath used when using the error-prone compiler.

* `deps_info['proguard_enabled"]`:
True to indicate that ProGuard processing is enabled for this target.

* `deps_info['proguard_configs"]`:
A list of paths to ProGuard configuration files related to this library.

* `deps_info['extra_classpath_jars']:
For some Java related types, a list of extra `.jar` files to use at build time
but not at runtime.

## <a name="target_java_binary">Target type `java_binary`</a>:

This type corresponds to a Java binary, which is nothing more than a
`java_library` target that also provides a main class name. It thus inherits
all entries from the `java_library` type, and adds:

* `deps_info['main_class']`:
Name of the main Java class that serves as an entry point for the binary.

* `deps_info['java_runtime_classpath']`:
The classpath used when running a Java or AOSP binary. Essentially the
collection of all `deps_info['jar_path']` entries for the target and all its
dependencies.


## <a name="target_junit_binary">Target type `junit_binary`</a>:

A target type for JUnit-specific binaries. Identical to
[`java_binary`](#target_java_binary) in the context of `.build_config` files,
except the name.


## <a name="target_java_annotation_processor">Target type \
`java_annotation_processor`</a>:

A target type for Java annotation processors. Identical to
[`java_binary`](#target_java_binary) in the context of `.build_config` files,
except the name, except that it requires a `deps_info['main_class']` entry.


## <a name="target_aosp_app">Target type `aosp_app`</a>:

Corresponds to an AOSP APP. Inherits from the
[`java_binary`](#target_java_binary) type and adds:

* `deps_info['app_path']`:
Path to the raw, unsigned, APP generated by this target.

* `deps_info['incremental_app_path']`:
Path to the raw, unsigned, incremental APP generated by this target.

* `deps_info['incremental_install_json_path']`:
Path to the JSON file with per-app details for incremental install.
See `build/aosp/gyp/incremental/write_installer_json.py` for more
details about its content.

* `deps_info['dist_jar']['all_interface_jars']`:
For `aosp_app` and `dist_jar` targets, a list of all interface jar files
that will be merged into the final `.jar` file for distribution.

* `deps_info['final_dex']['path']:
Path to the final classes.dex file (or classes.zip in case of multi-dex)
for this APP.

* `deps_info['final_dex']['dependency_dex_files']`:
The list of paths to all `deps_info['dex_path']` entries for all library
dependencies for this APP.

* `deps_info['proto_resources_path']`:
The path of an zip archive containing the APP's resources compiled to the
protocol buffer format (instead of regular binary xml + resources.arsc).

* `deps_info['module_rtxt_path']`:
The path of the R.txt file generated when compiling the resources for the bundle
module.

* `native['libraries']`
List of native libraries for the primary ABI to be embedded in this APP.
E.g. [ "libchrome.so" ] (i.e. this doesn't include any ABI sub-directory
prefix).

* `native['java_libraries_list']`
The same list as `native['libraries']` as a string holding a Java source
fragment, e.g. `"{\"chrome\"}"`, without any `lib` prefix, and `.so`
suffix (as expected by `System.loadLibrary()`).

* `native['second_abi_libraries']`
List of native libraries for the secondary ABI to be embedded in this APP.
Empty if only a single ABI is supported.

* `native['secondary_abi_java_libraries_list']`
The same list as `native['second_abi_libraries']` as a Java source string.

* `native['uncompress_shared_libraries']`
A boolean indicating whether native libraries are stored uncompressed in the
APP.

* `native['extra_shared_libraries']`
A list of native libraries to store within the APP, in addition to those from
`native['libraries']`. These correspond to things like the Chromium linker
or instrumentation libraries.

* `assets`
A list of assets stored compressed in the APP. Each entry has the format
`<source-path>:<destination-path>`, where `<source-path>` is relative to
`$CHROMIUM_OUTPUT_DIR`, and `<destination-path>` is relative to `//assets/`
within the APP.

NOTE: Not to be confused with the `deps_info['assets']` dictionary that
belongs to `aosp_assets` targets only.

* `uncompressed_assets`
A list of uncompressed assets stored in the APP. Each entry has the format
`<source-path>:<destination-path>` too.

* `compressed_locales_java_list`
A string holding a Java source fragment that gives the list of locales stored
compressed in the `//assets/` directory. E.g. `"{\"am\","\ar\",\"en-US\"}"`.
Note that the files will be stored with the `.pak` extension (e.g.
`//assets/en-US.pak`).

* `uncompressed_locales_java_list`
A string holding a Java source fragment that gives the list of locales stored
uncompressed in the `//assets/stored-locales/` directory. These are used for
the System WebView feature only. Note that the files will be stored with the
`.pak` extension.

* `extra_aosp_manifests`
A list of `deps_configs['manifest]` entries, for all resource
dependencies for this target. I.e. a list of paths to manifest files for
all the resources in this APP. These will be merged with the root manifest
file to generate the final one used to build the APP.

* `java_resources_jars`
This is a list of `.jar` files whose *Java* resources should be included in
the final APP. For example, this is used to copy the `.res` files from the
EMMA Coverage tool. The copy will omit any `.class` file and the top-level
`//meta-inf/` directory from the input jars. Everything else will be copied
into the final APP as-is.

NOTE: This has nothing to do with *AOSP* resources.

* `jni['all_source']`
The list of all `deps_info['java_sources_file']` entries for all library
dependencies for this APP. Note: this is a list of files, where each file
contains a list of Java source files. This is used for JNI registration.

* `deps_info['proguard_all_configs']`:
The collection of all 'deps_info['proguard_configs']` values from this target
and all its dependencies.

* `deps_info['proguard_classpath_jars']`:
The collection of all 'deps_info['extra_classpath_jars']` values from all
dependencies.

* `deps_info['proguard_under_test_mapping']`:
Applicable to apps with proguard enabled that have an app_under_test. This is
the path to the app_under_test's output proguard .mapping file.

## <a name="target_dist_aar">Target type `dist_aar`</a>:

This type corresponds to a target used to generate an `.aar` archive for
distribution. The archive's content is determined by the target's dependencies.

This always has the following entries:

  * `deps_info['supports_aosp']` (always True).
  * `deps_info['requires_aosp']` (always True).
  * `deps_info['proguard_configs']` (optional).


## <a name="target_dist_jar">Target type `dist_jar`</a>:

This type is similar to [`dist_aar`](#target_dist_aar) but is not
AOSP-specific, and used to create a `.jar` file that can be later
redistributed.

This always has the following entries:

  * `deps_info['proguard_enabled']` (False by default).
  * `deps_info['proguard_configs']` (optional).
  * `deps_info['supports_aosp']` (True by default).
  * `deps_info['requires_aosp']` (False by default).



## <a name="target_resource_rewriter">Target type `resource_rewriter`</a>:

The ResourceRewriter Java class is in charge of rewriting resource IDs at
runtime, for the benefit of the System WebView feature. This is a special
target type for it.

Its `.build_config` only keeps a list of dependencies in its
`deps_info['deps_configs']` key.

## <a name="dict_javac">The `deps_info['javac']` dictionary</a>:

This dictionary appears in Java-related targets (e.g. `java_library`,
`aosp_app` and others), and contains information related to the compilation
of Java sources, class files, and jars.

* `javac['resource_packages']`
For `java_library` targets, this is the list of package names for all resource
dependencies for the current target. Order must match the one from
`javac['srcjars']`. For other target types, this key does not exist.

* `javac['classpath']`
The classpath used to compile this target when annotation processors are
present.

* `javac['interface_classpath']`
The classpath used to compile this target when annotation processors are
not present. These are also always used to known when a target needs to be
rebuilt.

* `javac['processor_classpath']`
The classpath listing the jars used for annotation processors. I.e. sent as
`-processorpath` when invoking `javac`.

* `javac['processor_classes']`
The list of annotation processor main classes. I.e. sent as `-processor' when
invoking `javac`.

## <a name="aosp_app_bundle">Target type `aosp_app_bundle`</a>:

This type corresponds to an AOSP app bundle (`.aab` file).

--------------- END_MARKDOWN ---------------------------------------------------
"""

import itertools
import json
import optparse
import os
import sys
import xml.dom.minidom

from util import build_utils

# Types that should never be used as a dependency of another build config.
_ROOT_TYPES = ('aosp_app', 'java_binary', 'java_annotation_processor',
               'junit_binary', 'resource_rewriter', 'aosp_app_bundle')
# Types that should not allow code deps to pass through.
_RESOURCE_TYPES = ('aosp_assets', 'aosp_resources', 'system_java_library')


def _ExtractMarkdownDocumentation(input_text):
  """Extract Markdown documentation from a list of input strings lines.

     This generates a list of strings extracted from |input_text|, by looking
     for '-- BEGIN_MARKDOWN --' and '-- END_MARKDOWN --' line markers."""
  in_markdown = False
  result = []
  for line in input_text.splitlines():
    if in_markdown:
      if '-- END_MARKDOWN --' in line:
        in_markdown = False
      else:
        result.append(line)
    else:
      if '-- BEGIN_MARKDOWN --' in line:
        in_markdown = True

  return result


def _ParseAndFlattenGnLists(gn_lists):
    ret = []
    for arg in gn_lists:
        ret.extend(build_utils.parse_gn_list(arg))
    return ret


class AndroidManifest(object):
  def __init__(self, path):
    self.path = path
    dom = xml.dom.minidom.parse(path)
    manifests = dom.getElementsByTagName('manifest')
    assert len(manifests) == 1
    self.manifest = manifests[0]

  def GetInstrumentationElements(self):
    instrumentation_els = self.manifest.getElementsByTagName('instrumentation')
    if len(instrumentation_els) == 0:
      return None
    return instrumentation_els

  def CheckInstrumentationElements(self, expected_package):
    instrs = self.GetInstrumentationElements()
    if not instrs:
      raise Exception('No <instrumentation> elements found in %s' % self.path)
    for instr in instrs:
      instrumented_package = instr.getAttributeNS(
          'http://schemas.android.com/apk/res/android', 'targetPackage')
      if instrumented_package != expected_package:
        raise Exception(
            'Wrong instrumented package. Expected %s, got %s'
            % (expected_package, instrumented_package))

  def GetPackageName(self):
    return self.manifest.getAttribute('package')


dep_config_cache = {}


def GetDepConfig(path):
  if path not in dep_config_cache:
    with open(path) as jsonfile:
      dep_config_cache[path] = json.load(jsonfile)['deps_info']
  return dep_config_cache[path]


def DepsOfType(wanted_type, configs):
  if wanted_type == "java_library":
    return [c for c in configs
            if c['type'] == wanted_type or c['type'] == "ohos_maple_jar2so"]
  else:
    return [c for c in configs if c['type'] == wanted_type]


def GetAllDepsConfigsInOrder(deps_config_paths):
  def GetDeps(path):
    return GetDepConfig(path)['deps_configs']
  return build_utils.get_sorted_transitive_dependencies(deps_config_paths, GetDeps)


class Deps(object):
  def __init__(self, direct_deps_config_paths):
    self.all_deps_config_paths = GetAllDepsConfigsInOrder(
        direct_deps_config_paths)
    self.direct_deps_configs = [
        GetDepConfig(p) for p in direct_deps_config_paths]
    self.all_deps_configs = [
        GetDepConfig(p) for p in self.all_deps_config_paths]
    self.direct_deps_config_paths = direct_deps_config_paths

  def All(self, wanted_type=None):
    if type is None:
      return self.all_deps_configs
    return DepsOfType(wanted_type, self.all_deps_configs)

  def Direct(self, wanted_type=None):
    if wanted_type is None:
      return self.direct_deps_configs
    return DepsOfType(wanted_type, self.direct_deps_configs)

  def AllConfigPaths(self):
    return self.all_deps_config_paths

  def RemoveNonDirectDep(self, path):
    if path in self.direct_deps_config_paths:
      raise Exception('Cannot remove direct dep.')
    self.all_deps_config_paths.remove(path)
    self.all_deps_configs.remove(GetDepConfig(path))

  def GradlePrebuiltJarPaths(self):
    ret = []

    def helper(cur):
      for config in cur.Direct('java_library'):
        if config['is_prebuilt'] or config['gradle_treat_as_prebuilt']:
          if config['jar_path'] not in ret:
            ret.append(config['jar_path'])

    helper(self)
    return ret

  def GradleLibraryProjectDeps(self):
    ret = []

    def helper(cur):
      for config in cur.Direct('java_library'):
        if config['is_prebuilt']:
          pass
        elif config['gradle_treat_as_prebuilt']:
          helper(Deps(config['deps_configs']))
        elif config not in ret:
          ret.append(config)

    helper(self)
    return ret


def _MergeAssets(all_assets):
  """Merges all assets from the given deps.

  Returns:
    A tuple of: (compressed, uncompressed, locale_paks)
    |compressed| and |uncompressed| are lists of "srcPath:zipPath". srcPath is
    the path of the asset to add, and zipPath is the location within the zip
    (excluding assets/ prefix).
    |locale_paks| is a set of all zipPaths that have been marked as
    treat_as_locale_paks=true.
  """
  compressed = {}
  uncompressed = {}
  locale_paks = set()
  for asset_dep in all_assets:
    entry = asset_dep['assets']
    disable_compression = entry.get('disable_compression')
    treat_as_locale_paks = entry.get('treat_as_locale_paks')
    dest_map = uncompressed if disable_compression else compressed
    other_map = compressed if disable_compression else uncompressed
    outputs = entry.get('outputs', [])
    for src, dest in itertools.zip_longest(entry['sources'], outputs):
      if not dest:
        dest = os.path.basename(src)
      # Merge so that each path shows up in only one of the lists, and that
      # deps of the same target override previous ones.
      other_map.pop(dest, 0)
      dest_map[dest] = src
      if treat_as_locale_paks:
        locale_paks.add(dest)

  def create_list(asset_map):
    ret = ['%s:%s' % (src, dest) for dest, src in list(asset_map.items())]
    # Sort to ensure deterministic ordering.
    ret.sort()
    return ret

  return create_list(compressed), create_list(uncompressed), locale_paks


def _ResolveGroups(configs):
  """Returns a list of configs with all groups inlined."""
  ret = list(configs)
  while True:
    groups = DepsOfType('group', ret)
    if not groups:
      return ret
    for config in groups:
      index = ret.index(config)
      expanded_configs = [GetDepConfig(p) for p in config['deps_configs']]
      ret[index:index + 1] = expanded_configs


def _DepsFromPaths(dep_paths, target_type, filter_root_targets=True):
  """Resolves all groups and trims dependency branches that we never want.
  """
  configs = [GetDepConfig(p) for p in dep_paths]
  configs = _ResolveGroups(configs)
  # Don't allow root targets to be considered as a dep.
  if filter_root_targets:
    configs = [c for c in configs if c['type'] not in _ROOT_TYPES]

  # Don't allow java libraries to cross through assets/resources.
  if target_type in _RESOURCE_TYPES:
    configs = [c for c in configs if c['type'] in _RESOURCE_TYPES]
  return Deps([c['path'] for c in configs])


def _ExtractSharedLibsFromRuntimeDeps(runtime_deps_files):
  ret = []
  for path in runtime_deps_files:
    with open(path) as f:
      for line in f:
        line = line.rstrip()
        if not line.endswith('.so'):
          continue
        # Only unstripped .so files are listed in runtime deps.
        # Convert to the stripped .so by going up one directory.
        ret.append(os.path.normpath(line.replace('lib.unstripped/', '')))
  ret.reverse()
  return list(set(ret))


def _CreateJavaLibrariesList(library_paths):
  """Returns a java literal array with the "base" library names:
  e.g. libfoo.so -> foo
  """
  return ('{%s}' % ','.join(['"%s"' % s[3:-3] for s in library_paths]))


def _CreateJavaLocaleListFromAssets(assets, locale_paks):
  """Returns a java literal array from a list of locale assets.

  Args:
    assets: A list of all APP asset paths in the form 'src:dst'
    locale_paks: A list of asset paths that corresponds to the locale pak
      files of interest. Each |assets| entry will have its 'dst' part matched
      against it to determine if they are part of the result.
  Returns:
    A string that is a Java source literal array listing the locale names
    of the corresponding asset files, without directory or .pak suffix.
    E.g. '{"en-GB", "en-US", "es-ES", "fr", ... }'
  """
  assets_paths = [a.split(':')[1] for a in assets]
  locales = [os.path.basename(a)[:-4] for a in assets_paths if a in locale_paks]
  return '{%s}' % ','.join(['"%s"' % l for l in sorted(locales)])


def combine_java_sources_files(sources_list, java_sources_file):
  with open(java_sources_file, 'w') as k:
    for sources_file in sources_list:
      with open(sources_file, 'r') as f:
        k.write(f.read())


def main(argv):
  parser = optparse.OptionParser()
  build_utils.add_depfile_option(parser)
  parser.add_option('--build-config', help='Path to build_config output.')
  parser.add_option(
      '--type',
      help='Type of this target (e.g. java_library).')
  parser.add_option(
      '--deps-configs',
      help='GN-list of dependent build_config files.')
  parser.add_option(
      '--annotation-processor-configs',
      help='GN-list of build_config files for annotation processors.')
  parser.add_option(
      '--classpath-deps-configs',
      help='GN-list of build_config files for libraries to include as '
           'build-time-only classpath.')

  # aosp_resources options
  parser.add_option('--srcjar', help='Path to target\'s resources srcjar.')
  parser.add_option('--resources-zip', help='Path to target\'s resources zip.')
  parser.add_option('--r-text', help='Path to target\'s R.txt file.')
  parser.add_option('--package-name',
      help='Java package name for these resources.')
  parser.add_option('--manifest', help='Path to manifest.')
  parser.add_option('--resource-dirs', action='append', default=[],
                    help='GYP-list of resource dirs')

  # aosp_assets options
  parser.add_option('--asset-sources', help='List of asset sources.')
  parser.add_option('--asset-renaming-sources',
                    help='List of asset sources with custom destinations.')
  parser.add_option('--asset-renaming-destinations',
                    help='List of asset custom destinations.')
  parser.add_option('--disable-asset-compression', action='store_true',
                    help='Whether to disable asset compression.')
  parser.add_option('--treat-as-locale-paks', action='store_true',
      help='Consider the assets as locale paks in BuildConfig.java')

  # java library options
  parser.add_option('--jar-path', help='Path to target\'s jar output.')
  parser.add_option('--unprocessed-jar-path',
      help='Path to the .jar to use for javac classpath purposes.')
  parser.add_option('--interface-jar-path',
      help='Path to the .interface.jar to use for javac classpath purposes.')
  parser.add_option('--is-prebuilt', action='store_true',
                    help='Whether the jar was compiled or pre-compiled.')
  parser.add_option('--java-sources-file', help='Path to .sources file')
  parser.add_option('--bundled-srcjars',
      help='GYP-list of .srcjars that have been included in this java_library.')
  parser.add_option('--supports-aosp', action='store_true',
      help='Whether this library supports running on the AOSP platform.')
  parser.add_option('--requires-aosp', action='store_true',
      help='Whether this library requires running on the AOSP platform.')
  parser.add_option('--bypass-platform-checks', action='store_true',
      help='Bypass checks for support/require AOSP platform.')
  parser.add_option('--extra-classpath-jars',
      help='GYP-list of .jar files to include on the classpath when compiling, '
           'but not to include in the final binary.')
  parser.add_option('--gradle-treat-as-prebuilt', action='store_true',
      help='Whether this library should be treated as a prebuilt library by '
           'generate_gradle.py.')
  parser.add_option('--main-class',
      help='Main class for java_binary or java_annotation_processor targets.')
  parser.add_option('--java-resources-jar-path',
                    help='Path to JAR that contains java resources. Everything '
                    'from this JAR except meta-inf/ content and .class files '
                    'will be added to the final APP.')

  # java library options
  parser.add_option('--dex-path', help='Path to target\'s dex output.')

  # native library options
  parser.add_option('--shared-libraries-runtime-deps',
                    help='Path to file containing runtime deps for shared '
                         'libraries.')
  parser.add_option('--native-libs',
                    action='append',
                    help='GN-list of native libraries for primary '
                         'aosp-abi. Can be specified multiple times.',
                    default=[])
  parser.add_option('--secondary-abi-shared-libraries-runtime-deps',
                    help='Path to file containing runtime deps for secondary '
                         'abi shared libraries.')
  parser.add_option('--secondary-native-libs',
                    action='append',
                    help='GN-list of native libraries for secondary '
                         'aosp-abi. Can be specified multiple times.',
                    default=[])
  parser.add_option('--uncompress-shared-libraries', default=False,
                    action='store_true',
                    help='Whether to store native libraries uncompressed')
  # app options
  parser.add_option('--app-path', help='Path to the target\'s app output.')
  parser.add_option('--incremental-app-path',
                    help="Path to the target's incremental app output.")
  parser.add_option('--incremental-install-json-path',
                    help="Path to the target's generated incremental install "
                    "json.")

  parser.add_option('--tested-app-config',
      help='Path to the build config of the tested app (for an instrumentation '
      'test app).')
  parser.add_option('--proguard-enabled', action='store_true',
      help='Whether proguard is enabled for this app or bundle module.')
  parser.add_option('--proguard-configs',
      help='GN-list of proguard flag files to use in final app.')
  parser.add_option('--proguard-mapping-path',
      help='Path to jar created by ProGuard step')
  parser.add_option('--fail',
      help='GN-list of error message lines to fail with.')

  parser.add_option('--final-dex-path',
                    help='Path to final input classes.dex (or classes.zip) to '
                    'use in final app.')
  parser.add_option('--app-proto-resources',
                    help='Path to resources compiled in protocol buffer format '
                         ' for this app.')
  parser.add_option(
      '--module-rtxt-path',
      help='Path to R.txt file for resources in a bundle module.')

  parser.add_option('--generate-markdown-format-doc', action='store_true',
                    help='Dump the Markdown .build_config format documentation '
                    'then exit immediately.')
  parser.add_option('--output_shared_library',
                    help='output shared library for ohos_maple_jar2so target')
  parser.add_option('--manifest_file',
                    help='path to manifest_file of java_library target')
  parser.add_option('--output_mplt',
                    action='append',
                    help='output mplt for ohos_maple_jar2so target')
  parser.add_option('--deps_mplt',
                    help='dependent mplts of ohos_maple_jar2so target')
  parser.add_option('--write_java_sources_file', action='store_true',
                    help='only useful for combine_jars target')
  parser.add_option('--aosp_deps', action='append',
                    help='aosp_deps of java_library targets')
  parser.add_option('--external_deps', action='append',
                    help='external_deps of java_library targets')
  parser.add_option('--combine_target', action='store_true',
                    help='specify it is an ohos_combine_jars targets')
  parser.add_option('--is_hap', action='store_true',
                    help='specify if it is a hap package')
  parser.add_option('--hap_profile',
                    help='path to hap profile')
  parser.add_option('--shell-app',
                    help='path to shell app')
  parser.add_option('--jni-output-dir',
                    help='output directories for jni headers')

  options, args = parser.parse_args(argv)

  if args:
    parser.error('No positional arguments should be given.')

  if options.generate_markdown_format_doc:
    doc_lines = _ExtractMarkdownDocumentation(__doc__)
    for line in doc_lines:
      print(line)
    return 0

  if options.output_mplt:
    options.output_mplt = _ParseAndFlattenGnLists(options.output_mplt)

  if options.fail:
    parser.error('\n'.join(build_utils.parse_gn_list(options.fail)))

  jar_path_options = ['jar_path', 'unprocessed_jar_path', 'interface_jar_path']
  required_options_map = {
      'aosp_app': ['build_config', 'dex_path', 'final_dex_path'] + \
          jar_path_options,
      'aosp_app_bundle_module': ['build_config', 'dex_path',
          'final_dex_path'] + jar_path_options,
      'aosp_assets': ['build_config'],
      'aosp_resources': ['build_config', 'resources_zip'],
      'dist_aar': ['build_config'],
      'dist_jar': ['build_config'],
      'group': ['build_config'],
      'java_annotation_processor': ['build_config', 'main_class'],
      'java_binary': ['build_config'],
      'java_library': ['build_config'] + jar_path_options,
      'junit_binary': ['build_config'],
      'resource_rewriter': ['build_config'],
      'system_java_library': ['build_config'],
      'aosp_app_bundle': ['build_config'],
      'ohos_maple_jar2so': ['build_config'],
  }
  required_options = required_options_map.get(options.type)
  if not required_options:
    raise Exception('Unknown type: <%s>' % options.type)

  build_utils.check_options(options, parser, required_options)

  if options.app_proto_resources:
    if options.type != 'aosp_app_bundle_module':
      raise Exception('--app-proto-resources can only be used with '
                      '--type=aosp_app_bundle_module')
  if options.module_rtxt_path:
    if options.type != 'aosp_app_bundle_module':
      raise Exception('--module-rxt-path can only be used with '
                      '--type=aosp_app_bundle_module')

  is_app_or_module_target = options.type in ('aosp_app',
      'aosp_app_bundle_module')

  if options.uncompress_shared_libraries:
    if not is_app_or_module_target:
      raise Exception('--uncompressed-shared-libraries can only be used '
                      'with --type=aosp_app or '
                      '--type=aosp_app_bundle_module')

  if any(getattr(options, x) for x in jar_path_options):
    for attr in jar_path_options:
      if not getattr(options, attr):
        raise 'Expected %s to be set.'

  if options.requires_aosp and not options.supports_aosp:
    raise Exception(
        '--supports-aosp is required when using --requires-aosp')

  is_java_target = options.type in (
      'java_binary', 'junit_binary', 'java_annotation_processor',
      'java_library', 'aosp_app', 'dist_aar', 'dist_jar',
      'system_java_library', 'aosp_app_bundle_module', 'ohos_maple_jar2so')

  deps = _DepsFromPaths(
      build_utils.parse_gn_list(options.deps_configs), options.type)
  processor_deps = _DepsFromPaths(
      build_utils.parse_gn_list(options.annotation_processor_configs or ''),
      options.type, filter_root_targets=False)
  classpath_deps = _DepsFromPaths(
      build_utils.parse_gn_list(options.classpath_deps_configs or ''),
      options.type)

  all_inputs = sorted(set(deps.AllConfigPaths() +
                          processor_deps.AllConfigPaths() +
                          classpath_deps.AllConfigPaths()))

  system_library_deps = deps.Direct('system_java_library')
  direct_library_deps = deps.Direct('java_library')
  all_library_deps = deps.All('java_library')
  all_resources_deps = deps.All('aosp_resources')

  # Initialize some common config.
  # Any value that needs to be queryable by dependents must go within deps_info.
  config = {
    'deps_info': {
      'name': os.path.basename(options.build_config),
      'path': options.build_config,
      'type': options.type,
      'deps_configs': sorted(deps.direct_deps_config_paths)
    },
    # Info needed only by generate_gradle.py.
    'gradle': {}
  }
  deps_info = config['deps_info']
  gradle = config['gradle']

  if options.jni_output_dir:
    deps_info['jni_output_dir'] = options.jni_output_dir

  if options.type == 'ohos_maple_jar2so':
    config['outputs'] = {}
    if options.output_shared_library:
      config['outputs']['shared_library'] = options.output_shared_library

    config['outputs']['output_mplt'] = []
    config['deps_mplt'] = []
    if options.output_mplt:
      mplts = []
      for mplt in options.output_mplt:
        if mplt.endswith('.txt'):
          all_inputs.append(mplt)
          with open(mplt, 'r') as f:
            mplts.extend(f.read().split('\n'))
        else:
          mplts.extend([mplt])
      config['outputs']['output_mplt'] = mplts
      deps_info['deps_mplt'] = sorted(mplts)

  if options.type == 'aosp_app' and options.tested_app_config:
    tested_app_deps = Deps([options.tested_app_config])
    tested_app_name = tested_app_deps.Direct()[0]['name']
    tested_app_resources_deps = tested_app_deps.All('aosp_resources')
    gradle['app_under_test'] = tested_app_name
    all_resources_deps = [
        d for d in all_resources_deps if d not in tested_app_resources_deps]

  # Required for generating gradle files.
  if options.type == 'java_library':
    deps_info['is_prebuilt'] = bool(options.is_prebuilt)
    deps_info['gradle_treat_as_prebuilt'] = options.gradle_treat_as_prebuilt
    deps_info['deps_mplt'] = []
    for c in classpath_deps.Direct('ohos_maple_jar2so'):
      if 'deps_mplt' not in c.keys():
          continue
      deps_info['deps_mplt'].extend(sorted(m for m in c['deps_mplt']
                                    if m not in deps_info['deps_mplt']))
  deps_info['aosp_deps'] = []
  deps_info['external_deps'] = []
  if options.aosp_deps:
    deps_info['aosp_deps'] += options.aosp_deps
  if options.external_deps:
    deps_info['external_deps'] += options.external_deps
  if options.combine_target:
    for c in direct_library_deps:
      deps_info['aosp_deps'] += c['aosp_deps']
      deps_info['external_deps'] += c['external_deps']
    deps_info['combine_target'] = True
  deps_info['aosp_deps'] = sorted(list(set(deps_info['aosp_deps'])))
  deps_info['external_deps'] = sorted(list(set(deps_info['external_deps'])))


  if options.manifest:
    deps_info['manifest'] = options.manifest
  if options.hap_profile:
    deps_info['hap_profile'] = options.hap_profile

  if is_java_target:
    if options.java_sources_file:
      deps_info['java_sources_file'] = options.java_sources_file
    if options.write_java_sources_file:
      sources_list = [c['java_sources_file'] for c in direct_library_deps
                      if 'java_sources_file' in c]
      combine_java_sources_files(sources_list, options.java_sources_file)
      all_inputs.extend(sources_list)
    if options.bundled_srcjars:
      gradle['bundled_srcjars'] = (
          build_utils.parse_gn_list(options.bundled_srcjars))

    if options.main_class:
      deps_info['main_class'] = options.main_class
    if options.manifest_file:
      deps_info['manifest_file'] = options.manifest_file

  if is_app_or_module_target or options.type in ('group', 'java_library'):
    config['jni'] = {}
    all_java_sources = [c['java_sources_file'] for c in all_library_deps
                        if 'java_sources_file' in c]
    if options.java_sources_file:
      all_java_sources.append(options.java_sources_file)
    config['jni']['all_source'] = all_java_sources

    if options.app_proto_resources:
      deps_info['proto_resources_path'] = options.app_proto_resources

    if options.module_rtxt_path:
      deps_info['module_rtxt_path'] = options.module_rtxt_path

  if is_java_target:
    deps_info['requires_aosp'] = bool(options.requires_aosp)
    deps_info['supports_aosp'] = bool(options.supports_aosp)

    if not options.bypass_platform_checks:
      deps_require_aosp = (all_resources_deps +
          [d['name'] for d in all_library_deps if d['requires_aosp']])
      deps_not_support_aosp = (
          [d['name'] for d in all_library_deps if not d['supports_aosp']])

      if deps_require_aosp and not options.requires_aosp:
        raise Exception('Some deps require building for the AOSP platform: '
            + str(deps_require_aosp))

      if deps_not_support_aosp and options.supports_aosp:
        raise Exception('Not all deps support the AOSP platform: '
            + str(deps_not_support_aosp))

  if is_java_target:
    # Classpath values filled in below (after applying tested_app_config).
    config['javac'] = {}
    if options.jar_path:
      deps_info['jar_path'] = options.jar_path
      deps_info['unprocessed_jar_path'] = options.unprocessed_jar_path
      deps_info['interface_jar_path'] = options.interface_jar_path
    if options.dex_path:
      deps_info['dex_path'] = options.dex_path
    if options.type == 'aosp_app':
      deps_info['app_path'] = options.app_path
      deps_info['incremental_app_path'] = options.incremental_app_path
      deps_info['incremental_install_json_path'] = (
          options.incremental_install_json_path)

  if options.type == 'aosp_assets':
    all_asset_sources = []
    if options.asset_renaming_sources:
      all_asset_sources.extend(
          build_utils.parse_gn_list(options.asset_renaming_sources))
    if options.asset_sources:
      all_asset_sources.extend(build_utils.parse_gn_list(options.asset_sources))

    deps_info['assets'] = {
        'sources': all_asset_sources
    }
    if options.asset_renaming_destinations:
      deps_info['assets']['outputs'] = (
          build_utils.parse_gn_list(options.asset_renaming_destinations))
    if options.disable_asset_compression:
      deps_info['assets']['disable_compression'] = True
    if options.treat_as_locale_paks:
      deps_info['assets']['treat_as_locale_paks'] = True

  if options.type == 'aosp_resources':
    deps_info['resources_zip'] = options.resources_zip
    if options.srcjar:
      deps_info['srcjar'] = options.srcjar
      deps_info['dex_deps_jar_path'] = options.srcjar
      deps_info['dex_deps_interface_jar_path'] = options.srcjar
      deps_info['jar_path'] = options.srcjar
    if options.manifest:
      manifest = AndroidManifest(options.manifest)
      deps_info['package_name'] = manifest.GetPackageName()
    if options.package_name:
      deps_info['package_name'] = options.package_name
    if options.r_text:
      deps_info['r_text'] = options.r_text

    deps_info['resources_dirs'] = []
    if options.resource_dirs:
      for gyp_list in options.resource_dirs:
        deps_info['resources_dirs'].extend(build_utils.parse_gn_list(gyp_list))

  if options.requires_aosp and is_java_target:
    # Lint all resources that are not already linted by a dependent library.
    owned_resource_dirs = set()
    owned_resource_zips = set()
    owned_resource_srcjars = set()
    for c in all_resources_deps:
      # Always use resources_dirs in favour of resources_zips so that lint error
      # messages have paths that are closer to reality (and to avoid needing to
      # extract during lint).
      if c['resources_dirs']:
        owned_resource_dirs.update(c['resources_dirs'])
      else:
        owned_resource_zips.add(c['resources_zip'])
      srcjar = c.get('srcjar')
      if srcjar:
        owned_resource_srcjars.add(srcjar)

    for c in all_library_deps:
      if c['requires_aosp']:
        owned_resource_dirs.difference_update(c['owned_resources_dirs'])
        owned_resource_zips.difference_update(c['owned_resources_zips'])
        # Many .aar files include R.class files in them, as it makes it easier
        # for IDEs to resolve symbols. However, including them is not required
        # and not all prebuilts do. Rather than try to detect their presence,
        # just assume they are not there. The only consequence is redundant
        # compilation of the R.class.
        if not c['is_prebuilt']:
          owned_resource_srcjars.difference_update(c['owned_resource_srcjars'])
    deps_info['owned_resources_dirs'] = sorted(owned_resource_dirs)
    deps_info['owned_resources_zips'] = sorted(owned_resource_zips)
    deps_info['owned_resource_srcjars'] = sorted(owned_resource_srcjars)

    if options.type == 'java_library':
      config['javac']['resource_packages'] = [
          c['package_name'] for c in all_resources_deps if 'package_name' in c]

  if options.type in ('aosp_resources', 'aosp_app', 'junit_binary',
                      'resource_rewriter', 'dist_aar',
                      'aosp_app_bundle_module'):
    config['resources'] = {}
    config['resources']['dependency_zips'] = [
        c['resources_zip'] for c in all_resources_deps]
    extra_package_names = []
    extra_r_text_files = []
    if options.type != 'aosp_resources':
      extra_package_names = [
          c['package_name'] for c in all_resources_deps if 'package_name' in c]
      extra_r_text_files = [
          c['r_text'] for c in all_resources_deps if 'r_text' in c]

    config['resources']['extra_package_names'] = extra_package_names
    config['resources']['extra_r_text_files'] = extra_r_text_files

  if is_app_or_module_target:
    deps_dex_files = [
        c['dex_path'] for c in all_library_deps if 'dex_path' in c]

  if is_java_target:
    # The classpath used to compile this target when annotation processors are
    # present.
    javac_classpath = [
        c['unprocessed_jar_path'] for c in direct_library_deps]
    # The classpath used to compile this target when annotation processors are
    # not present. These are also always used to know when a target needs to be
    # rebuilt.
    javac_interface_classpath = [
        c['interface_jar_path'] for c in direct_library_deps]
    # The classpath used for error prone.
    javac_full_interface_classpath = [
        c['interface_jar_path'] for c in all_library_deps]
    # The classpath used for bytecode-rewritting.
    javac_full_classpath = [
        c['unprocessed_jar_path'] for c in all_library_deps]

    # Deps to add to the compile-time classpath (but not the runtime classpath).
    javac_extra_jars = []
    extra_jars = []
    for c in classpath_deps.Direct('java_library'):
      if 'unprocessed_jar_path' in c:
        javac_extra_jars.extend([c['unprocessed_jar_path']])
      if 'jar_path' in c:
        extra_jars.extend([c['jar_path']])

    for c in classpath_deps.Direct('ohos_maple_jar2so'):
      if 'javac_full_interface_classpath' in c:
        javac_extra_jars.extend(c['javac_full_interface_classpath'])

    if options.extra_classpath_jars:
      # These are .jars to add to javac classpath but not to runtime classpath.
      javac_extra_jars.extend(
          build_utils.parse_gn_list(options.extra_classpath_jars))
      extra_jars.extend(build_utils.parse_gn_list(options.extra_classpath_jars))

    if extra_jars:
      deps_info['extra_classpath_jars'] = sorted(extra_jars)

    javac_extra_jars = [p for p in javac_extra_jars if p not in javac_classpath]
    deps_info['dex_deps_jar_path'] = sorted(
        [c['jar_path'] for c in all_library_deps])
    deps_info['dex_deps_interface_jar_path'] = sorted(
        [c['interface_jar_path'] for c in all_library_deps])
    javac_classpath.extend(javac_extra_jars)
    javac_interface_classpath.extend(javac_extra_jars)
    javac_full_interface_classpath.extend(
        p for p in javac_extra_jars if p not in javac_full_classpath)
    javac_full_classpath.extend(
        p for p in javac_extra_jars if p not in javac_full_classpath)

  if is_java_target or options.type == 'aosp_app_bundle':
    # The classpath to use to run this target (or as an input to ProGuard).
    java_full_classpath = []
    if is_java_target and options.jar_path:
      java_full_classpath.append(options.jar_path)
    java_full_classpath.extend(c['jar_path'] for c in all_library_deps)
    if options.type == 'aosp_app_bundle':
      for d in deps.Direct('aosp_app_bundle_module'):
        java_full_classpath.extend(
            c for c in d.get('java_runtime_classpath', [])
            if c not in java_full_classpath)

  system_jars = [c['jar_path'] for c in system_library_deps]
  system_interface_jars = [c['interface_jar_path'] for c in system_library_deps]
  if system_library_deps:
    config['aosp'] = {}
    config['aosp']['sdk_interface_jars'] = system_interface_jars
    config['aosp']['sdk_jars'] = system_jars
    gradle['bootclasspath'] = system_jars

  if options.proguard_configs:
    deps_info['proguard_configs'] = (
        build_utils.parse_gn_list(options.proguard_configs))

  if options.type in ('aosp_app', 'dist_aar', 'dist_jar',
                      'aosp_app_bundle_module', 'aosp_app_bundle'):
    all_configs = deps_info.get('proguard_configs', [])
    extra_jars = list()
    for c in all_library_deps:
      all_configs.extend(
          p for p in c.get('proguard_configs', []) if p not in all_configs)
      extra_jars.extend(
          p for p in c.get('extra_classpath_jars', []) if p not in extra_jars)
    if options.type == 'aosp_app_bundle':
      for c in deps.Direct('aosp_app_bundle_module'):
        all_configs.extend(
            p for p in c.get('proguard_configs', []) if p not in all_configs)
    deps_info['proguard_all_configs'] = sorted(all_configs)
    if options.type == 'aosp_app_bundle':
      for d in deps.Direct('aosp_app_bundle_module'):
        extra_jars.extend(
            c for c in d.get('proguard_classpath_jars', [])
            if c not in extra_jars)
    deps_info['proguard_classpath_jars'] = sorted(extra_jars)

    if options.type == 'aosp_app_bundle':
      deps_proguard_enabled = []
      deps_proguard_disabled = []
      for d in deps.Direct('aosp_app_bundle_module'):
        if not d['java_runtime_classpath']:
          # We don't care about modules that have no Java code for proguarding.
          continue
        if d['proguard_enabled']:
          deps_proguard_enabled.append(d['name'])
        else:
          deps_proguard_disabled.append(d['name'])
      if deps_proguard_enabled and deps_proguard_disabled:
        raise Exception('Deps %s have proguard enabled while deps %s have '
                        'proguard disabled' % (deps_proguard_enabled,
                                               deps_proguard_disabled))
    else:
      deps_info['proguard_enabled'] = bool(options.proguard_enabled)
      if options.proguard_mapping_path:
        deps_info['proguard_mapping_path'] = options.proguard_mapping_path

  # The java code for an instrumentation test app is assembled differently for
  # ProGuard vs. non-ProGuard.
  #
  # Without ProGuard: Each library's jar is dexed separately and then combined
  # into a single classes.dex. A test app will include all dex files not already
  # present in the app-under-test. At runtime all test code lives in the test
  # app, and the program code lives in the app-under-test.
  #
  # With ProGuard: Each library's .jar file is fed into ProGuard, which outputs
  # a single .jar, which is then dexed into a classes.dex. A test app includes
  # all jar files from the program and the tests because having them separate
  # doesn't work with ProGuard's whole-program optimizations. Although the
  # app-under-test still has all of its code in its classes.dex, none of it is
  # used at runtime because the copy of it within the test app takes precedence.
  if options.type == 'aosp_app' and options.tested_app_config:
    tested_app_config = GetDepConfig(options.tested_app_config)

    if tested_app_config['proguard_enabled']:
      assert options.proguard_enabled, ('proguard must be enabled for '
          'instrumentation apps if it\'s enabled for the tested app.')
      # Mutating lists, so no need to explicitly re-assign to dict.
      all_configs.extend(p for p in tested_app_config['proguard_all_configs']
                         if p not in all_configs)
      extra_jars.extend(p for p in tested_app_config['proguard_classpath_jars']
                        if p not in extra_jars)
      tested_app_config = GetDepConfig(options.tested_app_config)
      deps_info['proguard_under_test_mapping'] = (
          tested_app_config['proguard_mapping_path'])
    elif options.proguard_enabled:
      # Not sure why you'd want to proguard the test app when the under-test app
      # is not proguarded, but it's easy enough to support.
      deps_info['proguard_under_test_mapping'] = ''

    expected_tested_package = tested_app_config['package_name']
    AndroidManifest(options.manifest).CheckInstrumentationElements(
        expected_tested_package)

    # Add all tested classes to the test's classpath to ensure that the test's
    # java code is a superset of the tested app's java code
    java_full_classpath.extend(
        p for p in tested_app_config['java_runtime_classpath']
        if p not in java_full_classpath)
    # Include in the classpath classes that are added directly to the app under
    # test (those that are not a part of a java_library).
    javac_classpath.append(tested_app_config['unprocessed_jar_path'])
    javac_full_classpath.append(tested_app_config['unprocessed_jar_path'])
    javac_interface_classpath.append(tested_app_config['interface_jar_path'])
    javac_full_interface_classpath.append(
        tested_app_config['interface_jar_path'])
    javac_full_interface_classpath.extend(
        p for p in tested_app_config['javac_full_interface_classpath']
        if p not in javac_full_interface_classpath)
    javac_full_classpath.extend(
        p for p in tested_app_config['javac_full_classpath']
        if p not in javac_full_classpath)

    # Exclude dex files from the test app that exist within the app under test.
    tested_app_library_deps = tested_app_deps.All('java_library')
    tested_app_deps_dex_files = [c['dex_path'] for c in tested_app_library_deps]
    deps_dex_files = [
        p for p in deps_dex_files if p not in tested_app_deps_dex_files]

  # Dependencies for the final dex file of an app.
  if is_app_or_module_target:
    config['final_dex'] = {}
    dex_config = config['final_dex']
    dex_config['dependency_dex_files'] = deps_dex_files
    dex_config['path'] = options.final_dex_path

  if is_java_target:
    config['javac']['bootclasspath'] = system_jars
    config['javac']['classpath'] = javac_classpath
    config['javac']['interface_classpath'] = javac_interface_classpath
    # Direct() will be of type 'java_annotation_processor'.
    config['javac']['processor_classpath'] = [
        c['jar_path'] for c in processor_deps.Direct() if c.get('jar_path')] + [
        c['jar_path'] for c in processor_deps.All('java_library')]
    config['javac']['processor_classes'] = [
        c['main_class'] for c in processor_deps.Direct()]
    deps_info['javac_full_classpath'] = sorted(javac_full_classpath)
    deps_info['javac_full_interface_classpath'] = sorted(
        javac_full_interface_classpath)

  if options.type in ('aosp_app', 'dist_jar', 'java_binary', 'junit_binary',
                      'aosp_app_bundle_module', 'aosp_app_bundle'):
    deps_info['java_runtime_classpath'] = sorted(java_full_classpath)

  if options.type in ('aosp_app', 'dist_jar'):
    all_interface_jars = []
    if options.jar_path:
      all_interface_jars.append(options.interface_jar_path)
    all_interface_jars.extend(c['interface_jar_path'] for c in all_library_deps)

    config['dist_jar'] = {
      'all_interface_jars': all_interface_jars,
    }

  if is_app_or_module_target:
    if options.is_hap is None:
      manifest = AndroidManifest(options.manifest)
      deps_info['package_name'] = manifest.GetPackageName()
      if not options.tested_app_config and manifest.GetInstrumentationElements():
        # This must then have instrumentation only for itself.
        manifest.CheckInstrumentationElements(manifest.GetPackageName())

    library_paths = []
    java_libraries_list = None
    runtime_deps_files = build_utils.parse_gn_list(
        options.shared_libraries_runtime_deps or '[]')
    if runtime_deps_files:
      library_paths = _ExtractSharedLibsFromRuntimeDeps(runtime_deps_files)
      java_libraries_list = _CreateJavaLibrariesList(library_paths)

    secondary_abi_library_paths = []
    secondary_abi_java_libraries_list = None
    secondary_abi_runtime_deps_files = build_utils.parse_gn_list(
        options.secondary_abi_shared_libraries_runtime_deps or '[]')
    if secondary_abi_runtime_deps_files:
      secondary_abi_library_paths = _ExtractSharedLibsFromRuntimeDeps(
          secondary_abi_runtime_deps_files)
      secondary_abi_java_libraries_list = _CreateJavaLibrariesList(
          secondary_abi_library_paths)
    for gn_list in options.secondary_native_libs:
      secondary_abi_library_paths.extend(build_utils.parse_gn_list(gn_list))

    extra_shared_libraries = []
    for gn_list in options.native_libs:
      extra_shared_libraries.extend(build_utils.parse_gn_list(gn_list))

    all_inputs.extend(runtime_deps_files)
    config['native'] = {
      'libraries': library_paths,
      'secondary_abi_libraries': secondary_abi_library_paths,
      'java_libraries_list': java_libraries_list,
      'secondary_abi_java_libraries_list': secondary_abi_java_libraries_list,
      'uncompress_shared_libraries': options.uncompress_shared_libraries,
      'extra_shared_libraries': extra_shared_libraries,
    }
    config['assets'], config['uncompressed_assets'], locale_paks = (
        _MergeAssets(deps.All('aosp_assets')))
    config['compressed_locales_java_list'] = _CreateJavaLocaleListFromAssets(
        config['assets'], locale_paks)
    config['uncompressed_locales_java_list'] = _CreateJavaLocaleListFromAssets(
        config['uncompressed_assets'], locale_paks)

    config['extra_aosp_manifests'] = list([_f for _f in (
        d.get('manifest') for d in all_resources_deps) if _f])

    # Collect java resources
    java_resources_jars = [d['java_resources_jar'] for d in all_library_deps
                           if 'java_resources_jar' in d]
    if options.tested_app_config:
      tested_app_resource_jars = [d['java_resources_jar']
                                  for d in tested_app_library_deps
                                  if 'java_resources_jar' in d]
      java_resources_jars = [jar for jar in java_resources_jars
                             if jar not in tested_app_resource_jars]
    config['java_resources_jars'] = java_resources_jars

  if options.java_resources_jar_path:
    deps_info['java_resources_jar'] = options.java_resources_jar_path

  build_utils.write_json(config, options.build_config, only_if_changed=True)

  if options.depfile:
    build_utils.write_depfile(options.depfile, options.build_config, all_inputs,
                             add_pydeps=False)  # pydeps listed in GN.


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
