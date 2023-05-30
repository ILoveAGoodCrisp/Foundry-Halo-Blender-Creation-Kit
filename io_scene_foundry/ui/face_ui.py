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

from ..utils.nwo_utils import bpy_enum_list, closest_bsp_object, export_objects, layer_face_count, random_colour, sort_alphanum, true_bsp, true_region
from . import poll_ui
from .templates import NWO_Op, NWO_PropPanel
from bpy.props import EnumProperty, BoolProperty, StringProperty
import bpy
import bmesh
from uuid import uuid4
import gpu
from gpu_extras.batch import batch_for_shader
import numpy as np
from random import random
from .object_ui import NWO_RegionList, NWO_GlobalMaterialList, NWO_GlobalMaterialMenu

class NWO_FacePropAddMenu(bpy.types.Menu):
    bl_label = "Add Face Property"
    bl_idname = "NWO_MT_FacePropAdd"

    def draw(self, context):
        layout = self.layout
        ob = context.object
        ob_nwo = ob.nwo
        if poll_ui(('MODEL', 'SKY')):
            layout.operator("nwo.face_layer_add", text='Region').options = 'region'
        # if poll_ui('SCENARIO') and ob_nwo.mesh_type_ui == '_connected_geometry_mesh_type_structure':
        #     layout.operator("nwo.face_layer_add", text='Seam').options = 'seam'
        if ob_nwo.mesh_type_ui == '_connected_geometry_mesh_type_collision' or ob_nwo.mesh_type_ui == '_connected_geometry_mesh_type_physics' or ob_nwo.mesh_type_ui == '_connected_geometry_mesh_type_poop' or (ob_nwo.mesh_type_ui == '_connected_geometry_mesh_type_default' and poll_ui('SCENARIO')):
            layout.operator("nwo.face_layer_add", text='Collision Material').options = 'face_global_material'
        if ob_nwo.mesh_type_ui in ('_connected_geometry_mesh_type_render', '_connected_geometry_mesh_type_poop', '_connected_geometry_mesh_type_poop_collision', '_connected_geometry_mesh_type_collision'):
            layout.operator("nwo.face_layer_add", text="Two Sided").options = "two_sided"
        if poll_ui(('MODEL', 'SCENARIO', 'PREFAB')):
            if ob_nwo.mesh_type_ui in ('_connected_geometry_mesh_type_render', '_connected_geometry_mesh_type_poop', '_connected_geometry_mesh_type_structure'):
                layout.operator("nwo.face_layer_add", text='Uncompressed').options = 'precise_position'
            # layout.operator_menu_enum("nwo.face_layer_add_misc",
            #                         property="options",
            #                         text="Other",
            #                         )

        if poll_ui(('SCENARIO', 'PREFAB')):
            layout.operator("nwo.face_layer_add", text="Sky").options = "_connected_geometry_face_type_sky"
            layout.operator("nwo.face_layer_add", text="Seam Sealer").options = "_connected_geometry_face_type_seam_sealer"
            layout.operator("nwo.face_layer_add", text="Emissive").options = "emissive"
            layout.operator_menu_enum("nwo.face_layer_add_face_type",
                                    property="options",
                                    text="Type",
                                    )
            layout.operator_menu_enum("nwo.face_layer_add_face_mode",
                                    property="options",
                                    text="Mode",
                                    )
            layout.operator_menu_enum("nwo.face_layer_add_flags",
                                    property="options",
                                    text="Flags",
                                    )
            layout.operator_menu_enum("nwo.face_layer_add_lightmap",
                                    property="options",
                                    text="Lightmap",
                                    )


class NWO_FacePropPanel(NWO_PropPanel):
    bl_label = "Face Properties"
    bl_idname = "NWO_PT_FaceLevelDetailsPanel"
    bl_parent_id = "NWO_PT_ObjectDetailsPanel"
    bl_context = "mesh"

    @classmethod
    def poll(cls, context):
        ob = context.object
        valid_mesh_types = ('_connected_geometry_mesh_type_collision', '_connected_geometry_mesh_type_structure', '_connected_geometry_mesh_type_render', '_connected_geometry_mesh_type_poop')
        return ob and ob.nwo.export_this and ob.type == 'MESH' and ob.nwo.object_type_ui == '_connected_geometry_object_type_mesh' and ob.nwo.mesh_type_ui in valid_mesh_types
    
    def draw(self, context):
        layout = self.layout
        ob = context.object
        ob_nwo = ob.data.nwo
        layout.use_property_split = True
        row = layout.row()
        row.use_property_split = False
        #row.prop(ob_nwo, "mesh_face", expand=True)
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        if len(ob_nwo.face_props) <= 0 and context.mode != 'EDIT_MESH':
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
            col = flow.column()
            col.scale_y = 1.3
            col.operator("nwo.edit_face_map", text="Use Edit Mode to add face properties")
        else:


            rows = 4

            row = layout.row()
            row.template_list("NWO_UL_FacePropList", "", ob_nwo, "face_props", ob_nwo, "face_props_index", rows=rows)
            
            if context.mode == 'EDIT_MESH':
                col = row.column(align=True)
                col.menu(NWO_FacePropAddMenu.bl_idname, text='', icon='ADD')
                col.operator("nwo.face_layer_remove", icon='REMOVE', text="")

                # col.separator()

                # col.operator("nwo.edit_face_map", text='', icon='EDITMODE_HLT')

                col.separator()
                col.operator("nwo.face_layer_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("nwo.face_layer_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

                row = layout.row()

                if ob_nwo.face_props:
                    sub = row.row(align=True)
                    sub.operator("nwo.face_layer_assign", text="Assign").assign = True
                    sub.operator("nwo.face_layer_assign", text="Remove").assign = False

                    sub = row.row(align=True)
                    sub.operator("nwo.face_layer_select", text="Select").select = True
                    sub.operator("nwo.face_layer_select", text="Deselect").select = False
            
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
            col = flow.column()
            row = col.row()
            if ob_nwo.face_props:
                item = ob_nwo.face_props[ob_nwo.face_props_index]
                # row.prop(item, 'name')
                # if not (item.region_name_override and item.face_type_override and item.face_mode_override and item.face_sides_override and item.face_draw_distance_override and item.texcoord_usage_override
                #          and item.face_global_material_override and item.ladder_override and item.slip_surface_override and item.decal_offset_override and item.group_transparents_by_plane_override
                #            and item.no_shadow_override and item.precise_position_override and item.no_lightmap_override and item.no_pvs_override
                #         ):

                # if (is_poop and (item.instanced_collision_override or item.instanced_physics_override or item.cookie_cutter_override)):
                #     if item.instanced_collision_override:
                #         col.label(text="Current FaceMap is used for this mesh's bullet collision")
                #     if item.instanced_physics_override:
                #         col.label(text="Current FaceMap is used for this mesh's player collision")
                #     if item.cookie_cutter_override:
                #         col.label(text="Current FaceMap is used for this mesh's cookie cutter")

                # if item.instanced_collision_override:
                #     row = col.row()
                #     row.prop(item, "instanced_collision")
                #     row.operator("nwo.remove_face_property", text='', icon='X').options = 'instanced_collision'
                # if item.instanced_physics_override:
                #     row = col.row()
                #     row.prop(item, "instanced_physics")
                #     row.operator("nwo.remove_face_property", text='', icon='X').options = 'instanced_physics'
                # if item.cookie_cutter_override:
                #     row = col.row()
                #     row.prop(item, "cookie_cutter")
                #     row.operator("nwo.remove_face_property", text='', icon='X').options = 'cookie_cutter'
                if item.region_name_override:
                    row = col.row()
                    row.prop(item, "region_name_ui")
                    row.operator_menu_enum("nwo.face_region_list", "region", text='', icon="DOWNARROW_HLT")
                if item.face_type_override:
                    if item.face_type_ui == '_connected_geometry_face_type_sky':
                        col.separator()
                        box = col.box()
                        row = box.row()
                        row.label(text="Face Type Settings")
                        row = box.row()
                        row.prop(item, "face_type_ui")
                        row = box.row()
                        row.prop(item, "sky_permutation_index_ui")
                    else:
                        row = col.row()
                        row.prop(ob_nwo, "face_type_ui")
                        
                if item.face_mode_override:
                    row = col.row()
                    row.prop(item, "face_mode_ui")
                if item.face_two_sided_override:
                    row = col.row()
                    row.prop(item, "face_two_sided_ui")
                if item.face_draw_distance_override:
                    row = col.row()
                    row.prop(item, "face_draw_distance_ui")
                if item.texcoord_usage_override:
                    row = col.row()
                    row.prop(item, 'texcoord_usage_ui')
                if item.face_global_material_override:
                    row = col.row()
                    row.prop(item, "face_global_material_ui")
                    row.operator_menu_enum("nwo.face_global_material_list", "global_material", text='', icon="DOWNARROW_HLT")
                if item.ladder_override:
                    row = col.row()
                    row.prop(item, "ladder_ui")
                if item.slip_surface_override:
                    row = col.row()
                    row.prop(item, "slip_surface_ui")
                if item.decal_offset_override:
                    row = col.row()
                    row.prop(item, "decal_offset_ui")
                if item.group_transparents_by_plane_override:
                    row = col.row()
                    row.prop(item, "group_transparents_by_plane_ui")
                if item.no_shadow_override:
                    row = col.row()
                    row.prop(item, "no_shadow_ui")
                if item.precise_position_override:
                    row = col.row()
                    row.prop(item, "precise_position_ui")
                if item.no_lightmap_override:
                    row = col.row()
                    row.prop(item, "no_lightmap_ui")
                if item.no_pvs_override:
                    row = col.row()
                    row.prop(item, "no_pvs_ui")
                # lightmap
                if item.lightmap_additive_transparency_override:
                    row = col.row()
                    row.prop(item, "lightmap_additive_transparency_ui")
                if item.lightmap_resolution_scale_override:
                    row = col.row()
                    row.prop(item, "lightmap_resolution_scale_ui")
                if item.lightmap_type_override:
                    row = col.row()
                    row.prop(item, "lightmap_type_ui")
                if item.lightmap_analytical_bounce_modifier_override:
                    row = col.row()
                    row.prop(item, "lightmap_analytical_bounce_modifier_ui")
                if item.lightmap_general_bounce_modifier_override:
                    row = col.row()
                    row.prop(item, "lightmap_general_bounce_modifier_ui")
                if item.lightmap_translucency_tint_color_override:
                    row = col.row()
                    row.prop(item, "lightmap_translucency_tint_color_ui")
                if item.lightmap_lighting_from_both_sides_override:
                    row = col.row()
                    row.prop(item, "lightmap_lighting_from_both_sides_ui")
                # material lighting
                if item.emissive_override:
                    col.separator()
                    box = col.box()
                    row = box.row()
                    row.label(text="Emissive Settings")
                    # row.operator("nwo.remove_mesh_property", text='', icon='X').options = 'emissive'
                    row = box.row()
                    row.prop(item, "material_lighting_emissive_color_ui", text="Color")
                    row = box.row()
                    row.prop(item, "material_lighting_emissive_power_ui", text="Power")
                    row = box.row()
                    row.prop(item, "material_lighting_emissive_quality_ui", text="Quality")
                    row = box.row()
                    row.prop(item, "material_lighting_emissive_focus_ui", text="Focus")
                    row = box.row()
                    row.prop(item, "material_lighting_attenuation_falloff_ui", text="Attenutation Falloff")
                    row = box.row()
                    row.prop(item, "material_lighting_attenuation_cutoff_ui", text="Attenutation Cutoff")
                    row = box.row()
                    row.prop(item, "material_lighting_bounce_ratio_ui", text="Bounce Ratio")
                    row = box.row()
                    row.prop(item, "material_lighting_use_shader_gel_ui", text="Shader Gel")
                    row = box.row()
                    row.prop(item, "material_lighting_emissive_per_unit_ui", text="Emissive Per Unit")

# ----------------------------------------------------------------

class NWO_UL_FacePropList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        face_layer = item
        if face_layer:
            if context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(context.object.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(context.object.data)

            layer = bm.faces.layers.int.get(face_layer.layer_name)
            row = layout.row()      
            row.scale_x = 0.25
            row.prop(face_layer, "layer_colour", text="")
            row = layout.row()
            row.prop(face_layer, "name", text="", emboss=False, icon_value=icon)
            row = layout.row()
            row.alignment = 'RIGHT'
            row.label(text=f'{str(layer_face_count(bm, layer))}  ')

    
def toggle_override(context, option, bool_var):
    ob = context.object
    ob_nwo = ob.data.nwo
    item = ob_nwo.face_props[ob_nwo.face_props_index]
        
    match option:
        case 'seam':
            item.seam_override = bool_var
        case 'region':
            item.region_name_override = bool_var
        case 'face_type':
            item.face_type_override = bool_var
        case 'face_mode':
            item.face_mode_override = bool_var
        case 'two_sided':
            item.face_two_sided_override = bool_var
            item.face_two_sided_ui = True
        case '_connected_geometry_face_type_sky':
            item.face_type_override = bool_var
            item.face_type_ui = '_connected_geometry_face_type_sky'
        case '_connected_geometry_face_type_seam_sealer':
            item.face_type_override = bool_var
            item.face_type_ui = '_connected_geometry_face_type_seam_sealer'
        case '_connected_geometry_face_mode_render_only':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_render_only'
        case '_connected_geometry_face_mode_collision_only':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_collision_only'
        case '_connected_geometry_face_mode_sphere_collision_only':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_sphere_collision_only'
        case '_connected_geometry_face_mode_shadow_only':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_shadow_only'
        case '_connected_geometry_face_mode_lightmap_only':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_lightmap_only'
        case '_connected_geometry_face_mode_breakable':
            ob_nwo.face_mode_override = bool_var
            ob_nwo.face_mode_ui = '_connected_geometry_face_mode_breakable'
        case 'face_draw_distance':
            item.face_draw_distance_override = bool_var
        case 'texcoord_usage':
            item.texcoord_usage_override = bool_var
        case 'face_global_material':
            item.face_global_material_override = bool_var
        case 'ladder':
            item.ladder_override = bool_var
        case 'slip_surface':
            item.slip_surface_override = bool_var
        case 'decal_offset':
            item.decal_offset_override = bool_var
        case 'group_transparents_by_plane':
            item.group_transparents_by_plane_override = bool_var
        case 'no_shadow':
            item.no_shadow_override = bool_var
        case 'precise_position':
            item.precise_position_override = bool_var
        case 'no_lightmap':
            item.no_lightmap_override = bool_var
        case 'no_pvs':
            item.no_pvs_override = bool_var
        # instances
        case 'instanced_collision':
            item.instanced_collision_override = bool_var
        case 'instanced_physics':
            item.instanced_physics_override = bool_var
        case 'cookie_cutter':
            item.cookie_cutter_override = bool_var
        # lightmap
        case 'lightmap_additive_transparency':
            item.lightmap_additive_transparency_override = bool_var
        case 'lightmap_resolution_scale':
            item.lightmap_resolution_scale_override = bool_var
        case 'lightmap_type':
            item.lightmap_type_override = bool_var
        case 'lightmap_analytical_bounce_modifier':
            item.lightmap_analytical_bounce_modifier_override = bool_var
        case 'lightmap_general_bounce_modifier':
            item.lightmap_general_bounce_modifier_override = bool_var
        case 'lightmap_translucency_tint_color':
            item.lightmap_translucency_tint_color_override = bool_var
        case 'lightmap_lighting_from_both_sides':
            item.lightmap_lighting_from_both_sides_override = bool_var
        # material lighting
        case 'emissive':
            item.emissive_override = bool_var

class NWO_FaceDefaultsToggle(NWO_Op):
    bl_idname = "nwo.toggle_defaults"
    bl_label = "Toggle Defaults"
    bl_description = "Toggles the default Face Properties display"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode in ('OBJECT', 'EDIT')

    def execute(self, context):
        
        context.object.nwo.toggle_face_defaults = not context.object.nwo.toggle_face_defaults

        return {'FINISHED'}
    
class NWO_EditMode(NWO_Op):
    """Toggles Edit Mode for face map editing"""
    bl_idname = "nwo.edit_face_map"
    bl_label = "Enter Edit Mode"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode in ('OBJECT', 'EDIT')

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT', toggle=True)

        return {'FINISHED'}

class NWO_FaceLayerAdd(NWO_Op):
    """Adds a face property that will override face properties set in the mesh"""
    bl_idname = "nwo.face_layer_add"
    bl_label = "Add"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode in ('OBJECT', 'EDIT')
    
    new : BoolProperty()

    options: EnumProperty(
        default="region",
        items=[
        ('region', 'Region', ''),
        ('emissive', 'Emissive', ''),
        ('face_global_material', 'Collision Material', ''),
        ('precise_position', 'Precise Position', ''),
        ('instanced_collision', 'Bullet Collision', ''),
        ('instanced_physics', 'Player Collision', ''),
        ('cookie_cutter', 'Cookie Cutter', ''),
        ('seam', 'Seam', ''),
        ('two_sided', "Two Sided", ""),
        ('_connected_geometry_face_type_sky', 'Sky', ''),
        ('_connected_geometry_face_type_seam_sealer', 'Seam Sealer', ''),
        ]
        )
    
    fm_name : StringProperty()
    
    def add_face_layer(self, me, prefix):
        bm = bmesh.from_edit_mesh(me)
        face_layer = bm.faces.layers.int.new(f'{prefix}_{str(uuid4())}')
        # get list of selected faces
        for face in bm.faces:
            if face.select:
                face[face_layer] = 1
        
        bmesh.update_edit_mesh(me)
        return face_layer.name, layer_face_count(bm, face_layer)

    def execute(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        match self.options:
            case 'seam':
                self.fm_name = f'seam {true_bsp(ob.nwo)}:'
            case 'precise_position':
                self.fm_name = 'Uncompressed'
            case '_connected_geometry_face_type_sky':
                self.fm_name = 'Sky'
            case '_connected_geometry_face_type_seam_sealer':
                self.fm_name = 'Seam Sealer'
            case '_connected_geometry_face_mode_render_only':
                self.fm_name = 'Render Only'
            case '_connected_geometry_face_mode_collision_only':
                self.fm_name = 'Collision Only'
            case '_connected_geometry_face_mode_sphere_collision_only':
                self.fm_name = 'Sphere Collision Onlu'
            case '_connected_geometry_face_mode_shadow_only':
                self.fm_name = 'Shadow Only'
            case '_connected_geometry_face_mode_lightmap_only':
                self.fm_name = 'Lightmap Only'
            case '_connected_geometry_face_mode_breakable':
                self.fm_name = 'Breakable'
            case 'two_sided':
                self.fm_name = 'Two Sided'
            case 'ladder':
                self.fm_name = 'Ladder'
            case 'slip_surface':
                self.fm_name = 'Slipsurface'
            case 'decal_offset':
                self.fm_name = 'Decal Offset'
            case 'group_transparents_by_plane':
                self.fm_name = 'Group Transparents By Plane'
            case 'no_shadow':
                self.fm_name = 'No Shadow'
            case 'no_lightmap':
                self.fm_name = 'No Lightmap'
            case 'no_pvs':
                self.fm_name = 'No PVS'
            case 'face_draw_distance':
                self.fm_name = 'draw_distance'
            case 'texcoord_usage':
                self.fm_name = 'texcoord_usage'
            # instances
            case 'instanced_collision':
                self.fm_name = 'projectile_collision'
            case 'instanced_physics':
                self.fm_name = 'sphere_collision'
            case 'cookie_cutter':
                self.fm_name = 'cookie_cutter'
            # lightmap
            case 'lightmap_additive_transparency':
                self.fm_name = 'lightmap_additive_transparency'
            case 'lightmap_resolution_scale':
                self.fm_name = 'lightmap_resolution_scale'
            case 'lightmap_type':
                self.fm_name = 'lightmap_type'
            case 'lightmap_analytical_bounce_modifier':
                self.fm_name = 'lightmap_analytical_bounce_modifier'
            case 'lightmap_general_bounce_modifier':
                self.fm_name = 'lightmap_general_bounce_modifier'
            case 'lightmap_translucency_tint_color':
                self.fm_name = 'lightmap_translucency_tint_color'
            case 'lightmap_lighting_from_both_sides':
                self.fm_name = 'lightmap_lighting_from_both_sides'
            # material lighting
            case 'emissive':
                self.fm_name = 'Emissive'

        if self.fm_name == '':
            self.fm_name = 'default'

        layer_name, face_count = self.add_face_layer(ob.data, self.fm_name)

        bpy.ops.uilist.entry_add(list_path="object.data.nwo.face_props", active_index_path="object.data.nwo.face_props_index")

        toggle_override(context, self.options, True)
        item = ob_nwo.face_props[ob_nwo.face_props_index]
        item.name = self.fm_name
        item.layer_name = layer_name
        item.face_count = face_count
        item.layer_colour = random_colour()
        if self.options == 'region':
            item.region_name_ui = self.fm_name
        elif self.options == 'face_global_material':
            item.face_global_material_ui = self.fm_name
        elif self.options == 'seam':
            closest_bsp = closest_bsp_object(ob)
            if closest_bsp is not None:
                item.seam_adjacent_bsp = true_bsp(closest_bsp.nwo)
            else:
                self.report({'WARNING'}, "No other BSPs in scene. Please create another BSP to use seams")
        context.area.tag_redraw()

        return {'FINISHED'}
    
    def draw(self, context):
        ob = context.object
        ob_nwo = ob.nwo
        layout = self.layout
        row = layout.row()
        if self.options == 'region':
            row.prop(self, "fm_name", text="Region")
            # row.operator_menu_enum("nwo.face_region_list", "region", text='', icon="DOWNARROW_HLT").dialog = True
        else:
            row.prop(self, "fm_name", text="Collision Material")
            # row.operator_menu_enum("nwo.face_global_material_list", "global_material", text='', icon="DOWNARROW_HLT").dialog = True
    
    def invoke(self, context, event):
        self.fm_name = ''
        if self.options in ('region', 'face_global_material'):
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

class NWO_FaceLayerRemove(NWO_Op):
    """Removes a face layer"""
    bl_idname = "nwo.face_layer_remove"
    bl_label = "Remove"

    @classmethod
    def poll(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        return ob_nwo.face_props

    def remove_face_layer(self, me, layer_name):
        bm = bmesh.from_edit_mesh(me)   
        # get list of selected faces
        bm.faces.layers.int.remove(bm.faces.layers.int.get(layer_name))
        bmesh.update_edit_mesh(me)

    def execute(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        item = ob_nwo.face_props[ob_nwo.face_props_index]
        self.remove_face_layer(ob.data, item.layer_name)
        ob_nwo.face_props.remove(ob_nwo.face_props_index)
        if ob_nwo.face_props_index > len(ob_nwo.face_props) - 1:
            ob_nwo.face_props_index += -1
        context.area.tag_redraw()

        return {'FINISHED'}
    
class NWO_FaceLayerAssign(NWO_Op):
    bl_idname = "nwo.face_layer_assign"
    bl_label = "Remove"

    assign : BoolProperty(default=True)

    def edit_layer(self, me, layer_name):
        bm = bmesh.from_edit_mesh(me)
        # get list of selected faces
        face_layer = bm.faces.layers.int.get(layer_name)
        for face in bm.faces:
            if face.select:
                face[face_layer] = int(self.assign)

        bmesh.update_edit_mesh(me)
        return layer_face_count(bm, face_layer)

    def execute(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        item = ob_nwo.face_props[ob_nwo.face_props_index]
        item.face_count = self.edit_layer(ob.data, item.layer_name)
        context.area.tag_redraw()

        return {'FINISHED'}
    
class NWO_FaceLayerSelect(NWO_Op):
    bl_idname = "nwo.face_layer_select"
    bl_label = "Select"

    select : BoolProperty(default=True)

    def select_by_layer(self, me, layer_name):
        bm = bmesh.from_edit_mesh(me)
        # get list of selected faces
        face_layer = bm.faces.layers.int.get(layer_name)
        for face in bm.faces:
            if face[face_layer] == 1:
                face.select = self.select

        bmesh.update_edit_mesh(me)

    def execute(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        item = ob_nwo.face_props[ob_nwo.face_props_index]
        self.select_by_layer(ob.data, item.layer_name)
        return {'FINISHED'}
    
class NWO_FaceLayerMove(NWO_Op):
    bl_idname = "nwo.face_layer_move"
    bl_label = "Move"

    direction: EnumProperty(
        name="Direction",
        items=(('UP', 'UP', 'UP'),
               ('DOWN', 'DOWN', 'DOWN')),
        default='UP'
    )

    @classmethod
    def poll(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        return ob_nwo.face_props

    def execute(self, context):
        ob = context.object
        ob_nwo = ob.data.nwo
        face_layers = ob_nwo.face_props
        active_index = ob_nwo.face_props_index
        delta = {
            "DOWN": 1,
            "UP": -1,
        }[self.direction]

        to_index = (active_index + delta) % len(face_layers)

        face_layers.move(active_index, to_index)
        ob_nwo.face_props_index = to_index

        return {'FINISHED'}
    
class NWO_FaceLayerAddFaceMode(NWO_FaceLayerAdd):
    """Adds a face property that will override face properties set in the mesh"""
    bl_idname = "nwo.face_layer_add_face_mode"
    bl_label = "Add"

    options: EnumProperty(
        items=[
        ('_connected_geometry_face_mode_render_only', 'Render Only', ''),
        ('_connected_geometry_face_mode_collision_only', 'Collision Only', ''),
        ('_connected_geometry_face_mode_sphere_collision_only', 'Sphere Collision Only', ''),
        ('_connected_geometry_face_mode_shadow_only', 'Shadow Only', ''),
        ('_connected_geometry_face_mode_lightmap_only', 'Lightmap Only', ''),
        ('_connected_geometry_face_mode_breakable', 'Breakable', ''),
        ]
        )

class NWO_FaceLayerAddFlags(NWO_FaceLayerAdd):
    """Adds a face property that will override face properties set in the mesh"""
    bl_idname = "nwo.face_layer_add_flags"
    bl_label = "Add"

    options : EnumProperty(
        items=[
        ('ladder', 'Ladder', ''),
        ('slip_surface', 'Slip Surface', ''),
        ('decal_offset', 'Decal Offset', ''),
        ('group_transparents_by_plane', 'Group Transparents by Plane', ''),
        ('no_shadow', 'No Shadow', ''),
        ('no_lightmap', 'No Lightmap', ''),
        ('no_pvs', 'No PVS', ''),
        ]
    )

class NWO_FaceLayerAddLightmap(NWO_FaceLayerAdd):
    """Adds a face property that will override face properties set in the mesh"""
    bl_idname = "nwo.face_layer_add_lightmap"
    bl_label = "Add"

    options : EnumProperty(
        items=[
        ('lightmap_additive_transparency', 'Transparency', ''),
        ('lightmap_resolution_scale', 'Resolution Scale', ''),
        ('lightmap_type', 'Lightmap Type', ''),
        # ('lightmap_analytical_bounce_modifier', 'Analytical Light Bounce Modifier', ''),
        # ('lightmap_general_bounce_modifier', 'General Light Bounce Modifier', ''),
        ('lightmap_translucency_tint_color', 'Translucency Tint Colour', ''),
        ('lightmap_lighting_from_both_sides', 'Lighting from Both Sides', ''),
        ]
    )


class NWO_FaceLayerAddMisc(NWO_FaceLayerAdd):
    """Adds a face property that will override face properties set in the mesh"""
    bl_idname = "nwo.face_layer_add_misc"
    bl_label = "Add"

    options : EnumProperty(
        items=[
        ('face_draw_distance', 'Draw Distance', ''),
        ('texcoord_usage', 'Texcord Usage', ''),
        ]
    )


vertex_shader = '''
in vec3 position;
in vec3 normal;
in vec4 color;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform vec3 camera_location;
uniform float factor1;
uniform float factor2;

out vec4 fcolor;
void main()
{
    
    vec3 pos = vec3(model * vec4(position, 1.0));
    vec3 nor = mat3(transpose(inverse(model))) * normal;
    
    float d = distance(pos, camera_location) * factor1;
    vec3 offset = nor * vec3(d);
    vec3 p = pos + offset;
    //p = pos;
    
    // hmmm?
    //vec3 n = nor * vec3(0.0);
    //nor = nor * vec3(0.0);
    
    vec3 dir = p - camera_location;
    dir = normalize(dir) * vec3(factor2);
    p = p + dir;
    
    //gl_Position = projection * view * model * vec4(position, 1.0);
    //gl_Position = projection * view * model * vec4(p, 1.0);
    gl_Position = projection * view * vec4(p, 1.0);
    //fcolor = color * vec4(offset, 1.0);
    fcolor = color;
    //fcolor = color * vec4(dir / vec3(factor2), 1.0);
}
'''
fragment_shader = '''
in vec4 fcolor;
out vec4 fragColor;
void main()
{
    fragColor = blender_srgb_to_framebuffer_space(fcolor);
}
'''

def draw(self):
    self.shader.bind()
    matrix = bpy.context.region_data.perspective_matrix
    self.shader.uniform_float("ModelViewProjectionMatrix", matrix @ self.o.matrix_world)
    self.shader.uniform_float("color", (self.colour.r, self.colour.g, self.colour.b, 0.25))
    self.batch.draw(self.shader)

class NWO_FaceLayerColour(NWO_Op):
    bl_idname = 'nwo.face_layer_colour'
    bl_options = {'REGISTER'}

    def build_batch(self):
        if len(self.verts):
            self.batch = batch_for_shader(
                self.shader, 'TRIS',
                {"pos": self.verts})
        else:
            self.batch = None

    def ensure_loops(self, bm):
        try:
            if self.loops is None:
                self.loops = bm.calc_loop_triangles()
            else:
                if len(self.loops):
                    looptris = self.loops[0]
                    if len(looptris):
                        loop = looptris[0]
                        loop.face
        except Exception as e:
            self.loops = bm.calc_loop_triangles()
        return self.loops

    def prepare(self, context, layer_name):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        bm = bmesh.from_edit_mesh(self.me)
        self.layer = bm.faces.layers.int.get(layer_name)
        self.verts = [loop.vert.co.to_tuple()
                        for looptris in self.ensure_loops(bm) for loop in looptris
                        if looptris[0].face.hide is False and looptris[0].face[self.layer]] if self.layer else []
        
        self.build_batch()

    def tag_redraw(self):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()
    
    def __init__(self):
        print("start")
    
    def __del__(self):
        print("end")
    
    def modal(self, context, event):
        if context.object.mode != 'EDIT':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
            self.tag_redraw()
            return {'CANCELLED'}
        else:
            pass
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self.o = context.object
        self.me = self.o.data
        item = self.me.nwo.face_props[self.me.nwo.face_props_index]
        self.prepare(context, item.layer_name)
        self.colour = item.layer_colour
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw, (self, ), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        self.tag_redraw()
        return {'RUNNING_MODAL'}

class NWO_RegionListFace(NWO_Op):
    bl_idname = "nwo.face_region_list"
    bl_label = "Region List"
    bl_description = "Applies a region to the selected face layer"

    def regions_items(self, context):
        # get scene regions
        regions = ['default']
        for ob in export_objects():
            region = true_region(ob.nwo)
            if region not in regions:
                regions.append(region)
            # also need to loop through face props
            for face_prop in ob.nwo.data.face_props: 
                if face_prop.region_name_override and face_prop.region_name_ui not in regions:
                    regions.append(face_prop.region_name_ui)

        regions = sort_alphanum(regions)
        items = []
        for index, region in enumerate(regions):
            items.append(bpy_enum_list(region, index))

        return items

    region : EnumProperty(
        name="Region",
        items=regions_items,
    )

    def execute(self, context):
        ob_nwo = context.object.data.nwo
        ob_nwo.face_props[ob_nwo.face_props_index].region_name_ui = self.region
        return {'FINISHED'}
    
class NWO_GlobalMaterialRegionListFace(NWO_RegionListFace):
    bl_idname = "nwo.face_global_material_regions_list"
    bl_label = "Collision Material List"
    bl_description = "Applies a global material to the selected face layer"

    def execute(self, context):
        ob_nwo = context.object.data.nwo
        ob_nwo.face_props[ob_nwo.face_props_index].face_global_material_ui = self.region
        return {'FINISHED'}
    
class NWO_GlobalMaterialListFace(NWO_Op):
    bl_idname = "nwo.face_global_material_list"
    bl_label = "Collision Material List"
    bl_description = "Applies a Collision Material to the selected face layer"

    def global_material_items(self, context):
        # get scene regions
        global_materials = ['default']
        for ob in export_objects():
            global_material = ob.nwo.face_global_material_ui
            if global_material not in global_materials and global_material:
                global_materials.append(global_material)
            # also need to loop through face props
            for face_prop in ob.data.nwo.face_props:
                if face_prop.face_global_material_override and face_prop.face_global_material_ui not in global_materials:
                    global_materials.append(face_prop.face_global_material_ui)

        global_materials = sort_alphanum(global_materials)
        items = []
        for index, global_material in enumerate(global_materials):
            items.append(bpy_enum_list(global_material, index))

        return items

    global_material : EnumProperty(
        name="Collision Material",
        items=global_material_items,
    )

    dialog : BoolProperty()

    def execute(self, context):
        ob_nwo = context.object.data.nwo
        ob_nwo.face_props[ob_nwo.face_props_index].face_global_material_ui = self.global_material
        return {'FINISHED'}

class NWO_GlobalMaterialMenuFace(bpy.types.Menu):
    bl_label = "Add Collision Material"
    bl_idname = "NWO_MT_AddGlobalMaterialFace"

    def draw(self, context):
        layout = self.layout
        ob = context.object
        global_materials = ['default']
        for ob in export_objects():
            global_material = ob.nwo.face_global_material_ui
            if global_material not in global_materials:
                global_materials.append(global_material)
            # also need to loop through face props
            for face_prop in ob.data.nwo.face_props:
                if face_prop.face_global_material_override and face_prop.face_global_material not in global_materials:
                    global_materials.append(face_prop.face_global_material)

        for g_mat in global_materials:
            layout.operator("nwo.global_material_list", text=g_mat).global_material = g_mat

        if poll_ui(('MODEL', 'SKY')):
            layout.operator_menu_enum("nwo.face_global_material_regions_list",
                                    property="region",
                                    text="From Region",
                                    )