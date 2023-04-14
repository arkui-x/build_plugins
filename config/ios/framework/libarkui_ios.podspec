# Copyright (c) 2023 Huawei Device Co., Ltd.
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

#
# NOTE: This podspec is NOT to be published. It is only used as a local source!
#

Pod::Spec.new do |s|
  s.name             = 'libarkui_ios'
  s.version          = '1.0.0'
  s.summary          = 'The ArkUI-X project extends the ArkUI framework to multiple OS platforms.'
  s.description      = <<-DESC
  The ArkUI-X project extends the ArkUI framework to multiple OS platforms.
  This enables developers to use one main set of code to develop applications for multiple OS platforms.
                       DESC
  s.homepage         = 'https://arkui-x.cn'
  s.license          = { :type => 'Apache' }
  s.author           = { 'ArkUI Dev Team' => 'contact@mail.arkui-x.cn' }
  s.source           = { :git => 'https://gitee.com/arkui-x', :tag => s.version.to_s }
  s.ios.deployment_target = '8.0'
  s.vendored_frameworks = 'libarkui_ios.framework'
end
