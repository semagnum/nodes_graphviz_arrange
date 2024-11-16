# Copyright 2024 Tachi
# THIS FILE HAS BEEN MODIFIED FROM THE ORIGINAL
# Including refactors and bugfixes to support Blender 4.2+
#
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

import os
import shutil
import sys
from pathlib import Path

import bpy


def report_error(msg):
    bpy.context.window_manager.popup_menu(
        lambda self, context: self.layout.label(text=str(msg)),
        title="Error",
        icon='ERROR')


class GraphvizAutodetect(bpy.types.Operator):
    """Attempts to automatically find the installed Graphviz "dot" tool"""
    bl_idname = "node.graphviz_arrange_autodetect"
    bl_label = "Auto-detect Graphviz"

    def execute(self, context):
        result = self.find_graphviz()
        if result is None:
            self.report_that_autodetection_failed()
        else:
            context.preferences.addons[__name__].preferences.dot_path = result
        return {'FINISHED'}

    @classmethod
    def find_graphviz(cls):
        # Looks in the Uninstall sections of the Windows registry to try to locate Graphviz.
        def find_in_windows_registry():
            from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, REG_SZ
            import winreg

            GRAPHVIZ_REGISTRY_LOCATIONS = [
                (HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Graphviz"),
                (HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Graphviz"),
                (HKEY_CURRENT_USER,
                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Graphviz"),
            ]

            for hive, key_path in GRAPHVIZ_REGISTRY_LOCATIONS:
                try:
                    key = winreg.OpenKey(hive, key_path)
                    value, value_type = winreg.QueryValueEx(
                        key, "UninstallString")
                    if value_type != REG_SZ:
                        continue
                    uninstall_exe_path = Path(value)
                    dot_path = uninstall_exe_path.with_name("dot.exe")
                    if dot_path.exists():
                        return dot_path
                except OSError:
                    continue

            return None

        def find_in_path():
            return shutil.which("dot")

        if os.name == "nt":
            dot_path = find_in_windows_registry()
            if dot_path is not None:
                return dot_path
        return find_in_path()

    @classmethod
    def find_graphviz_or_empty_string(cls):
        dot_path = GraphvizAutodetect.find_graphviz()
        return "" if dot_path is None else dot_path

    @classmethod
    def require_graphviz(cls, context):
        dot_path = None
        if __name__ in context.preferences.addons:
            dot_path = context.preferences.addons[__name__].preferences.dot_path
        if dot_path is None:
            dot_path = GraphvizAutodetect.find_graphviz()
        if dot_path is None:
            GraphvizAutodetect.report_that_autodetection_failed()
        return dot_path

    @classmethod
    def report_that_autodetection_failed(cls):
        if sys.platform.startswith("linux"):
            msg = ("Graphviz wasn't found. Please install it through "
                         "your OS's package manager and try again.")
        else:
            msg = ("Graphviz wasn't found. "
                         "If it's not installed, please install it from http://graphviz.org/ and try again. "
                         "If it is installed, you may need to specify its location "
                         "in the \"Node: Arrange Nodes via Graphviz\" addon preferences.")

        report_error(msg)
