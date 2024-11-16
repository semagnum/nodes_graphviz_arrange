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

import bpy

from .autodetect import GraphvizAutodetect


class GraphvizAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    dot_path: bpy.props.StringProperty(
        name="dot.exe",
        subtype='FILE_PATH',
        default=GraphvizAutodetect.find_graphviz_or_empty_string(),
        description="Filepath of \"dot.exe\". Graphviz must be installed on the system to use this addon"
    )
    node_sep: bpy.props.FloatProperty(
        name="Node Spacing",
        default=28.0,
        description="Separation between nodes at the same level"
    )
    rank_sep: bpy.props.FloatProperty(
        name="Rank Spacing",
        default=28.0,
        description="Separation between levels"
    )

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "dot_path")
        row = layout.row()
        row.operator('wm.url_open', text='Visit graphviz.org', icon='INTERNET').url = "https://graphviz.org/"
        row.operator(GraphvizAutodetect.bl_idname, icon='VIEWZOOM')

        layout.separator()
        separator_layout = layout.column()
        separator_layout.prop(self, "node_sep", text='Spacing Node')
        separator_layout.prop(self, "rank_sep", text='Rank')