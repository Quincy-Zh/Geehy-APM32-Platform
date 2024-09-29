# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os
import string

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
mcu = board.get("build.mcu", "")
MCU_FAMILY =  mcu[0:7]
PRODUCT_LINE = board.get("build.product_line", "")
assert PRODUCT_LINE, "Missing MCU or Product Line field"

env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-geehy-" + mcu[0:7])
assert os.path.isdir(FRAMEWORK_DIR)

def get_linker_script():
    # 
    default_ldscript = os.path.join(
        FRAMEWORK_DIR, "Libraries", "Device", "Geehy", "APM32F4xx", "Source", "gcc", "APM32F4xxx%s_FLASH.ld" % mcu[10].upper())

    return default_ldscript

def prepare_startup_file(src_path):
    startup_file = os.path.join(src_path, "gcc", "startup_%s.S" % PRODUCT_LINE.lower())
    print("startup_file:", startup_file)
    # Change file extension to uppercase:
    if not os.path.isfile(startup_file) and os.path.isfile(startup_file[:-2] + ".s"):
        os.rename(startup_file[:-2] + ".s", startup_file)
    if not os.path.isfile(startup_file):
        print("Warning! Cannot find the default startup file for %s. "
              "Ignore this warning if the startup code is part of your project." % mcu)


#
# Allow using custom linker scripts
#
if not board.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=get_linker_script())

#
# Prepare build environment
#

# The final firmware is linked against standard library with two specifications:
# nano.specs - link against a reduced-size variant of libc
# nosys.specs - link against stubbed standard syscalls

env.Append(
    CPPPATH=[
        os.path.join(FRAMEWORK_DIR, "Libraries", "CMSIS", "Include"),
        os.path.join(FRAMEWORK_DIR, "Libraries", "Device", "Geehy", "APM32F4xx", "Include"),
        os.path.join(FRAMEWORK_DIR, "Libraries", "APM32F4xx_StdPeriphDriver", "inc")
    ],


    LINKFLAGS=[
        "--specs=nano.specs",
        "--specs=nosys.specs"
    ]
)


env.BuildSources(
    os.path.join("$BUILD_DIR", "FrameworkHALDriver"),
    os.path.join(
        FRAMEWORK_DIR,
        "Libraries",
        MCU_FAMILY.upper() + "xx_StdPeriphDriver",
    ),
    src_filter="+<*> -<src/*usb*.c>",
)

#
# Compile CMSIS sources
#

sources_path = os.path.join(FRAMEWORK_DIR, "Libraries", "Device", "Geehy", "APM32F4xx", "Source")
prepare_startup_file(sources_path)

env.BuildSources(
    os.path.join("$BUILD_DIR", "FrameworkCMSIS"), 
    sources_path,
    src_filter=[
        "-<*>",
        "+<system_%sxx.c>" % mcu[0:7],
        "+<gcc/startup_%s.S>" % PRODUCT_LINE.lower(),
    ]
)
