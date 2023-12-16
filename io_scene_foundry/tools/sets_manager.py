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

'''Handles bpy operators and functions for the Sets Manager panel'''

import bpy
from io_scene_foundry.icons import get_icon_id
from io_scene_foundry.managed_blam.scenario import ScenarioTag

from io_scene_foundry.utils.nwo_utils import is_corinth, poll_ui, true_permutation, true_region, valid_nwo_asset

# Parent Classes
class TableEntryAdd(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    set_object_prop: bpy.props.BoolProperty()
    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        name = self.name.lower()
        nwo = context.scene.nwo
        table = getattr(nwo, self.table_str)
        all_names = [entry.name for entry in table]

        if not name:
            self.report({'WARNING'}, f"{self.type_str} name cannot be empty")
            return {'CANCELLED'}
        elif len(name) > 128:
            self.report({'WARNING'}, f"{self.type_str} name has a maximum of 128 characters")
            return {'CANCELLED'}
        elif name in all_names:
            self.report({'WARNING'}, f"{self.type_str} name already exists")
            return {'CANCELLED'}
    
        entry = table.add()
        entry.old = name
        entry.name = name
        setattr(nwo, f"{self.table_str}_active_index", len(table) - 1)
        if self.set_object_prop:
            ob = context.object
            if ob: setattr(ob.nwo, self.ob_prop_str, name)

        context.area.tag_redraw()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.activate_init = True
        layout.prop(self, "name", text="Name")

class TableEntryRemove(bpy.types.Operator):
    bl_options = {'UNDO'}

    def execute(self, context):
        nwo = context.scene.nwo
        table = getattr(nwo, self.table_str)
        table_active_index_str = f"{self.table_str}_active_index"
        table_active_index = getattr(nwo, table_active_index_str)
        entry = table[table_active_index]
        scene_objects = context.scene.objects
        entry_objects = [ob for ob in scene_objects if getattr(ob.nwo, self.ob_prop_str) == entry.name]
        table.remove(table_active_index)
        if table_active_index > len(table) - 1:
            setattr(nwo, table_active_index_str, table_active_index - 1)
        new_entry_name = table[0].name
        for ob in entry_objects:
            setattr(ob.nwo, self.ob_prop_str, new_entry_name)
        context.area.tag_redraw()
        return {'FINISHED'}
    
class TableEntryMove(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    direction: bpy.props.StringProperty()

    def execute(self, context):
        nwo = context.scene.nwo
        table = getattr(nwo, self.table_str)
        table_active_index_str = f"{self.table_str}_active_index"
        table_active_index = getattr(nwo, table_active_index_str)
        delta = {"down": 1, "up": -1,}[self.direction]
        current_index = table_active_index
        to_index = (current_index + delta) % len(table)
        table.move(current_index, to_index)
        setattr(nwo, table_active_index_str, to_index)

        context.area.tag_redraw()
        return {'FINISHED'}

class TableEntryAssignSingle(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    name: bpy.props.StringProperty(
        name="Name",
    )
    
    def execute(self, context):
        nwo = context.object.nwo
        old_name = getattr(nwo, self.ob_prop_str)
        setattr(nwo, self.ob_prop_str, self.name)
        if self.ob_prop_str == "region_name_ui" and nwo.seam_back_ui == self.name:
            nwo.seam_back_ui = old_name
        return {'FINISHED'}
    
class TableEntryAssign(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    name: bpy.props.StringProperty(
        name="Name",
    )
    
    def execute(self, context):
        sel_obs = context.selected_objects
        for ob in sel_obs:
            old_name = getattr(ob.nwo, self.ob_prop_str)
            setattr(ob.nwo, self.ob_prop_str, self.name)
            if self.ob_prop_str == "region_name_ui" and ob.nwo.seam_back_ui == self.name:
                ob.nwo.seam_back_ui = old_name
        return {'FINISHED'}
    
class TableEntrySelect(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    select: bpy.props.BoolProperty()
    
    def execute(self, context):
        nwo = context.scene.nwo
        table = getattr(context.scene.nwo, self.table_str)
        table_active_index_str = f"{self.table_str}_active_index"
        table_active_index = getattr(nwo, table_active_index_str)
        entry = table[table_active_index]
        available_objects = context.view_layer.objects
        entry_objects = [ob for ob in available_objects if true_table_entry(ob.nwo, self.ob_prop_str) == entry.name]
        [ob.select_set(self.select) for ob in entry_objects]
        return {'FINISHED'}
    
class TableEntryRename(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}
    
    new_name: bpy.props.StringProperty(
        name="New Name",
    )

    index: bpy.props.IntProperty()
    
    def execute(self, context):
        nwo = context.scene.nwo
        new_name = self.new_name.lower()
        table = getattr(nwo, self.table_str)
        table_active_index = self.index
        all_names = [entry.name for entry in table]
        all_names.pop(table_active_index)
        entry = table[table_active_index]

        if not entry.old:
            entry.old = 'default'

        if not new_name:
            self.report({'WARNING'}, f"{self.type_str} name cannot be empty")
            entry.name = entry.old
            return {'CANCELLED'}
        elif len(new_name) > 128:
            self.report({'WARNING'}, f"{self.type_str} name has a maximum of 128 characters")
            entry.name = entry.old
            return {'CANCELLED'}
        elif new_name in all_names:
            self.report({'WARNING'}, f"{self.type_str} name already exists")
            entry.name = entry.old
            return {'CANCELLED'}
        
        scene_objects = context.scene.objects
        entry_objects = [ob for ob in scene_objects if getattr(ob.nwo, self.ob_prop_str) == entry.old]
        old_name = str(entry.old)
        entry.old = new_name
        entry.name = new_name
        for ob in entry_objects:
            setattr(ob.nwo, self.ob_prop_str, new_name)
        scene_collections = bpy.data.collections
        current_type = self.type_str.lower()
        is_scenario = poll_ui(('SCENARIO', 'PREFAB'))
            
        for coll in scene_collections:
            c_parts = coll.name.split('::')
            if not c_parts or len(c_parts) != 2: continue
            if coll.nwo.type != current_type or c_parts[1] != old_name: continue
            true_type = current_type
            if current_type == 'region' and is_scenario:
                true_type = 'bsp'
            elif current_type == 'permutation' and is_scenario:
                true_type = 'layer'
            coll.name = true_type + '::' + self.new_name

        if hasattr(context.area, 'tag_redraw'):
            context.area.tag_redraw()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.activate_init = True
        layout.prop(self, "new_name", text="New Name")

class TableEntryHide(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    entry_name: bpy.props.StringProperty()
    
    def execute(self, context):
        nwo = context.scene.nwo
        table = getattr(nwo, self.table_str)
        entry = get_entry(table, self.entry_name)
        should_hide = entry.hidden
        available_objects = context.view_layer.objects
        entry_objects = [ob for ob in available_objects if true_table_entry(ob.nwo, self.ob_prop_str) == entry.name]
        [ob.hide_set(should_hide) for ob in entry_objects]
        return {'FINISHED'}
    
class TableEntryHideSelect(bpy.types.Operator):
    bl_options = {'UNDO'}
    
    entry_name: bpy.props.StringProperty()
    
    def execute(self, context):
        nwo = context.scene.nwo
        table = getattr(nwo, self.table_str)
        entry = get_entry(table, self.entry_name)
        should_hide_select = entry.hide_select
        available_objects = context.view_layer.objects
        entry_objects = [ob for ob in available_objects if true_table_entry(ob.nwo, self.ob_prop_str) == entry.name]
        for ob in entry_objects:
            ob.hide_select = should_hide_select
        return {'FINISHED'}

# REGIONS
class NWO_RegionAdd(TableEntryAdd):
    bl_label = ""
    bl_idname = "nwo.region_add"
    bl_description = "Add a new Region"

    def __init__(self):
        self.type_str = "Region"
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Add a new BSP"
        else:
            return "Add a new Region"

class NWO_FaceRegionAdd(bpy.types.Operator):
    bl_label = ""
    bl_idname = "nwo.face_region_add"
    bl_description = "Add a new Region"
    bl_options = {'UNDO'}

    set_object_prop: bpy.props.BoolProperty()
    name: bpy.props.StringProperty()

    def execute(self, context):
        name = self.name.lower()
        nwo = context.scene.nwo
        table = getattr(nwo, "regions_table")
        all_names = [entry.name for entry in table]

        if not name:
            self.report({'WARNING'}, f"Region name cannot be empty")
            return {'CANCELLED'}
        elif len(name) > 128:
            self.report({'WARNING'}, f"Region name has a maximum of 128 characters")
            return {'CANCELLED'}
        elif name in all_names:
            self.report({'WARNING'}, f"Region name already exists")
            return {'CANCELLED'}
    
        entry = table.add()
        entry.old = name
        entry.name = name
        setattr(nwo, f"regions_table_active_index", len(table) - 1)
        if self.set_object_prop:
            ob = context.object
            if ob and ob.type == 'MESH':
                face_layer = ob.data.nwo.face_props[ob.data.nwo.face_props_index]
                face_layer.region_name_ui = name
            

        context.area.tag_redraw()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.activate_init = True
        layout.prop(self, "name", text="Name")

class NWO_RegionRemove(TableEntryRemove):
    bl_label = ""
    bl_idname = "nwo.region_remove"
    bl_description = "Removes the active Region"

    @classmethod
    def poll(cls, context):
        return len(context.scene.nwo.regions_table) > 1

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Removes the active BSP"
        else:
            return "Removes the active Region"
    
class NWO_RegionMove(TableEntryMove):
    bl_label = ""
    bl_idname = "nwo.region_move"
    bl_description = "Moves the active Region"

    @classmethod
    def poll(cls, context):
        return len(context.scene.nwo.regions_table) > 1

    def __init__(self):
        self.table_str = "regions_table"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Moves the active BSP"
        else:
            return "Moves the active Region"
    
class NWO_RegionAssignSingle(TableEntryAssignSingle):
    bl_label = ""
    bl_idname = "nwo.region_assign_single"
    bl_description = "Assigns the active Region to the active Object"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table and context.object

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Assigns the selected BSP to the active Object"
        else:
            return "Assigns the selected Region to the active Object"
        
class NWO_FaceRegionAssignSingle(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_label = ''
    bl_idname = 'nwo.face_region_assign_single'
    bl_description = "Assigns the active Region to the active face layer"
    
    name: bpy.props.StringProperty(
        name="Name",
    )
    
    def execute(self, context):
        ob = context.object
        if not ob or ob.type != 'MESH':
            return {'CANCELLED'}
        face_layer = ob.data.nwo.face_props[ob.data.nwo.face_props_index]
        face_layer.region_name_ui = self.name
        lay_parts = face_layer.name.split('::')
        if lay_parts and len(lay_parts) == 2 and lay_parts[0] == 'region':
            face_layer.name = 'region::' + self.name
        return {'FINISHED'}
    
class NWO_RegionAssign(TableEntryAssign):
    bl_label = ""
    bl_idname = "nwo.region_assign"
    bl_description = "Assigns the active Region to selected Objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table and context.selected_objects

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Assigns the active BSP to selected Objects"
        else:
            return "Assigns the active Region to selected Objects"
    
class NWO_RegionSelect(TableEntrySelect):
    bl_label = ""
    bl_idname = "nwo.region_select"
    bl_description = "Selects/Deselects the active Region"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.select:
                return "Selects the active BSP"
            else:
                return "Deselects the active BSP"
        else:
            if properties.select:
                return "Selects the active Region"
            else:
                return "Deselects the active Region"
    
class NWO_RegionRename(TableEntryRename):
    bl_label = ""
    bl_idname = "nwo.region_rename"
    bl_description = "Renames the active Region and updates scene objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table

    def __init__(self):
        self.type_str = "Region"
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Renames the active BSP and updates scene objects"
        else:
            return "Renames the active Region and updates scene objects"
    
class NWO_RegionHide(TableEntryHide):
    bl_label = ""
    bl_idname = "nwo.region_hide"
    bl_description = "Hides/Unhides the active Region"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.hidden:
                return "Unhides the active BSP"
            else:
                return "Hides the active BSP"
        else:
            if properties.select:
                return "Unhides the active Region"
            else:
                return "Hides the active Region"

class NWO_RegionHideSelect(TableEntryHideSelect):
    bl_label = ""
    bl_idname = "nwo.region_hide_select"
    bl_description = "Disables selection of the active Region objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "region_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.hide_select:
                return "Enables selection of the active BSP objects"
            else:
                return "Disables selection of the active BSP objects"
        else:
            if properties.select:
                return "Enables selection of the active Region objects"
            else:
                return "Disables selection of the active Region objects"

# PERMUTATIONS
class NWO_PermutationAdd(TableEntryAdd):
    bl_label = ""
    bl_idname = "nwo.permutation_add"
    bl_description = "Add a new Permutation"

    def __init__(self):
        self.type_str = "Permutation"
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Add a new Layer"
        else:
            return "Add a new Permutation"

class NWO_PermutationRemove(TableEntryRemove):
    bl_label = ""
    bl_idname = "nwo.permutation_remove"
    bl_description = "Removes the active Permutation"

    @classmethod
    def poll(cls, context):
        return len(context.scene.nwo.permutations_table) > 1

    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Removes the active Layer"
        else:
            return "Removes the active Permutation"
    
class NWO_PermutationMove(TableEntryMove):
    bl_label = ""
    bl_idname = "nwo.permutation_move"
    bl_description = "Moves the active Permutation"

    @classmethod
    def poll(cls, context):
        return len(context.scene.nwo.permutations_table) > 1

    def __init__(self):
        self.table_str = "permutations_table"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Moves the active Layer"
        else:
            return "Moves the active Permutation"
    
class NWO_PermutationAssignSingle(TableEntryAssignSingle):
    bl_label = ""
    bl_idname = "nwo.permutation_assign_single"
    bl_description = "Assigns the selected Permutation to the active Object"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table and context.object
    
    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Assigns the selected Layer to the active Object"
        else:
            return "Assigns the selected Permutation to the active Object"
    
class NWO_PermutationAssign(TableEntryAssign):
    bl_label = ""
    bl_idname = "nwo.permutation_assign"
    bl_description = "Assigns the active Permutation to selected Objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table and context.selected_objects

    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Assigns the active Layer to selected Objects"
        else:
            return "Assigns the active Permutation to selected Objects"
    
class NWO_PermutationSelect(TableEntrySelect):
    bl_label = ""
    bl_idname = "nwo.permutation_select"
    bl_description = "Selects/Deselects the active Permutation"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table

    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.select:
                return "Selects the active Layer"
            else:
                return "Deselects the active Layer"
        else:
            if properties.select:
                return "Selects the active Permutation"
            else:
                return "Deselects the active Permutation"
    
class NWO_PermutationRename(TableEntryRename):
    bl_label = ""
    bl_idname = "nwo.permutation_rename"
    bl_description = "Renames the active Permutation and updates scene objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table

    def __init__(self):
        self.type_str = "Permutation"
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            return "Renames the active Layer and updates scene objects"
        else:
            return "Renames the active Permutation and updates scene objects"
    
class NWO_PermutationHide(TableEntryHide):
    bl_label = ""
    bl_idname = "nwo.permutation_hide"
    bl_description = "Hides/Unhides the active Permutation"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table

    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.hide_select:
                return "Enables selection of the active Layer objects"
            else:
                return "Disables selection of the active Layer objects"
        else:
            if properties.select:
                return "Enables selection of the active Permutation objects"
            else:
                return "Disables selection of the active Permutation objects"

class NWO_PermutationHideSelect(TableEntryHideSelect):
    bl_label = ""
    bl_idname = "nwo.permutation_hide_select"
    bl_description = "Disable selection of the active Permutation objects"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.permutations_table

    def __init__(self):
        self.table_str = "permutations_table"
        self.ob_prop_str = "permutation_name_ui"

    @classmethod
    def description(cls, context, properties) -> str:
        is_scenario = context.scene.nwo.asset_type == 'SCENARIO'
        if is_scenario:
            if properties.hide_select:
                return "Enables selection of the active Layer objects"
            else:
                return "Disables selection of the active Layer objects"
        else:
            if properties.select:
                return "Enables selection of the active Permutation objects"
            else:
                return "Disables selection of the active Permutation objects"


class NWO_SeamAssignSingle(TableEntryAssignSingle):
    bl_label = ""
    bl_idname = "nwo.seam_backface_assign_single"
    bl_description = "Sets the selected BSP as this seam's backfacing BSP reference"

    @classmethod
    def poll(cls, context):
        return context.scene.nwo.regions_table and context.object

    def __init__(self):
        self.table_str = "regions_table"
        self.ob_prop_str = "seam_back_ui"

# HELPER FUNCTIONS

def get_entry(table, entry_name):
    for entry in table:
        if entry.name == entry_name:
            return entry
        
def true_table_entry(nwo, ob_prop_str):
    if ob_prop_str == "region_name_ui":
        return true_region(nwo)
    elif ob_prop_str == "permutation_name_ui":
        return true_permutation(nwo)
    
    
# COOL TOOLS MENU
class NWO_BSPContextMenu(bpy.types.Menu):
    bl_idname = "NWO_MT_BSPContextMenu"
    bl_label = "BSP Context Menu"
        
    def draw(self, context):
        layout = self.layout
        layout.operator("nwo.print_bsp_info", text="Show BSP Info", icon='INFO')
        layout.operator("nwo.set_bsp_lightmap_res", text="Set BSP Lightmap Resolution", icon='OUTLINER_DATA_LIGHTPROBE')
        if is_corinth(context):
            layout.operator("nwo.set_default_sky", text="Set BSP Sky", icon_value=get_icon_id("sky"))
        
        
class NWO_BSPInfo(bpy.types.Operator):
    bl_idname = "nwo.print_bsp_info"
    bl_label = "Show BSP Info"
    bl_description = "Outputs information about the selected BSP"
    
    @classmethod
    def poll(cls, context):
        return poll_ui(('SCENARIO',)) and valid_nwo_asset(context)
        
    def execute(self, context):
        self.info = None
        nwo = context.scene.nwo
        bsp = nwo.regions_table[nwo.regions_table_active_index].name
        with ScenarioTag() as scenario:
            self.info = scenario.get_bsp_info(bsp)
        
        if self.info is None:
            self.report({'WARNING'}, f"BSP {bsp} does not exist in scenario tag. You may need to export this scene")
            return {'CANCELLED'}
        return context.window_manager.invoke_popup(self)
    
    def draw(self, context):
        layout = self.layout
        for k, v in self.info.items():
            layout.label(text=f'{k}: {v}')
            
class NWO_BSPSetLightmapRes(bpy.types.Operator):
    bl_idname = "nwo.set_bsp_lightmap_res"
    bl_label = "Set BSP Lightmap Resolution"
    bl_description = "Sets the lightmap resolution (size class) for this BSP. If this is a H4+ project, then it also allows you set the refinement size class"
    
    def size_class_items(self, context):
        items = []
        if is_corinth(context):
            items.append(("0", "32x32", ""))
            items.append(("1", "64x64", ""))
            items.append(("2", "128x128", ""))
            items.append(("3", "256x256", ""))
            items.append(("4", "512x512", ""))
            items.append(("5", "768x768", ""))
            items.append(("6", "1024x1024", ""))
            items.append(("7", "1280x1280", ""))
            items.append(("8", "1536x1536", ""))
            items.append(("9", "1792x1792", ""))
            items.append(("10", "2048x2048", ""))
            items.append(("11", "2304x2304", ""))
            items.append(("12", "2560x2560", ""))
            items.append(("13", "2816x2816", ""))
            items.append(("14", "3072x3072", ""))
        else:
            items.append(("0", "256x256", ""))
            items.append(("1", "512x512", ""))
            items.append(("2", "768x768", ""))
            items.append(("3", "1024x1024", ""))
            items.append(("4", "1280x1280", ""))
            items.append(("5", "1536x1536", ""))
            items.append(("6", "1792x1792", ""))
            
        return items
    
    size_class: bpy.props.EnumProperty(
        name="Lightmap Resolution",
        items=size_class_items
    )
    
    def refinement_size_class_items(self, context):
        items=[
            ("0", "4096x1024", ""),
            ("1", "1024x1024", ""),
            ("2", "2048x1024", ""),
            ("3", "6144x1024", ""),
        ]
        
        return items
    
    refinement_size_class: bpy.props.EnumProperty(
        name="Lightmap Refinement",
        items=refinement_size_class_items,
    )
    
    @classmethod
    def poll(cls, context):
        return poll_ui(('SCENARIO',)) and valid_nwo_asset(context)
        
    def execute(self, context):
        self.info = None
        nwo = context.scene.nwo
        bsp = nwo.regions_table[nwo.regions_table_active_index].name
        with ScenarioTag() as scenario:
            success = scenario.set_bsp_lightmap_res(bsp, int(self.size_class), int(self.refinement_size_class))
            if not success:
                self.report({'WARNING'}, f"BSP {bsp} does not exist in scenario tag. You may need to export this scene")
                return {'CANCELLED'}
        
        if is_corinth(context):
            self.report({'INFO'}, f"Set lightmap resolution of {self.size_class_items(context)[int(self.size_class)][1]} and refinement class of {self.refinement_size_class_items(context)[int(self.refinement_size_class)][1]}")
        else:
            self.report({'INFO'}, f"Set lightmap resolution of {self.size_class}")
        
        return {'FINISHED'}
    
    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "size_class", text="Resolution")
        if is_corinth(context):
            layout.prop(self, "refinement_size_class", text="Refinement")