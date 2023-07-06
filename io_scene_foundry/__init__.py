# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2023 Crisp
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####

# Don't edit the version or build version here or it will break CI
# Need to do this because of Blender parsing the plugin init code instead of actually executing it when getting bl_info

import ctypes
import bpy
from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.app.handlers import persistent
import os

from io_scene_foundry.utils.nwo_utils import (
    formalise_game_version,
    get_ek_path,
    valid_nwo_asset,
)

bl_info = {
    "name": "Foundry - Halo Blender Creation Kit",
    "author": "Crisp",
    "version": (0, 9, 0),
    "blender": (3, 6, 0),
    "location": "File > Export",
    "description": "Asset Exporter and Toolset for Halo Reach, Halo 4, and Halo 2 Aniversary Multiplayer: BUILD_VERSION_STR",
    "warning": "",
    "wiki_url": "https://c20.reclaimers.net/general/tools/foundry",
    "support": "COMMUNITY",
    "category": "Export",
}

from . import tools
from . import ui
from . import export
from . import managed_blam
from . import keymap
from . import icons


modules = [
    tools,
    ui,
    managed_blam,
    export,
    keymap,
    icons,
]


class HREKLocationPath(Operator):
    """Set the path to your Halo Reach Editing Kit"""

    bl_idname = "nwo.hrek_path"
    bl_label = "Select Folder"
    bl_options = {"REGISTER"}

    filter_folder: BoolProperty(
        default=True,
        options={"HIDDEN"},
    )

    directory: StringProperty(
        name="hrek_path",
        description="Set the path to your Halo Reach Editing Kit",
    )

    def execute(self, context):
        context.preferences.addons[
            __package__
        ].preferences.hrek_path = self.directory.strip('"\\')

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class H4EKLocationPath(Operator):
    """Set the path to your Halo 4 Editing Kit"""

    bl_idname = "nwo.h4ek_path"
    bl_label = "Select Folder"
    bl_options = {"REGISTER"}

    filter_folder: BoolProperty(
        default=True,
        options={"HIDDEN"},
    )

    directory: StringProperty(
        name="h4ek_path",
        description="Set the path to your Halo 4 Editing Kit",
    )

    def execute(self, context):
        context.preferences.addons[
            __package__
        ].preferences.h4ek_path = self.directory.strip('"\\')

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class H2AMPEKLocationPath(Operator):
    """Set the path to your Halo 2 Anniversary Multiplayer Editing Kit"""

    bl_idname = "nwo.h2aek_path"
    bl_label = "Select Folder"
    bl_options = {"REGISTER"}

    filter_folder: BoolProperty(
        default=True,
        options={"HIDDEN"},
    )

    directory: StringProperty(
        name="h2aek_path",
        description="Set the path to your Halo 2 Anniversary Multiplayer Editing Kit",
    )

    def execute(self, context):
        context.preferences.addons[
            __package__
        ].preferences.h2aek_path = self.directory.strip('"\\')

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


class ToolkitLocationPreferences(AddonPreferences):
    bl_idname = __package__

    def clean_hrek_path(self, context):
        self["hrek_path"] = self["hrek_path"].strip('"\\')

    hrek_path: StringProperty(
        name="HREK Path",
        description="Specify the path to your Halo Reach Editing Kit folder containing tool / tool_fast",
        default="",
        update=clean_hrek_path,
    )

    def clean_h4ek_path(self, context):
        self["h4ek_path"] = self["h4ek_path"].strip('"\\')

    h4ek_path: StringProperty(
        name="H4EK Path",
        description="Specify the path to your Halo 4 Editing Kit folder containing tool / tool_fast",
        default="",
        update=clean_h4ek_path,
    )

    def clean_h2aek_path(self, context):
        self["h2aek_path"] = self["h2aek_path"].strip('"\\')

    h2aek_path: StringProperty(
        name="H2AMPEK Path",
        description="Specify the path to your Halo 2 Anniversary MP Editing Kit folder containing tool / tool_fast",
        default="",
        update=clean_h2aek_path,
    )

    tool_type: EnumProperty(
        name="Tool Type",
        description="Specify whether the add on should use Tool or Tool Fast",
        default="tool_fast",
        items=[("tool_fast", "Tool Fast", ""), ("tool", "Tool", "")],
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Halo Reach Editing Kit Path")
        row = layout.row(align=True)
        row.prop(self, "hrek_path", text="")
        row.operator("nwo.hrek_path", text="", icon='FILE_FOLDER')
        row = layout.row(align=True)
        row.label(text="Halo 4 Editing Kit Path")
        row = layout.row(align=True)
        row.prop(self, "h4ek_path", text="")
        row.operator("nwo.h4ek_path", text="", icon='FILE_FOLDER')
        row = layout.row(align=True)
        row.label(text="Halo 2 Anniversary Multiplayer Editing Kit Path")
        row = layout.row(align=True)
        row.prop(self, "h2aek_path", text="")
        row.operator("nwo.h2aek_path", text="", icon='FILE_FOLDER')
        row = layout.row(align=True)
        row.label(text="Tool Version")
        row = layout.row(align=True)
        row.prop(self, "tool_type", expand=True)


def msgbus_callback(context):
    try:
        ob = context.object
        if context.object:
            highlight = ob.data.nwo.highlight
            if highlight and context.mode == "EDIT_MESH":
                bpy.ops.nwo.face_layer_color_all(enable_highlight=highlight)
    except:
        pass


def subscribe(owner):
    subscribe_to = bpy.types.Object, "mode"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=owner,
        args=(bpy.context,),
        notify=msgbus_callback,
        options={
            "PERSISTENT",
        },
    )


@persistent
def load_set_output_state(dummy):
    file_path = os.path.join(bpy.app.tempdir, "foundry_output.txt")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            state = f.read()

        if state == "True":
            bpy.context.scene.nwo_export.show_output = True
        else:
            bpy.context.scene.nwo_export.show_output = False
    else:
        bpy.context.scene.nwo_export.show_output = True


@persistent
def load_handler(dummy):
    if not bpy.app.background:
        # Set game version from file
        context = bpy.context
        game_version_txt_path = os.path.join(bpy.app.tempdir, "game_version.txt")
        # only do this if the scene is not an asset
        if not valid_nwo_asset(context) and os.path.exists(game_version_txt_path):
            with open(game_version_txt_path, "r") as temp_file:
                context.scene.nwo.game_version = temp_file.read()

        # set output to on
        # context.scene.nwo_export.show_output = True

        # run ManagedBlam on startup if enabled
        if context.scene.nwo.mb_startup:
            bpy.ops.managed_blam.init()

        # create warning if current game_version is incompatible with loaded managedblam.dll
        if os.path.exists(os.path.join(bpy.app.tempdir, "blam.txt")):
            with open(os.path.join(bpy.app.tempdir, "blam.txt"), "r") as blam_txt:
                mb_path = blam_txt.read()

            if not mb_path.startswith(get_ek_path()):
                game = formalise_game_version(context.scene.nwo.game_version)
                result = ctypes.windll.user32.MessageBoxW(
                    0,
                    f"{game} incompatible with loaded ManagedBlam version: {mb_path + '.dll'}. Please restart Blender or switch to a {game} asset.\n\nClose Blender?",
                    f"ManagedBlam / Game Mismatch",
                    4,
                )
                if result == 6:
                    bpy.ops.wm.quit_blender()

        # like and subscribe
        subscription_owner = object()
        subscribe(subscription_owner)

        file_path = os.path.join(bpy.app.tempdir, "foundry_output.txt")
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("True")


@persistent
def get_temp_settings(dummy):
    """Restores settings that the user created on export. Necesssary due to the way the exporter undos changes made during scene export"""
    scene = bpy.context.scene
    nwo = scene.nwo
    nwo_export = scene.nwo_export
    temp_file_path = os.path.join(bpy.app.tempdir, "nwo_scene_settings.txt")
    if os.path.exists(temp_file_path):
        with open(temp_file_path, "r") as temp_file:
            settings = temp_file.readlines()

        settings = [line.strip() for line in settings]
        scene.nwo_halo_launcher.sidecar_path = settings[0]
        nwo.game_version = settings[1]
        nwo.asset_type = settings[2]
        nwo.output_biped = True if settings[3] == "True" else False
        nwo.output_crate = True if settings[4] == "True" else False
        nwo.output_creature = True if settings[5] == "True" else False
        nwo.output_device_control = True if settings[6] == "True" else False
        nwo.output_device_dispenser = True if settings[7] == "True" else False
        nwo.output_device_machine = True if settings[8] == "True" else False
        nwo.output_device_terminal = True if settings[9] == "True" else False
        nwo.output_effect_scenery = True if settings[10] == "True" else False
        nwo.output_equipment = True if settings[11] == "True" else False
        nwo.output_giant = True if settings[12] == "True" else False
        nwo.output_scenery = True if settings[13] == "True" else False
        nwo.output_vehicle = True if settings[14] == "True" else False
        nwo.output_weapon = True if settings[15] == "True" else False
        nwo_export.show_output = True if settings[16] == "True" else False
        nwo_export.lightmap_all_bsps = True if settings[17] == "True" else False
        nwo_export.lightmap_quality = settings[18]
        nwo_export.lightmap_quality_h4 = settings[19]
        nwo_export.lightmap_region = settings[20]
        nwo_export.lightmap_specific_bsp = settings[21]
        nwo_export.lightmap_structure = True if settings[22] == "True" else False
        nwo_export.import_force = True if settings[23] == "True" else False
        nwo_export.import_verbose = True if settings[24] == "True" else False
        nwo_export.import_draft = True if settings[25] == "True" else False
        nwo_export.import_seam_debug = True if settings[26] == "True" else False
        nwo_export.import_skip_instances = True if settings[27] == "True" else False
        nwo_export.import_decompose_instances = (
            True if settings[28] == "True" else False
        )
        nwo_export.import_surpress_errors = True if settings[29] == "True" else False
        nwo_export.import_lighting = True if settings[30] == "True" else False
        nwo_export.import_meta_only = True if settings[31] == "True" else False
        nwo_export.import_disable_hulls = True if settings[32] == "True" else False
        nwo_export.import_disable_collision = True if settings[33] == "True" else False
        nwo_export.import_no_pca = True if settings[34] == "True" else False
        nwo_export.import_force_animations = True if settings[35] == "True" else False

        os.remove(temp_file_path)


def fix_icons():
    icons.icons_activate()

def register():
    bpy.utils.register_class(ToolkitLocationPreferences)
    bpy.utils.register_class(HREKLocationPath)
    bpy.utils.register_class(H4EKLocationPath)
    bpy.utils.register_class(H2AMPEKLocationPath)
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.load_post.append(load_set_output_state)
    bpy.app.handlers.undo_post.append(get_temp_settings)
    for module in modules:
        module.register()

    bpy.app.timers.register(fix_icons, first_interval=0.04)


def unregister():
    try:
        bpy.app.timers.unregister(fix_icons)
    except:
        pass
    
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.load_post.append(load_set_output_state)
    bpy.app.handlers.undo_post.remove(get_temp_settings)
    bpy.utils.unregister_class(ToolkitLocationPreferences)
    bpy.utils.unregister_class(HREKLocationPath)
    bpy.utils.unregister_class(H4EKLocationPath)
    bpy.utils.unregister_class(H2AMPEKLocationPath)
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
