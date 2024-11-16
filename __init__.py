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

if "bpy" in locals():
    import importlib
    import os
    import sys
    import types


    def reload_package(package):
        assert (hasattr(package, '__package__'))
        fn = package.__file__
        fn_dir = os.path.dirname(fn) + os.sep
        module_visit = {fn}
        del fn

        def reload_recursive_ex(module):
            module_iter = (
                module_child
                for module_child in vars(module).values()
                if isinstance(module_child, types.ModuleType)
            )
            for module_child in module_iter:
                fn_child = getattr(module_child, '__file__', None)
                if (fn_child is not None) and fn_child.startswith(fn_dir) and fn_child not in module_visit:
                    # print('Reloading:', fn_child, 'from', module)
                    module_visit.add(fn_child)
                    reload_recursive_ex(module_child)

            importlib.reload(module)

        return reload_recursive_ex(package)


    reload_package(sys.modules[__name__])

import bpy

from . import arrange, autodetect, preferences

def menu_func(self, _context):
    self.layout.separator()
    self.layout.operator(arrange.GraphvizArrange.bl_idname)


classes = (
    arrange.GraphvizArrange,
    autodetect.GraphvizAutodetect,
    preferences.GraphvizAddonPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_node.append(menu_func)


def unregister():
    bpy.types.NODE_MT_node.remove(menu_func)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
