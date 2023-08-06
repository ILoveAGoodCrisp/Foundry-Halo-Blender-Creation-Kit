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

from io_scene_foundry.utils import nwo_globals
from io_scene_foundry.managed_blam.mb_utils import get_bungie, get_tag_and_path
from io_scene_foundry.utils.nwo_utils import (
    dot_partition,
    get_asset_path,
    get_tags_path,
    get_valid_shader_name,
    managed_blam_active,
    not_bungie_game,
    print_warning,
)
import bpy
import os
from bpy.types import Context, Operator, OperatorProperties
from bpy.props import StringProperty
from io_scene_foundry.utils.nwo_utils import get_ek_path
import sys
import subprocess
import ctypes

class ManagedBlam():
    def __init__(self):
        if not managed_blam_active():
            bpy.ops.managed_blam.init()

        self.path = ""
        self.read_only = False

    def get_path(self): # stub
        return ""

    def tag_edit(self, tag): # stub
        pass

    def tag_helper(self):
        self.tag_is_new = False
        if not self.path:
            self.path = self.get_path()

        self.system_path = get_tags_path() + self.path

        self.Bungie = get_bungie()
        self.tag, self.tag_path = get_tag_and_path(self.Bungie, self.path)
        tag = self.tag
        try:
            if os.path.exists(self.system_path):
                tag.Load(self.tag_path)
            elif not self.read_only:
                self.tag_is_new = True
                tag.New(self.tag_path)
            else:
                print("Read only mode but tag path does not exist")
            if self.read_only:
                self.tag_read(tag)
            else:
                self.tag_edit(tag)
                tag.Save()

        finally:
            tag.Dispose()


class ManagedBlam_Init(Operator):
    """Initialises Managed Blam and locks the currently selected game"""

    bl_idname = "managed_blam.init"
    bl_label = "Managed Blam"
    bl_options = {"REGISTER"}
    bl_description = "Initialises Managed Blam and locks the currently selected game"

    install_only : bpy.props.BoolProperty()

    @classmethod
    def description(cls, context: Context, properties: OperatorProperties) -> str:
        if properties.install_only:
            return "Installs pythonnet for Blender's python library. Pythonnet includes the clr module necessary for Foundry to be able to talk to the Halo tag API - Managedblam"

    def callback(self):
        pass

    def execute(self, context):
        # append the blender python module path to the sys PATH
        packages_path = os.path.join(sys.exec_prefix, "lib", "site-packages")
        sys.path.append(packages_path)
        # Get the reference to ManagedBlam.dll
        mb_path = os.path.join(get_ek_path(), "bin", "managedblam")

        # Check that a path to ManagedBlam actually exists
        if not os.path.exists(f"{mb_path}.dll"):
            print_warning("Could not find path to ManagedBlam.dll")
            return {"CANCELLED"}

        # Logic for importing the clr module and importing Bungie/Corinth from ManagedBlam.dll
        try:
            import clr

            try:
                clr.AddReference(mb_path)
                if context.scene.nwo.game_version == "reach":
                    import Bungie
                else:
                    import Corinth as Bungie

            except:
                print("Failed to add reference to ManagedBlam")
                return {"CANCELLED"}
        except:
            if not self.install_only:
                print("Couldn't find clr module, attempting pythonnet install")
                install = ctypes.windll.user32.MessageBoxW(
                    0,
                    "ManagedBlam requires the pythonnet module to be installed for Blender.\n\nInstall pythonnet now?",
                    f"Pythonnet Install Required",
                    4,
                )
                if install != 6:
                    return {"CANCELLED"}
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "pythonnet"]
                )
                print("Succesfully installed necessary modules")

                shutdown = ctypes.windll.user32.MessageBoxW(
                    0,
                    "Pythonnet module installed for Blender. Please restart Blender to use ManagedBlam.\n\nClose Blender now?",
                    f"Pythonnet Installed for Blender",
                    4,
                )
                if shutdown != 6:
                    return {"CANCELLED"}
                bpy.ops.wm.quit_blender()

            except:
                print("Failed to install pythonnet")
                return {"CANCELLED"}
            else:
                if self.install_only:
                    self.report({'INFO'}, "ManagedBlam Setup Complete")
                return {"FINISHED"}

        else:
            nwo_globals.clr_installed = True
            if not self.install_only:
                # Initialise ManagedBlam
                print("Initialising ManagedBlam...")
                try:
                    startup_parameters = Bungie.ManagedBlamStartupParameters()
                    Bungie.ManagedBlamSystem.Start(
                        get_ek_path(), self.callback(), startup_parameters
                    )
                except:
                    print("ManagedBlam already initialised. Skipping")
                    return {"CANCELLED"}
                else:
                    # print("Success!")
                    nwo_globals.mb_active = True
                    nwo_globals.mb_path = mb_path

            return {"FINISHED"}
            

class ManagedBlamTag(Operator):
    bl_options = {"REGISTER"}

    path : StringProperty()

    def get_path(self): # stub
        return ""

    def tag_edit(self, context, tag): # stub
        pass

    def execute(self, context):
        if not self.path:
            self.path = self.get_path()

        self.system_path = get_tags_path() + self.path

        self.Bungie = get_bungie(self.report)
        self.tag, self.tag_path = get_tag_and_path(self.Bungie, self.path)
        tag = self.tag
        try:
            if os.path.exists(self.system_path):
                tag.Load(self.tag_path)
            else:
                tag.New(self.tag_path)

            self.tag_edit(context, tag)
            tag.Save()

        finally:
            tag.Dispose()

        return {'FINISHED'}

class ManagedBlam_Close(Operator):
    """Closes Managed Blam"""
    bl_idname = "managed_blam.close"
    bl_label = "Managed Blam Close"
    bl_options = {"REGISTER"}
    bl_description = "Closes Managed Blam"

    def execute(self, context):
        Bungie = get_bungie(self.report)
        Bungie.ManagedBlamSystem.Stop()
        return {"FINISHED"}
    
class ManagedBlamGetGlobalMaterials(ManagedBlam):
    def __init__(self):
        super().__init__()
        self.read_only = True
        self.tag_helper()

    def get_path(self):
        globals_path = os.path.join("globals", "globals.globals")
        return globals_path
    
    def tag_read(self, tag):
        global_materials = []
        blocks = tag.SelectField("Block:materials")
        for element in blocks:
            field = element.SelectField("name")
            global_materials.append(field.GetStringData())

        self.global_materials = global_materials

class ManagedBlamGetNodeOrder(ManagedBlam):
    def __init__(self, tag_path, is_animation_graph=False):
        super().__init__()
        self.read_only = True
        self.path = tag_path
        self.is_anim_graph = is_animation_graph
        self.tag_helper()
    
    def tag_read(self, tag):
        self.nodes = []
        if self.is_anim_graph:
            nodes_block = tag.SelectField("Struct:definitions[0]/Block:skeleton nodes")
        else:
            nodes_block = tag.SelectField("Block:nodes")

        for element in nodes_block:
            node_name = element.SelectField("name").GetStringData()
            self.nodes.append(node_name)

class ManagedBlamGetModelFromObject(ManagedBlam):
    def __init__(self, tag_path):
        super().__init__()
        self.read_only = True
        self.path = tag_path
        self.tag_helper()
    
    def tag_read(self, tag):
        # Find the object struct
        first_struct = tag.Fields[0]
        if first_struct.DisplayName == "object":
            object_struct = first_struct
        else:
            object_struct = first_struct.Elements[0].Fields[0]

        model_field = tag.SelectField(f"{object_struct.FieldPath}/Reference:model")
        model_path = model_field.Path
        if model_path:
            self.model_tag_path = model_path.RelativePathWithExtension
        else:
            print(f"{self.path} has no model reference")
            self.model_tag_path = None

class ManagedBlamGetModelVariants(ManagedBlam):
    def __init__(self, tag_path):
        super().__init__()
        self.read_only = True
        self.path = tag_path
        self.tag_helper()
    
    def tag_read(self, tag):
        self.variants = []
        # Select the variants block
        variants_block = tag.SelectField("Block:variants")
        for element in variants_block:
            var = element.SelectField("name").GetStringData()
            self.variants.append(var)

class ManagedBlamNewShader(ManagedBlam):
    def __init__(self, blender_material, is_reach):
        super().__init__()
        self.blender_material = blender_material
        self.is_reach = is_reach
        self.tag_helper()

    def get_path(self):
        asset_path = get_asset_path()
        shaders_dir = os.path.join(asset_path, "shaders" if self.is_reach else "materials")
        shader_name = get_valid_shader_name(self.blender_material)
        tag_ext = ".shader" if self.is_reach else ".material"
        shader_path = os.path.join(shaders_dir, shader_name + tag_ext)

        return shader_path

    def tag_edit(self, tag):

        # field = tag.SelectField("Struct:render_method[0]/Block:parameters")
        # parameters = field
        # for index, p in enumerate(self.parameters):
        #     parameters.AddElement()

        #     field = tag.SelectField(f"Struct:render_method[0]/Block:parameters[{index}]/StringId:parameter name")
        #     name = field
        #     type.SetStringData(p.name)

        #     field = tag.SelectField(f"Struct:render_method[0]/Block:parameters[{index}]/LongEnum:parameter type")
        #     type = field
        #     type.SetStringData(p.name)

        #     field = tag.SelectField(f"Struct:render_method[0]/Block:parameters[{index}]/Reference:bitmap")
        #     bitmap = field
        #     bitmap.Reference.Path = get_tag_and_path(Bungie, p.bitmap)
        pass

class ManagedBlamNewBitmap(ManagedBlam):
    def __init__(self, bitmap_name, bitmap_type):
        super().__init__()
        self.bitmap_name = bitmap_name
        self.bitmap_type = bitmap_type if bitmap_type else "default"
        self.tag_helper()

    def get_path(self):
        asset_path = get_asset_path()
        bitmaps_dir = os.path.join(asset_path, "bitmaps")
        bitmap_path = os.path.join(bitmaps_dir, self.bitmap_name + ".bitmap")

        return bitmap_path

    def tag_edit(self, tag):
        if self.bitmap_type == "default":
            suffix = self.bitmap_name.rpartition("_")[2].lower()
            print(suffix)
            self.bitmap_type = "Diffuse Map"
            if suffix and "_" in self.bitmap_name.strip("_"):
                h4 = not_bungie_game()
                if suffix.startswith(("orm", "mro", "mtr", "rmo", "control")):
                    self.bitmap_type = "Material Map"
                elif suffix.startswith("3d"):
                    self.bitmap_type = "3D Texture"
                elif suffix.startswith("blend"):
                    self.bitmap_type = "Blend Map (linear for terrains)"
                elif suffix.startswith("bump"):
                    self.bitmap_type = "Bump Map (from Height Map)"
                elif suffix.startswith(("cc", "change")):
                    self.bitmap_type = "Change Color Map"
                elif suffix.startswith("cube"):
                    self.bitmap_type = "Cube Map (Reflection Map)"
                elif suffix.startswith(("detailb", "detail_b")):
                    self.bitmap_type = "Detail Bump Map (from Height Map - fades out)"
                elif suffix.startswith(("detailn", "detail_n")):
                    self.bitmap_type = "Detail Normal Map"
                elif suffix.startswith("det"):
                    self.bitmap_type = "Detail Map"
                elif suffix.startswith("dsprite"):
                    self.bitmap_type = "Sprite (Double Multiply, Gray Background)"
                elif suffix.startswith("float"):
                    self.bitmap_type = "Float Map (WARNING)"
                elif suffix.startswith("height"):
                    self.bitmap_type = "Height Map (for Parallax)"
                elif suffix.startswith(("illum", "self", "emm")):
                    self.bitmap_type = "Self-Illum Map"
                elif suffix.startswith("msprite"):
                    self.bitmap_type = "Sprite (Blend, White Background)"
                elif suffix.startswith("spec"):
                    self.bitmap_type = "Specular Map"
                elif suffix.startswith("sprite"):
                    self.bitmap_type = "Sprite (Additive, Black Background)"
                elif suffix.startswith("ui"):
                    self.bitmap_type = "Interface Bitmap"
                elif suffix.startswith("vec"):
                    self.bitmap_type = "Vector Map"
                elif suffix.startswith("warp"):
                    self.bitmap_type = "Warp Map (EMBM)"
                elif suffix.startswith(("zbump", "dx_normal")):
                    self.bitmap_type = "ZBrush Bump Map (from Bump Map)"
                elif suffix.startswith(("nor", "nm", "nrm")):
                    if h4:
                        self.bitmap_type = "Normal Map (from Standard Orientation of Maya, Modo, Zbrush)"
                    else:
                        self.bitmap_type = "Normal Map (aka zbump)"


        usage_enum = tag.SelectField("LongEnum:Usage")
        usage_enum.SetValue(self.bitmap_type)
        curve_mode = tag.SelectField("CharEnum:curve mode")
        curve_mode.SetValue("force PRETTY")
        override_block = tag.SelectField("Block:usage override")
        # Check for existing usage override block so we don't overwrite
        if not override_block.Elements.Count:
            override_block.AddElement()
        override_element = override_block.Elements[0]
        reset = override_element.SelectField("reset usage override")
        reset.RunCommand()
        bitmap_curve = override_element.SelectField("bitmap curve")
        if bitmap_curve.Value == 1: # 1 is xRGB
            bitmap_curve.SetValue("sRGB (gamma 2.2)")
        flags = override_element.SelectField("flags")
        flags.SetBit("Ignore Curve Override", True)
        # flags.SetBit("Dont Allow Size Optimization", True)
        # dicer_flags = override_element.SelectField("dicer flags")
        # dicer_flags.SetBit("Color Grading sRGB Correction", True)

class ManagedBlam_NewMaterial(ManagedBlamTag):
    """Runs a ManagedBlam Operation"""

    bl_idname = "managed_blam.new_material"
    bl_label = "ManagedBlam"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Runs a ManagedBlam Operation"

    blender_material: StringProperty(
        default="Material",
        name="Blender Material",
    )

    def get_path(self):
        asset_path = get_asset_path()
        shaders_dir = os.path.join(asset_path, "materials")
        shader_name = get_valid_shader_name(self.blender_material)
        shader_path = os.path.join(shaders_dir, shader_name + ".material")

        return shader_path

    def tag_edit(self, context, tag):
        pass


class ManagedBlam_NewBitmap(ManagedBlamTag):
    """Runs a ManagedBlam Operation"""

    bl_idname = "managed_blam.new_bitmap"
    bl_label = "ManagedBlam"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Runs a ManagedBlam Operation"

    bitmap_name: StringProperty(
        default="bitmap",
        name="Bitmap",
    )

    bitmap_type: StringProperty(
        default="bitmap",
        name="Bitmap",
    )

    def get_path(self):
        asset_path = get_asset_path()
        bitmaps_dir = os.path.join(asset_path, "bitmaps")
        bitmap_path = os.path.join(bitmaps_dir, self.bitmap_name + ".bitmap")

        return bitmap_path

    def tag_edit(self, context, tag):
        pass
        # field = tag.SelectField("Struct:render_method[0]/Block:parameters")
        # bitmap_type = field
        # # type.SetStringData(p.name)
    
class ManagedBlam_ModelOverride(ManagedBlamTag):
    """Runs a ManagedBlam Operation"""

    bl_idname = "managed_blam.new_model_override"
    bl_label = "ManagedBlam"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Runs a ManagedBlam Operation"

    render_model: StringProperty()
    collision_model: StringProperty()
    physics_model: StringProperty()
    model_animation_graph: StringProperty()

    def get_path(self):
        asset_path = get_asset_path()
        asset_name = asset_path.rpartition(os.sep)[2]
        model_path = os.path.join(asset_path, asset_name + ".model")

        return model_path

    def tag_edit(self, context, tag):
        if self.render_model and os.path.exists(os.path.join(get_tags_path() + self.render_model)):
            _, new_tag_ref = get_tag_and_path(self.Bungie, self.render_model)
            field = tag.SelectField("Reference:render model")
            render_model = field
            render_model.Path = new_tag_ref

        if self.collision_model and os.path.exists(os.path.join(get_tags_path() + self.collision_model)):
            _, new_tag_ref = get_tag_and_path(self.Bungie, self.collision_model)
            field = tag.SelectField("Reference:collision model")
            collision_model = field
            collision_model.Path = new_tag_ref

        if self.model_animation_graph and os.path.exists(os.path.join(get_tags_path() + self.model_animation_graph)):
            _, new_tag_ref = get_tag_and_path(self.Bungie, self.model_animation_graph)
            field = tag.SelectField("Reference:animation")
            model_animation_graph = field
            model_animation_graph.Path = new_tag_ref
            
        if self.physics_model and os.path.exists(os.path.join(get_tags_path() + self.physics_model)):
            _, new_tag_ref = get_tag_and_path(self.Bungie, self.physics_model)
            field = tag.SelectField("Reference:physics_model")
            physics_model = field
            physics_model.Path = new_tag_ref

class ManagedBlam_RenderStructureMeta(ManagedBlamTag):
    """Runs a ManagedBlam Operation"""

    bl_idname = "managed_blam.render_structure_meta"
    bl_label = "ManagedBlam"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Runs a ManagedBlam Operation"

    structure_meta: StringProperty()

    def get_path(self):
        asset_path = get_asset_path()
        asset_name = asset_path.rpartition(os.sep)[2]
        model_path = os.path.join(asset_path, asset_name + ".render_model")

        return model_path

    def tag_edit(self, context, tag):
        if self.structure_meta and os.path.exists(os.path.join(get_tags_path() + self.structure_meta)):
            _, new_tag_ref = get_tag_and_path(self.Bungie, self.structure_meta)
            field = tag.SelectField("Reference:structure meta data")
            structure_meta = field
            structure_meta.Path = new_tag_ref


classeshalo = (
    ManagedBlam_Init,
    ManagedBlam_Close,
    # ManagedBlam_NewShader,
    # ManagedBlam_NewMaterial,
    ManagedBlam_NewBitmap,
    ManagedBlam_ModelOverride,
    ManagedBlam_RenderStructureMeta,
)

def register():
    for clshalo in classeshalo:
        bpy.utils.register_class(clshalo)


def unregister():
    for clshalo in classeshalo:
        bpy.utils.unregister_class(clshalo)

if __name__ == "__main__":
    register()
