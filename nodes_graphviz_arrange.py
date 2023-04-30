# blender-nodes-graphviz/nodes_graphviz_arrange.py

from bpy.props import FloatProperty, StringProperty
from bpy.types import AddonPreferences, Operator
from pathlib import Path
import bpy
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

bl_info = {
    "name": "Arrange Nodes via Graphviz",
    "author": "Tachi",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "category": "Node",
}

DEFAULT_NODE_SEP = 28.0
DEFAULT_RANK_SEP = 28.0

DPI = 72.0
FONT_SIZE = 11

# Units copied from node_update_bases() in node_draw.cc.
WIDGET_UNIT = 20.0
NODE_DY = WIDGET_UNIT
NODE_SOCKDY = 0.1 * WIDGET_UNIT
NODE_DYS = 0.5 * WIDGET_UNIT

# Regexes.
EDGE_FROM = re.compile(r"node_(\d+):o(\d+)")
EDGE_TO = re.compile(r"node_(\d+):i(\d+)")
NODE_TITLE = re.compile(r"^(.*?)(?:\.\d{3})?$")


def logger(submodule=None):
    return logging.getLogger("nodes_graphviz_arrange" +
                             ("." + submodule if submodule is not None else ""))


def report_error(msg):
    bpy.context.window_manager.popup_menu(
        lambda self, context: self.layout.label(text=str(msg)),
        title="Error",
        icon='ERROR')


def write_line(line, f):
    logger("gv_input").debug(line)
    print(line, file=f)


def index_of_socket(sockets, query_socket):
    for index, socket in enumerate(sockets):
        if socket == query_socket:
            return index
    return 0


class GraphvizAutodetect(Operator):
    """Attempts to automatically find the installed Graphviz "dot" tool."""
    bl_idname = "node.graphviz_arrange_autodetect"
    bl_label = "Find Graphviz Automatically"

    def execute(self, context):
        result = self.find_graphviz()
        if result is None:
            self.report_that_autodetection_failed()
        else:
            context.preferences.addons[__name__].preferences.dot_path = result
        return {'FINISHED'}

    @classmethod
    def find_graphviz(klass):
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
    def require_graphviz(klass, context):
        dot_path = None
        if __name__ in context.preferences.addons:
            dot_path = context.preferences.addons[__name__].preferences.dot_path
        if dot_path is None:
            dot_path = GraphvizAutodetect.find_graphviz()
        if dot_path is None:
            GraphvizAutodetect.report_that_autodetection_failed()
        return dot_path

    @classmethod
    def report_that_autodetection_failed(klass):
        if sys.platform.startswith("linux"):
            report_error(textwrap.dedent("""\
                    Graphviz wasn't found. Please install it through your OS's package
                    manager and try again.
                    """))
        else:
            report_error(textwrap.dedent("""\
                    Graphviz wasn't found. If it's not installed, please install it from
                    http://graphviz.org/ and try again. If it is installed, you may need to specify its
                    location in the \"Node: Arrange Nodes via Graphviz\" addon preferences.
                    """))


class GraphvizOpenWebSite(Operator):
    """Opens http://graphviz.org/ in a Web browser."""
    bl_idname = "node.graphviz_arrange_open_website"
    bl_label = "Open http://graphviz.org/"

    def execute(self, context):
        bpy.ops.wm.url_open(url="http://graphviz.org/")
        return {'FINISHED'}


class GraphvizAddonPreferences(AddonPreferences):
    bl_idname = __name__

    dot_path: StringProperty(name="\"dot\" Tool Location",
                             subtype='FILE_PATH', default=GraphvizAutodetect.find_graphviz(),
                             description=textwrap.dedent("""\
        The location of \"dot.exe\". The addon will do its best to automatically detect this, but
        you may have to specify it manually if that fails. You can install Graphviz from
        http://graphviz.org/.
        """))
    node_sep: FloatProperty(
        name="Node Spacing", default=DEFAULT_NODE_SEP,
        description="Separation between nodes at the same level")
    rank_sep: FloatProperty(
        name="Rank Spacing", default=DEFAULT_RANK_SEP,
        description="Separation between levels")

    def draw(self, context):
        layout = self.layout

        help_column = layout.column(align=True)
        help_column.label(
            text="Graphviz needs to be installed on the system to use this addon.")
        if sys.platform.startswith("linux"):
            help_column.label(
                text="If it's not installed, install it through your OS's package manager.")
        else:
            help_column.label(
                text="If it's not installed, install it from http://graphviz.org/ below.")
        help_column.label(
            text="After installing Graphviz, click \"Find Graphviz Automatically\" to " +
            "automatically find it.")

        layout.prop(self, "dot_path")
        buttons_layout = layout.row()
        buttons_layout.operator("node.graphviz_arrange_open_website")
        buttons_layout.operator("node.graphviz_arrange_autodetect")

        layout.separator()
        separator_layout = layout.row()
        separator_layout.prop(self, "node_sep")
        separator_layout.prop(self, "rank_sep")


class GraphvizArrange(Operator):
    """Arranges nodes via Graphviz."""
    bl_idname = "node.graphviz_arrange"
    bl_label = "Arrange Nodes via Graphviz"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        node_editors = [
            area for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR']
        if len(node_editors) == 0:
            report_error("No node editor is open")
            return
        if len(node_editors) > 1:
            report_error("More than one node editor is open")
            return

        node_editor = node_editors[0]
        node_space = node_editor.spaces[0]
        node_tree = node_space.node_tree
        if node_tree.nodes.active:
            while node_tree.nodes.active != context.active_node:
                node_tree = node_tree.nodes.active.node_tree

        logger().info(node_editor.spaces[0].path.to_string)

        self.remove_passthrough_reroute_nodes(node_tree)
        dot_file = self.write_dot(node_tree)

        try:
            dot_path = GraphvizAutodetect.require_graphviz(context)
            if dot_path is not None:
                self.run_graphviz_and_arrange(node_tree, dot_path, dot_file)
                if event.shift:
                    self.show_rendered_graph(dot_path, dot_file)
        finally:
            os.unlink(dot_file.name)

        return {'FINISHED'}

    def remove_passthrough_reroute_nodes(self, node_tree):
        nodes_to_remove = set()

        reroute_nodes = {}
        for node in node_tree.nodes:
            if node.bl_idname == "NodeReroute":
                reroute_nodes[node.name] = {
                    "node": node,
                    "from": [],
                    "to": [],
                }

        # Build doubly-linked list.
        for link in node_tree.links:
            logger().info(link.from_node.name + " -> " + link.to_node.name)
            if link.to_node.name in reroute_nodes:
                reroute_nodes[link.to_node.name]["from"].append(
                    {"link": link, "socket": link.from_socket, "node": link.from_node})
            if link.from_node.name in reroute_nodes:
                reroute_nodes[link.from_node.name]["to"].append(
                    {"link": link, "socket": link.to_socket, "node": link.to_node})

        logger().info(repr(reroute_nodes))

        for info in reroute_nodes.values():
            from_count, to_count = len(info["from"]), len(info["to"])
            if from_count > 1 or to_count > 1 or (from_count == 0 and to_count == 0):
                continue

            from_socket, to_socket = None, None
            from_node, to_node = None, None

            for edge in info["from"]:
                from_socket = edge["socket"]
                from_node = edge["node"]
                node_tree.links.remove(edge["link"])
                if edge["node"].name in reroute_nodes:
                    reroute_nodes[edge["node"].name]["to"] = [
                        e for e in reroute_nodes[edge["node"].name]["to"] if
                        e["node"] != info["node"]]

            for edge in info["to"]:
                to_socket = edge["socket"]
                to_node = edge["node"]
                node_tree.links.remove(edge["link"])
                if edge["node"].name in reroute_nodes:
                    reroute_nodes[edge["node"].name]["from"] = [
                        e for e in reroute_nodes[edge["node"].name]["from"] if
                        e["node"] != info["node"]]

            if from_socket is not None and to_socket is not None:
                new_link = node_tree.links.new(from_socket, to_socket)
                for edge in info["from"]:
                    if edge["node"].name in reroute_nodes:
                        reroute_nodes[edge["node"].name]["to"].append(
                            {"link": new_link, "socket": to_socket, "node": to_node})
                for edge in info["to"]:
                    if edge["node"].name in reroute_nodes:
                        reroute_nodes[edge["node"].name]["from"].append(
                            {"link": new_link, "socket": from_socket, "node": from_node})

            nodes_to_remove.add(info["node"].name)

        for node in list(node_tree.nodes):
            if node.name in nodes_to_remove:
                node_tree.nodes.remove(node)

    def run_graphviz_and_arrange(self, node_tree, dot_path, dot_file):
        result = subprocess.run(
            [dot_path, "-Tplain-ext", dot_file.name], capture_output=True, text=True)
        if result.returncode != 0:
            report_error(result.stderr)
            return

        graphviz_output = result.stdout
        logger("gv_output").debug(graphviz_output)

        all_nodes = list(node_tree.nodes)

        for line in graphviz_output.splitlines():
            # FIXME: support quoted strings
            fields = line.split()
            match fields[0]:
                case "node":
                    graphviz_node_id = fields[1]
                    node_index = int(
                        graphviz_node_id[(graphviz_node_id.find('_') + 1):])
                    node = all_nodes[node_index]
                    node.location.x = (
                        float(fields[2]) - float(fields[4]) * 0.5) * DPI
                    node.location.y = (
                        float(fields[3]) + float(fields[5]) * 0.5) * DPI

                case "edge":
                    (from_node_index, from_socket) = EDGE_FROM.match(
                        fields[1]).groups()
                    (to_node_index, to_socket) = EDGE_TO.match(
                        fields[2]).groups()

                    from_node = all_nodes[int(from_node_index)]
                    to_node = all_nodes[int(to_node_index)]
                    from_socket = int(from_socket)
                    to_socket = int(to_socket)

                    control_point_count = int(fields[3])
                    if control_point_count == 4:
                        continue

                    # FIXME: O(n)
                    for link in node_tree.links:
                        if link.from_node == from_node and \
                            link.from_socket == from_node.outputs[from_socket] and \
                                link.to_node == to_node and \
                                link.to_socket == to_node.inputs[to_socket]:
                            node_tree.links.remove(link)
                            break

                    last_node, last_socket = from_node, from_socket
                    control_point_index = 2

                    while control_point_index < control_point_count - 2:
                        x_pos = float(fields[4 + control_point_index * 2 + 0])
                        y_pos = float(fields[4 + control_point_index * 2 + 1])

                        reroute_node = node_tree.nodes.new("NodeReroute")
                        reroute_node.location = (x_pos * DPI, y_pos * DPI)

                        node_tree.links.new(
                            last_node.outputs[last_socket], reroute_node.inputs[0])

                        last_node = reroute_node
                        last_socket = 0
                        control_point_index += 3

                    # Connect last.
                    node_tree.links.new(
                        last_node.outputs[last_socket], to_node.inputs[to_socket])

    def show_rendered_graph(self, dot_path, dot_file):
        pdf_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".pdf")

        result = subprocess.run(
            [dot_path, "-Tpdf", dot_file.name], stdout=pdf_file)
        if result.returncode != 0:
            report_error(result.stderr)
            return

        pdf_file.flush()
        pdf_file.close()

        # TODO: Non-Windows
        os.startfile(pdf_file.name)

    def write_dot(self, node_tree):
        theme = bpy.context.preferences.themes[0]

        dot_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".dot")

        try:
            write_line("digraph G {", dot_file)
            self.write_dot_options(dot_file)

            node_scale = float(node_tree.nodes[0].width) / \
                float(node_tree.nodes[0].dimensions[0])
            print("node_scale=" + str(node_scale))

            node_name_to_index = dict()
            for node_index, node in enumerate(node_tree.nodes):
                node_name_to_index[node.name] = node_index
                graphviz_node_width = float(node.dimensions[0] * node_scale)
                graphviz_node_height = float(node.dimensions[1] * node_scale)
                header_scale = (float(NODE_DY) + float(NODE_DYS) /
                                2.0) / graphviz_node_height
                formatted_options = self.format_graphviz_options({
                    "width": graphviz_node_width / DPI,
                    "height": graphviz_node_height / DPI,
                    "fillcolor": "%s;%f:%s" % (
                        self.blender_rgb_to_dot(
                            theme.node_editor.input_node),
                        header_scale,
                        self.blender_rgba_to_dot(
                            theme.node_editor.node_backdrop)
                    )
                })
                write_line("node_%d [%s, label=" %
                           (node_index, formatted_options), dot_file)
                write_line(
                    "<<table border=\"0\" cellborder=\"0\" cellpadding=\"0\" cellspacing=\"0\">",
                    dot_file)
                self.write_dot_rows(node, graphviz_node_width, graphviz_node_height,
                                    dot_file)
                write_line("</table>>]", dot_file)

            for link in node_tree.links:
                # Find which index each socket is.
                from_socket_index = index_of_socket(
                    link.from_node.outputs, link.from_socket)
                to_socket_index = index_of_socket(
                    link.to_node.inputs, link.to_socket)

                write_line("node_%d:o%d -> node_%d:i%d [%s];" % (
                    node_name_to_index[link.from_node.name],
                    from_socket_index,
                    node_name_to_index[link.to_node.name],
                    to_socket_index,
                    self.format_graphviz_options({})), dot_file)

            write_line("}", dot_file)
            dot_file.flush()
        except:
            dot_file.close()
            os.unlink(dot_file.name)
            raise

        dot_file.close()

        with open(dot_file.name, "r") as f:
            bpy.context.window_manager.clipboard = f.read()

        return dot_file

    def blender_rgb_to_dot(self, blender_color):
        return "#%02x%02x%02x" % tuple([round(x * 255.0) for x in blender_color])

    def blender_rgba_to_dot(self, blender_color):
        return "#%02x%02x%02x%02x" % tuple([round(x * 255.0) for x in blender_color])

    def write_dot_options(self, dot_file):
        preferences = bpy.context.preferences
        theme = preferences.themes[0]

        if __name__ in preferences.addons:
            addon_prefs = preferences.addons[__name__].preferences
            node_sep = addon_prefs.node_sep
            rank_sep = addon_prefs.rank_sep
        else:
            node_sep = DEFAULT_NODE_SEP
            rank_sep = DEFAULT_RANK_SEP

        node_options = {
            "fontcolor": self.blender_rgb_to_dot(theme.user_interface.wcol_regular.text),
            "fontsize": FONT_SIZE,
            "fixedsize": "shape",
            "gradientangle": "270",
            "margin": "0.0",
            "shape": "rect",
            "style": "filled,rounded",
            "penwidth": "2",
        }

        all_options = [
            ("node", node_options),
            ("graph", {
                "bgcolor": self.blender_rgba_to_dot(theme.user_interface.wcol_regular.item),
                "fontcolor": self.blender_rgb_to_dot(theme.user_interface.wcol_regular.text),
                "margin": 0,
                "nodesep": node_sep / DPI,
                "rankdir": "LR",
                "ranksep": rank_sep / DPI,
                "splines": "polyline",
            }),
            ("edge", {
                "arrowhead": "none",
                "color": self.blender_rgba_to_dot(theme.node_editor.wire),
                "penwidth": 4,
            })
        ]

        full_font_path = preferences.view.font_path_ui
        if os.name == "nt":
            self.write_dot_font_options_win32(node_options, full_font_path)

        for (section, options) in all_options:
            formatted_options = self.format_graphviz_options(options)
            write_line("%s[%s]" % (section, formatted_options), dot_file)

    def format_graphviz_options(self, options):
        string = ""
        first = True
        for key, value in options.items():
            if first:
                first = False
            else:
                string += ","
            string += key + "=" + json.dumps(str(value))
        return string

    # This is an unfortunately-complex way to grab the font family from the Blender UI font if it's
    # available to Graphviz's fontconfig library.
    #
    # This isn't actually needed to get the layout right, but it makes the PDF look a little nicer.
    # Admittedly this is overengineered.
    def write_dot_font_options_win32(self, node_options, full_font_path):
        from ctypes import c_int, c_wchar, cdll, windll, POINTER, Structure
        from ctypes.wintypes import BYTE, DWORD, LONG, LPARAM, LPVOID
        import ctypes

        node_options["fontname"] = "Verdana"

        if full_font_path == "":
            return

        full_font_path = Path(full_font_path)
        with open(full_font_path, mode='rb') as font_file:
            font_content = font_file.read()

        gdi32, user32 = windll.gdi32, windll.user32
        msvcrt = cdll.msvcrt

        class LOGFONTW(Structure):
            _fields_ = [
                ('lfHeight', LONG),
                ('lfWidth', LONG),
                ('lfEscapement', LONG),
                ('lfOrientation', LONG),
                ('lfWeight', LONG),
                ('lfItalic', BYTE),
                ('lfUnderline', BYTE),
                ('lfStrikeOut', BYTE),
                ('lfCharSet', BYTE),
                ('lfOutPrecision', BYTE),
                ('lfClipPrecision', BYTE),
                ('lfQuality', BYTE),
                ('lfPitchAndFamily', BYTE),
                ('lfFaceName', c_wchar * 32)
            ]

        gdi32.CreateFontIndirectW.argtypes = [POINTER(LOGFONTW)]
        gdi32.GetFontData.argtypes = [LPVOID, DWORD, DWORD, LPVOID, DWORD]

        FONTENUMPROCW = ctypes.WINFUNCTYPE(
            c_int, POINTER(LOGFONTW), LPVOID, DWORD, LPARAM)

        TRUETYPE_FONTTYPE = 0x4

        def iterate_fonts(logfont, text_metrics, font_type, lparam):
            nonlocal font_content, gdi32, hdc, msvcrt, node_options, user32, TRUETYPE_FONTTYPE

            if (font_type & TRUETYPE_FONTTYPE) == 0:
                return 1
            hfont = gdi32.CreateFontIndirectW(logfont)
            if hfont is None:
                return 1
            try:
                gdi32.SelectObject(hdc, hfont)

                this_font_size = gdi32.GetFontData(hdc, 0, 0, None, 0)
                if this_font_size != len(font_content):
                    return 1
                this_font_content = ctypes.create_string_buffer(this_font_size)
                if gdi32.GetFontData(hdc, 0, 0, this_font_content, this_font_size) != \
                        this_font_size:
                    return 1

                if msvcrt.memcmp(this_font_content, font_content, this_font_size) != 0:
                    return 1

                node_options["fontname"] = str(logfont.contents.lfFaceName)
                return 0
            finally:
                gdi32.DeleteObject(hfont)

        hdc = user32.GetDC(None)
        try:
            gdi32.EnumFontFamiliesExW(
                hdc, None, FONTENUMPROCW(iterate_fonts), 0, 0)
        finally:
            user32.ReleaseDC(hdc)

    def write_dot_rows(self,
                       node,
                       graphviz_node_width,
                       graphviz_node_height,
                       dot_file):
        table_width = graphviz_node_width
        table_height = graphviz_node_height

        current_y = 0

        # Write node title.
        # TODO: downward-pointing chevron as image?
        title = node.bl_label if node.label == "" else node.label
        current_y += self.write_dot_row(dot_file=dot_file,
                                        label="    " + title,
                                        cell_width=table_width,
                                        cell_height=NODE_DY)
        current_y += self.write_dot_row(dot_file=dot_file,
                                        label=" ",
                                        cell_width=table_width,
                                        cell_height=NODE_DYS / 2.0)

        visible_outputs, visible_inputs = [], []
        for output_index, output in enumerate(node.outputs):
            if output.enabled:
                visible_outputs.append((output_index, output))
        for input_index, input in enumerate(node.inputs):
            if not input.enabled:
                continue
            height = NODE_DY
            if input.type == 'VECTOR' and not input.is_linked and not input.hide_value:
                height += NODE_DY * 3.0
            visible_inputs.append(
                {"input": input, "index": input_index, "height": height})

        for visible_output_index, (output_index, output) in enumerate(visible_outputs):
            current_y += self.write_dot_row(dot_file=dot_file,
                                            label=output.name + "    ",
                                            cell_width=table_width,
                                            cell_height=NODE_DY,
                                            align="right",
                                            port="o%d" % output_index)
            if visible_output_index < len(visible_outputs) - 1:
                current_y += self.write_dot_row(dot_file=dot_file,
                                                label=" ",
                                                cell_width=table_width,
                                                cell_height=NODE_SOCKDY)

        # Skip to end.
        spacer_height = table_height - current_y
        if len(visible_inputs) > 0:
            spacer_height -= sum([input["height"] for input in visible_inputs])
            spacer_height -= (len(visible_inputs) - 1) * NODE_SOCKDY
            spacer_height -= NODE_DYS / 2   # End space.
        self.write_dot_row(dot_file=dot_file,
                           label="",
                           cell_width=table_width,
                           cell_height=spacer_height)

        for visible_input_index, visible_input in enumerate(visible_inputs):
            self.write_dot_row(dot_file=dot_file,
                               label="    " + visible_input["input"].name,
                               port="i%d" % visible_input["index"],
                               cell_width=table_width,
                               cell_height=NODE_DY)
            if visible_input["height"] > NODE_DY:
                self.write_dot_row(dot_file=dot_file,
                                   label="",
                                   cell_width=table_width,
                                   cell_height=visible_input["height"] - NODE_DY)
            if visible_input_index < len(visible_inputs) - 1:
                self.write_dot_row(dot_file=dot_file,
                                   label=" ",
                                   cell_width=table_width,
                                   cell_height=NODE_SOCKDY)

        if len(visible_inputs) > 0:
            self.write_dot_row(dot_file=dot_file, label="", cell_width=table_width,
                               cell_height=NODE_DYS / 2.0)

    def write_dot_row(self,
                      dot_file,
                      label,
                      cell_width,
                      cell_height,
                      align="left",
                      port=None):
        options = {
            "height": cell_height,
            "width": cell_width,
            "align": align,
            "fixedsize": "true",
            "valign": "bottom",
        }

        if port is not None:
            options["port"] = port

        string = "<tr>"
        string += "<td"
        for key, value in options.items():
            string += " " + key + "=" + json.dumps(str(value))
        string += ">%s</td></tr>" % label
        write_line(string, dot_file)

        return cell_height


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(GraphvizArrange.bl_idname)


def register():
    bpy.utils.register_class(GraphvizArrange)
    bpy.utils.register_class(GraphvizAutodetect)
    bpy.utils.register_class(GraphvizOpenWebSite)
    bpy.utils.register_class(GraphvizAddonPreferences)
    bpy.types.NODE_MT_node.append(menu_func)


def unregister():
    bpy.utils.unregister_class(GraphvizArrange)
    bpy.utils.unregister_class(GraphvizAutodetect)
    bpy.utils.unregister_class(GraphvizOpenWebSite)
    bpy.utils.unregister_class(GraphvizAddonPreferences)


if __name__ == "__main__":
    register()
