# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2022 Generalkidd & Crisp
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

bl_info = {
    'name': 'Halo GR2 Export',
    'author': 'Generalkidd, Crisp',
    'version': (117, 343, 2552),
    'blender': (3, 3, 0),
    'location': 'File > Export',
    'category': 'Export',
    'description': 'Halo Gen4 Asset Exporter'
    }

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, orientation_helper
from time import sleep
special_prefixes = ('b ', 'b_', 'frame ', 'frame_','bip ','bip_','bone ','bone_','#','+soft_ceiling','+soft_kill','+slip_surface', '@','+cookie','+decorator','+flair', '%', '$','+fog','+portal', '+seam','+water', '\'')

import os
import sys
t = os.getcwd()
t += '\\scripts\\addons\\io_scene_fbx'
sys.modules[bpy.types.IMPORT_SCENE_OT_fbx.__module__].__file__
sys.path.insert(0,t)
from io_scene_fbx import export_fbx_bin

@orientation_helper(axis_forward='Y', axis_up='Z')
class Export_Halo_GR2(Operator, ExportHelper):
    """Writes a Halo Reach GR2 File using your Halo Editing Kit"""
    bl_idname = 'export_halo.gr2'
    bl_label = 'Export Asset'

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default='*.fbx',
        options={'HIDDEN'},
        maxlen=1024,
    )
    game_version:EnumProperty(
        name="Game Version",
        description="The game to export this asset for",
        items=[ ('REACH', "Halo Reach", "Export an asset intended for Halo Reach")]
    )
    keep_fbx: BoolProperty(
        name="FBX",
        description="Keep the source FBX file after GR2 conversion",
        default=True,
    )
    keep_json: BoolProperty(
        name="JSON",
        description="Keep the source JSON file after GR2 conversion",
        default=True,
    )
    export_sidecar: BoolProperty(
        name="Export Sidecar",
        description="",
        default=True,
    )
    sidecar_type: EnumProperty(
        name='Asset Type',
        description='',
        default='MODEL',
        items=[ ('MODEL', "Model", ""), ('SCENARIO', "Scenario", ""), ('DECORATOR', "Decorator", ""), ('PARTICLE MODEL', "Particle Model", "")]
    )
    export_method: EnumProperty(
        name="Export Method",
        description="",
        items=[('BATCH', "Batch", ""), ('SELECTED', "Selected", "")]
    )
    export_animations: BoolProperty(
        name='Animations',
        description='',
        default=True,
    )
    export_render: BoolProperty(
        name='Render Models',
        description='',
        default=True,
    )
    export_collision: BoolProperty(
        name='Collision Models',
        description='',
        default=True,
    )
    export_physics: BoolProperty(
        name='Physics Models',
        description='',
        default=True,
    )
    export_markers: BoolProperty(
        name='Markers',
        description='',
        default=True,
    )
    export_structure: BoolProperty(
        name='Structure',
        description='',
        default=True,
    )
    export_structure_design: BoolProperty(
        name='Structure Design',
        description='',
        default=True,
    )
    output_biped: BoolProperty(
        name='Biped',
        description='',
        default=False,
    )
    output_crate: BoolProperty(
        name='Crate',
        description='',
        default=False,
    )
    output_creature: BoolProperty(
        name='Creature',
        description='',
        default=False,
    )
    output_device_control: BoolProperty(
        name='Device Control',
        description='',
        default=False,
    )
    output_device_machine: BoolProperty(
        name='Device Machine',
        description='',
        default=False,
    )
    output_device_terminal: BoolProperty(
        name='Device Terminal',
        description='',
        default=False,
    )
    output_effect_scenery: BoolProperty(
        name='Effect Scenery',
        description='',
        default=False,
    )
    output_equipment: BoolProperty(
        name='Equipment',
        description='',
        default=False,
    )
    output_giant: BoolProperty(
        name='Giant',
        description='',
        default=False,
    )
    output_scenery: BoolProperty(
        name='Scenery',
        description='',
        default=False,
    )
    output_vehicle: BoolProperty(
        name='Vehicle',
        description='',
        default=False,
    )
    output_weapon: BoolProperty(
        name='Weapon',
        description='',
        default=False,
    )
    import_to_game: BoolProperty(
        name='Import to Game',
        description='',
        default=False,
    )
    import_check: BoolProperty(
        name='Check',
        description='Run the import process but produce no output files',
        default=False,
    )
    import_force: BoolProperty(
        name='Force',
        description="Force all files to import even if they haven't changed",
        default=False,
    )
    import_verbose: BoolProperty(
        name='Verbose',
        description="Write additional import progress information to the console",
        default=False,
    )
    import_draft: BoolProperty(
        name='Draft',
        description="Skip generating PRT data. Faster speed, lower quality",
        default=False,
    )
    import_seam_debug: BoolProperty(
        name='Seam Debug',
        description="Write extra seam debugging information to the console",
        default=False,
    )
    import_skip_instances: BoolProperty(
        name='Skip Instances',
        description="Skip importing all instanced geometry",
        default=False,
    )
    import_decompose_instances: BoolProperty(
        name='Decompose Instances',
        description="Run convex decomposition for instanced geometry physics (very slow)",
        default=False,
    )
    import_surpress_errors: BoolProperty(
        name='Surpress Errors',
        description="Do not write errors to vrml files",
        default=False,
    )
    apply_unit_scale: BoolProperty(
        name="Apply Unit",
        description="",
        default=True,
    )
    apply_scale_options: EnumProperty(
        default='FBX_SCALE_UNITS',
        items=[('FBX_SCALE_UNITS', "FBX Units Scale",""),]
    )
    use_selection: BoolProperty(
        name="selection",
        description="",
        default=True,
    )
    add_leaf_bones: BoolProperty(
        name='',
        description='',
        default=False
    )
    bake_anim: BoolProperty(
        name='',
        description='',
        default=True
    )
    bake_anim_use_all_bones: BoolProperty(
        name='',
        description='',
        default=False
    )
    bake_anim_use_nla_strips: BoolProperty(
        name='',
        description='',
        default=False
    )
    bake_anim_use_all_actions: BoolProperty(
        name='',
        description='',
        default=False
    )
    bake_anim_force_startend_keying: BoolProperty(
        name='',
        description='',
        default=False
    )

    def UpdateVisible(self, context):
        if self.export_hidden == True:
            self.use_visible = False
        else:
            self.use_visible = True
    
    export_hidden: BoolProperty(
        name="Hidden",
        update=UpdateVisible,
        description="Export visible objects only",
        default=True,
    )
    use_visible: BoolProperty(
        name="",
        description="",
        default=False,
    )

    def GetAssetPath(self):
        asset = self.filepath.rpartition('\\')[0]
        return asset

    asset_path: StringProperty(
        name='',
        description="",
        get=GetAssetPath,
    )

    def GetAssetName(self):
        asset = self.asset_path.rpartition('\\')[2]
        asset = asset.strip('.fbx')
        return asset

    asset_name: StringProperty(
        name='',
        description="",
        get=GetAssetName,
    )

    def execute(self, context):
        keywords = self.as_keywords()
        from . import export_gr2, export_sidecar_xml, import_sidecar

        if self.sidecar_type == 'MODEL':

            if self.export_render:
                perm_list = []
                for ob in bpy.data.objects:
                    if ob.halo_json.Permutation_Name == '':
                        perm = 'default'
                    else:
                        perm = ob.halo_json.Permutation_Name
                    if perm not in perm_list:
                        perm_list.append(perm)
                        SelectModelRender(perm)
                        for select in bpy.context.selected_objects:
                            print (select.name)
                        export_fbx_bin.save(self, context, **keywords)
                        export_gr2.save(self, context, self.report, 'render', perm, **keywords)

            if self.export_collision:
                perm_list = []
                for ob in bpy.data.objects:
                    if ob.halo_json.Permutation_Name == '':
                        perm = 'default'
                    else:
                        perm = ob.halo_json.Permutation_Name
                    if perm not in perm_list:
                        perm_list.append(perm)
                        SelectModelCollision(perm)
                        export_fbx_bin.save(self, context, **keywords)
                        export_gr2.save(self, context, self.report, 'collision', perm, **keywords)

            if self.export_physics:
                perm_list = []
                for ob in bpy.data.objects:
                    if ob.halo_json.Permutation_Name == '':
                        perm = 'default'
                    else:
                        perm = ob.halo_json.Permutation_Name
                    if perm not in perm_list:
                        perm_list.append(perm)
                        SelectModelPhysics(perm)
                        export_fbx_bin.save(self, context, **keywords)
                        export_gr2.save(self, context, self.report, 'physics', perm, **keywords)

            if self.export_markers:
                SelectModelMarkers()
                export_fbx_bin.save(self, context, **keywords)
                export_gr2.save(self, context, self.report, 'markers', **keywords)

            SelectModelSkeleton()
            export_fbx_bin.save(self, context, **keywords)
            export_gr2.save(self, context, self.report, 'skeleton', **keywords)

            if self.export_animations and 0<=len(bpy.data.actions):
                SelectModelSkeleton()
                for ob in bpy.context.selected_objects:
                    bpy.context.view_layer.objects.active = ob
                    for anim in bpy.data.actions:
                        ob.animation_data.action = anim
                        export_fbx_bin.save(self, context, **keywords)
                        export_gr2.save(self, context, self.report, 'animations', **keywords)
                    
        elif self.sidecar_type == 'SCENARIO':
            print('not implemented')

        elif self.sidecar_type == 'DECORATOR':
            print('not implemented')

        elif self.sidecar_type == 'PARTICLE MODEL':
            print('not implemented')

        export_sidecar_xml.save(self, context, self.report, **keywords)
        return import_sidecar.save(self, context, self.report, **keywords)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        box = layout.box()
        # SETTINGS #
        box.label(text="Settings")

        col = box.column()
        col.prop(self, "game_version", text='Game Version')
        col.prop(self, "export_method", text='Export Method')
        col.prop(self, "sidecar_type", text='Asset Type')

        sub = box.column(heading="Keep")
        sub.prop(self, "keep_fbx")
        sub.prop(self, "keep_json")
        # EXPORT CATEGORIES #
        box = layout.box()
        box.label(text="Export Categories")
        sub = box.column(heading="Export")
        sub.prop(self, "export_hidden")
        if self.sidecar_type == 'MODEL':
            sub.prop(self, "export_animations")
            sub.prop(self, "export_render")
            sub.prop(self, "export_collision")
            sub.prop(self, "export_physics")
            sub.prop(self, "export_markers")
        elif self.sidecar_type == 'SCENARIO':
            sub.prop(self, "export_structure")
            sub.prop(self, "export_structure_design")
        else:
            sub.prop(self, "export_render")

        # SIDECAR SETTINGS #
        box = layout.box()
        box.label(text="Sidecar Settings")
        col = box.column()
        col.prop(self, "export_sidecar")
        if self.sidecar_type == 'MODEL' and self.export_sidecar:
            sub = box.column(heading="Output Tags")
        if self.sidecar_type == 'MODEL':
            sub.prop(self, "output_biped")
            sub.prop(self, "output_crate")
            sub.prop(self, "output_creature")
            sub.prop(self, "output_device_control")
            sub.prop(self, "output_device_machine")
            sub.prop(self, "output_device_terminal")
            sub.prop(self, "output_effect_scenery")
            sub.prop(self, "output_equipment")
            sub.prop(self, "output_giant")
            sub.prop(self, "output_scenery")
            sub.prop(self, "output_vehicle")
            sub.prop(self, "output_weapon")

        # IMPORT SETTINGS #
        box = layout.box()
        box.label(text="Import Settings")
        col = box.column()
        col.prop(self, "import_to_game")
        if self.import_to_game:
            sub = box.column(heading="Import Flags")
            sub.prop(self, "import_check")
            sub.prop(self, "import_force")
            sub.prop(self, "import_verbose")
            sub.prop(self, "import_surpress_errors")
        if self.sidecar_type == 'SCENARIO':
            sub.prop(self, "import_seam_debug")
            sub.prop(self, "import_skip_instances")
            sub.prop(self, "import_decompose_instances")
        else:
            sub.prop(self, "import_draft")

def SelectModelRender(perm):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        halo_mesh = ob.halo_json
        halo_mesh_name = ob.name
        if halo_mesh.Permutation_Name != perm and perm == 'default':
            perm = ''
        if (ob.type == 'MESH' and (not halo_mesh_name.startswith(special_prefixes)) and halo_mesh.Object_Type_All == 'MESH' and halo_mesh.ObjectMesh_Type == 'DEFAULT' and halo_mesh.Permutation_Name == perm) or ob.type == 'ARMATURE':
            ob.select_set(True)

def SelectModelCollision(perm):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        halo_mesh = ob.halo_json
        halo_mesh_name = ob.name
        if halo_mesh.Permutation_Name != perm and perm == 'default':
            perm = ''
        if (ob.type == 'MESH' and (not halo_mesh_name.startswith(special_prefixes) or halo_mesh_name.startswith('@')) and (halo_mesh.ObjectMesh_Type == 'COLLISION' or halo_mesh_name.startswith('@')) and halo_mesh.Object_Type_All == 'MESH' and halo_mesh.Permutation_Name == perm) or ob.type == 'ARMATURE':
            ob.select_set(True)

def SelectModelPhysics(perm):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        halo_mesh = ob.halo_json
        halo_mesh_name = ob.name
        if halo_mesh.Permutation_Name != perm and perm == 'default':
            perm = ''
        if (ob.type == 'MESH' and (not halo_mesh_name.startswith(special_prefixes) or halo_mesh_name.startswith('$')) and (halo_mesh.ObjectMesh_Type == 'PHYSICS' or halo_mesh_name.startswith('$')) and halo_mesh.Object_Type_All == 'MESH' and halo_mesh.Permutation_Name == perm) or ob.type == 'ARMATURE':
            ob.select_set(True)

def SelectModelMarkers():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        halo_node = ob.halo_json
        halo_node_name = ob.name
        if (ob.type == 'MESH' and (halo_node.Object_Type_All == 'MARKER' or halo_node_name.startswith('#'))) or ob.type == 'EMPTY' and (halo_node.Object_Type_No_Mesh == 'MARKER' or halo_node_name.startswith('#')) or ob.type == 'ARMATURE':
            ob.select_set(True)

def SelectModelSkeleton():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE':
            ob.select_set(True)

def menu_func_export(self, context):
    self.layout.operator(Export_Halo_GR2.bl_idname, text="Halo Granny File (.gr2)")

def register():
    bpy.utils.register_class(Export_Halo_GR2)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(Export_Halo_GR2)

if __name__ == "__main__":
    register()