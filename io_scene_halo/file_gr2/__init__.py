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
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper

import os
import sys
t = os.getcwd()
t += '\\scripts\\addons\\io_scene_fbx'
sys.modules[bpy.types.IMPORT_SCENE_OT_fbx.__module__].__file__
sys.path.insert(0,t)
from io_scene_fbx import export_fbx_bin

class Export_Halo_GR2(Operator, ExportHelper):
    """Exports a Halo GEN4 Asset using your Halo Editing Kit"""
    bl_idname = 'export_halo.gr2'
    bl_label = 'Export Asset'
    bl_options = {'UNDO', 'PRESET'}

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
    export_sidecar_xml: BoolProperty(
        name="Export Sidecar",
        description="",
        default=True,
    )
    sidecar_type: EnumProperty(
        name='Asset Type',
        description='',
        default='MODEL',
        items=[ ('MODEL', "Model", ""), ('SCENARIO', "Scenario", ""), ('SKY', 'Sky', ''), ('DECORATOR SET', 'Decorator Set', ''), ('PARTICLE MODEL', 'Particle Model', '')]
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
    export_poops: BoolProperty(
        name='Instanced Geometry',
        description='',
        default=True,
    )
    export_markers: BoolProperty(
        name='Markers',
        description='',
        default=True,
    )
    export_lights: BoolProperty(
        name='Lights',
        description='',
        default=True,
    )
    export_portals: BoolProperty(
        name='Portals',
        description='',
        default=True,
    )
    export_seams: BoolProperty(
        name='Seams',
        description='',
        default=True,
    )
    export_water_surfaces: BoolProperty(
        name='Water Surfaces',
        description='',
        default=True,
    )
    export_fog_planes: BoolProperty(
        name='Fog Planes',
        description='',
        default=True,
    )
    export_cookie_cutters: BoolProperty(
        name='Cookie Cutters',
        description='',
        default=True,
    )
    export_lightmap_regions: BoolProperty(
        name='Lightmap Regions',
        description='',
        default=True,
    )
    export_boundary_surfaces: BoolProperty(
        name='Boundary Surfaces',
        description='',
        default=True,
    )
    export_water_physics: BoolProperty(
        name='Water Physics',
        description='',
        default=True,
    )
    export_rain_occluders: BoolProperty(
        name='Rain Occluders',
        description='',
        default=True,
    )
    export_shared: BoolProperty(
        name='Shared',
        description='Export geometry which is shared across all BSPs',
        default=True,
    )
    export_all_bsps: BoolProperty(
        name='All BSPs',
        description='',
        default=True,
    )
    export_specific_bsp: IntProperty(
        name='BSP',
        description='',
        default=0,
        min=0,
        max=99,
        step=5,
    )
    export_all_perms: BoolProperty(
        name='All Permutations',
        description='',
        default=True,
    )
    export_specific_perm: StringProperty(
        name='Permutation',
        description='Limited exporting to the named permutation only. Must match case',
        default='',
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
        default=True,
    )
    show_output: BoolProperty(
        name='Show Output',
        description='',
        default=True
    )
    run_tagwatcher: BoolProperty(
        name='Run Tagwatcher',
        description='Runs tag watcher after asset has been imported',
        default=False
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
    use_mesh_modifiers: BoolProperty(
        name='Apply Modifiers',
        description='',
        default=True,
    )
    use_triangles: BoolProperty(
        name='Triangulate',
        description='',
        default=True,
    )
    global_scale: FloatProperty(
        name='Scale',
        description='',
        default=1.0
    )
    use_armature_deform_only: BoolProperty(
        name='Deform Bones Only',
        description='Only export bones with the deform property ticked',
        default=True,
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
    import_in_background: BoolProperty(
        name='Run In Background',
        description="If enabled does not pause use of blender during the import process",
        default=False
    )
    lightmap_structure: BoolProperty(
        name='Run Lightmapper',
        default=False,
    )
    lightmap_quality: EnumProperty(
        name='Quality',
        items=(('DIRECT', "Direct", ""),
                ('DRAFT', "Draft", ""),
                ('LOW', "Low", ""),
                ('MEDIUM', "Medium", ""),
                ('HIGH', "High", ""),
                ('SUPER', "Super (very slow)", ""),
                ),
        default='DIRECT',
    )
    lightmap_all_bsps: BoolProperty(
        name='Lightmap All',
        default=True,
    )
    lightmap_specific_bsp: IntProperty(
        name='Specific BSP',
        default=0,
        min=0,
        max=99,
        step=5,
    )
    mesh_smooth_type: EnumProperty(
            name="Smoothing",
            items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description="Export smoothing information "
                        "(prefer 'Normals Only' option if your target importer understand split normals)",
            default='OFF',
            )
    import_bitmaps: BoolProperty(
        name='Import Bitmaps',
        default=False,
    )
    bitmap_type: EnumProperty(
        name='Bitmap Type',
        items=(('2dtextures', "2D Textures", ""),
                ('3dtextures', "3D Textures", ""),
                ('cubemaps', "Cubemaps", ""),
                ('sprites', "Sprites", ""),
                ('interface', "Interface", ""),
                ),
        default='2dtextures',
    )

    def execute(self, context):
        keywords = self.as_keywords()
        console = bpy.ops.wm

        if self.show_output:
            console.console_toggle() # toggle the console so users can see progress of export

        from .prepare_scene import prepare_scene
        (objects_selection, active_object, hidden_objects, mode, model_armature, temp_armature, asset_path, asset, skeleton_bones, halo_objects, timeline_start, timeline_end, lod_count
        ) = prepare_scene(context, self.report, **keywords) # prepares the scene for processing and returns information about the scene
        # try:
        from .process_scene import process_scene
        process_scene(self, context, keywords, self.report, model_armature, asset_path, asset, skeleton_bones, halo_objects, timeline_start, timeline_end, lod_count, **keywords)
        # except:
        #     print('ASSERT: Scene processing failed')
        #     self.report({'WARNING'},'ASSERT: Scene processing failed')

        from .repair_scene import repair_scene
        repair_scene(context, self.report, objects_selection, active_object, hidden_objects, mode, temp_armature, timeline_start, timeline_end, model_armature, halo_objects.lights, **keywords)

        if self.show_output:
            console.console_toggle()

        return {'FINISHED'}

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
        col.prop(self, "show_output", text='Show Output')
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
            sub.prop(self, 'export_poops')
            sub.prop(self, 'export_markers')
            sub.prop(self, 'export_lights')
            sub.prop(self, 'export_portals')
            sub.prop(self, 'export_seams')
            sub.prop(self, 'export_water_surfaces')
            sub.prop(self, 'export_fog_planes')
            sub.prop(self, 'export_cookie_cutters')
            col.separator()
            sub.prop(self, "export_boundary_surfaces")
            sub.prop(self, "export_water_physics")
            sub.prop(self, "export_rain_occluders")
            col.separator()
            sub.prop(self, 'export_shared')
            if not self.export_all_bsps:
                sub.prop(self, 'export_specific_bsp')
            sub.prop(self, 'export_all_bsps')
        else:
            sub.prop(self, "export_render")
        if (self.sidecar_type not in ('DECORATOR SET', 'PARTICLE MODEL')):
            col.separator()
            if not self.export_all_perms:
                sub.prop(self, 'export_specific_perm', text='Permutation')
            sub.prop(self, 'export_all_perms', text='All Permutations')

        # SIDECAR SETTINGS #
        box = layout.box()
        box.label(text="Sidecar Settings")
        col = box.column()
        col.prop(self, "export_sidecar_xml")
        if self.export_sidecar_xml:
            if self.sidecar_type == 'MODEL' and self.export_sidecar_xml:
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
            col.prop(self, "run_tagwatcher")
            #col.prop(self, 'import_in_background') removed for now as risk of causing issues
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

        # LIGHTMAP SETTINGS #
        if self.sidecar_type == 'SCENARIO':
            box = layout.box()
            box.label(text="Lightmap Settings")
            col = box.column()
            col.prop(self, "lightmap_structure")
            if self.lightmap_structure:
                col.prop(self, "lightmap_quality")
                if not self.lightmap_all_bsps:
                    col.prop(self, 'lightmap_specific_bsp')
                col.prop(self, 'lightmap_all_bsps')

        # # BITMAP SETTINGS #
        # box = layout.box()
        # box.label(text="Bitmap Settings")
        # col = box.column()
        # col.prop(self, "import_bitmaps")
        # if self.import_bitmaps:
        #     col.prop(self, "bitmap_type")

        # SCENE SETTINGS #
        box = layout.box()
        box.label(text="Scene Settings")
        col = box.column()
        col.prop(self, "use_mesh_modifiers")
        col.prop(self, "use_triangles")
        col.prop(self, 'use_armature_deform_only')
        col.prop(self, 'mesh_smooth_type')
        col.separator()
        col.prop(self, "global_scale")
def menu_func_export(self, context):
    self.layout.operator(Export_Halo_GR2.bl_idname, text="Halo Gen4 Asset Export (.fbx .json .gr2. .xml)")

# def UpdateSettings(
#     keep_fbx,
#     keep_json,
#     export_sidecar,
#     sidecar_type,
#     export_method,
#     export_animations,
#     export_render,
#     export_collision,
#     export_physics,
#     export_markers,
#     export_structure,
#     export_poops,
#     export_lights,
#     export_portals,
#     export_seams,
#     export_water_surfaces,
#     export_fog_planes,
#     export_cookie_cutters,
#     export_lightmap_regions,
#     export_boundary_surfaces,
#     export_water_physics,
#     export_rain_occluders,
#     export_shared,

# ):
    # halo_gr2 = bpy.context.Scene.halo_gr2


def register():
    bpy.utils.register_class(Export_Halo_GR2)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(Export_Halo_GR2)

if __name__ == "__main__":
    register()