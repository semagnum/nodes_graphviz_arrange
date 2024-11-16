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