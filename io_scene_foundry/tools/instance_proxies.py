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

"""Handles the creation and maintenance of instance proxy objects - physics, collision & cookie cutters"""

import bmesh
import bpy
from io_scene_foundry.tools.property_apply import apply_props_material

from io_scene_foundry.utils.nwo_utils import deselect_all_objects, layer_faces, set_active_object, set_object_mode, unlink

class NWO_ProxyInstanceEdit(bpy.types.Operator):
    bl_idname = "nwo.proxy_instance_edit"
    bl_description = "Switches to Proxy instance edit mode"
    bl_label = "Instance Proxy Mode"

    proxy : bpy.props.StringProperty()

    _timer = None

    def execute(self, context):
        self.old_sel = context.selected_objects.copy()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                view_3d = area.spaces.active
                if view_3d.local_view:
                    bpy.ops.view3d.localview()
                    break

        set_object_mode(context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.parent = context.object
        self.proxy_ob = bpy.data.objects[self.proxy]
        self.scene_coll = context.scene.collection.objects
        self.scene_coll.link(self.proxy_ob)
        self.proxy_ob.select_set(True)
        self.proxy_ob.matrix_world = self.parent.matrix_world

        bpy.ops.view3d.localview()
        deselect_all_objects()
        self.proxy_ob.select_set(True)
        set_active_object(self.proxy_ob)
        bpy.ops.object.editmode_toggle()
        context.scene.nwo.instance_proxy_running = True
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        scene_nwo = context.scene.nwo
        active = scene_nwo.instance_proxy_running
        edit_mode = context.mode == 'EDIT_MESH'
        
        if event.type == 'TIMER' and not (active and edit_mode):
            if context.mode == 'EDIT_MESH':
                bpy.ops.object.editmode_toggle()

            bpy.ops.view3d.localview()
            self.proxy_ob.select_set(False)
            unlink(self.proxy_ob)
            for sel_ob in self.old_sel:
                sel_ob.select_set(True)
            set_active_object(self.parent)
            scene_nwo.instance_proxy_running = False
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        context.scene.instance_proxy_running = False

class NWO_ProxyInstanceNew(bpy.types.Operator):
    bl_idname = "nwo.proxy_instance_new"
    bl_description = "New Proxy Instance"
    bl_label = "Instance Proxy New"

    proxy_type : bpy.props.EnumProperty(
        name="Type",
        items=[
            ("collision", "Collision", ""),
            ("physics", "Physics", ""),
            ("cookie_cutter", "Cookie Cutter", ""),
        ]
    )

    proxy_source : bpy.props.EnumProperty(
        name="Source",
        items=[
            ("bounding_box", "Bounding Box", ""),
            ("copy", "Copy", ""),
            ("existing", "Scene Mesh", ""),
        ]
    )

    proxy_copy : bpy.props.StringProperty(
        name="Mesh"
    )

    proxy_edit : bpy.props.BoolProperty(
        name="Edit",
        default=True
    )

    def build_bounding_box(self):
        me = bpy.data.meshes.new(self.proxy_name)
        ob = bpy.data.objects.new(self.proxy_name, me)
        bm = bmesh.new()
        bbox = self.parent.bound_box
        for co in bbox:
            bmesh.ops.create_vert(bm, co=co)

        bm.verts.ensure_lookup_table()
        back_face = [bm.verts[0], bm.verts[1], bm.verts[2], bm.verts[3]]
        front_face = [bm.verts[4], bm.verts[5], bm.verts[6], bm.verts[7]]
        left_face = [bm.verts[0], bm.verts[1], bm.verts[4], bm.verts[5]]
        right_face = [bm.verts[2], bm.verts[3], bm.verts[6], bm.verts[7]]
        bottom_face = [bm.verts[0], bm.verts[3], bm.verts[4], bm.verts[7]]
        top_face = [bm.verts[1], bm.verts[2], bm.verts[5], bm.verts[6]]
        bmesh.ops.contextual_create(bm, geom=back_face, mat_nr=0, use_smooth=False)
        bmesh.ops.contextual_create(bm, geom=front_face, mat_nr=0, use_smooth=False)
        bmesh.ops.contextual_create(bm, geom=left_face, mat_nr=0, use_smooth=False)
        bmesh.ops.contextual_create(bm, geom=right_face, mat_nr=0, use_smooth=False)
        bmesh.ops.contextual_create(bm, geom=bottom_face, mat_nr=0, use_smooth=False)
        bmesh.ops.contextual_create(bm, geom=top_face, mat_nr=0, use_smooth=False)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)

        return ob

    def build_from_parent(self):
        bm = bmesh.new()
        bm.from_mesh(self.parent.data)

        # cut out render_only faces
        for f in bm.faces:
            f.smooth = False
            f.select = False

        face_layers = self.parent.data.nwo.face_props
        layer_faces_dict = {
            layer: layer_faces(bm, bm.faces.layers.int.get(layer.layer_name))
            for layer in face_layers
        }
        
        for layer, face_seq in layer_faces_dict.items():
            face_count = len(face_seq)
            if not face_count:
                continue
            if layer.face_mode_override and layer.face_mode_ui in (
                "_connected_geometry_face_mode_render_only",
                "_connected_geometry_face_mode_lightmap_only",
                "_connected_geometry_face_mode_shadow_only",
            ):
                for f in face_seq:
                    f.select = True

        selected = [f for f in bm.faces if f.select]
        bmesh.ops.delete(bm, geom=selected, context="FACES")

        # make new object to take this bmesh
        me = bpy.data.meshes.new(self.proxy_name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(me.name, me)

        return ob
    
    def copy_mesh(self):
        me = bpy.data.meshes.new(self.proxy_name)
        bm = bmesh.new()
        bm.from_mesh(bpy.data.meshes[self.proxy_copy])
        for f in bm.faces:
            f.smooth = False

        bm.to_mesh(me)
        ob = bpy.data.objects.new(self.proxy_name, me)
        
        return ob

    def execute(self, context):
        self.parent = context.object
        # self.scene_coll = context.scene.collection.objects
        self.proxy_name = f"{self.parent.name}_proxy_{self.proxy_type}"
        if self.proxy_source == "bounding_box":
            ob = self.build_bounding_box()
        elif self.proxy_source == "copy":
            ob = self.build_from_parent()
        else:
            ob = self.copy_mesh()

        # self.scene_coll.link(ob)
        ob.nwo.proxy_parent = self.parent.data
        ob.nwo.proxy_type = self.proxy_type

        setattr(self.parent.data.nwo, f"proxy_{self.proxy_type}", ob)
        if self.proxy_type == "collision":
            apply_props_material(ob, "Collision")
        elif self.proxy_type == "physics":
            apply_props_material(ob, "Physics")
        else:
            apply_props_material(ob, "CookieCutter")

        if self.proxy_edit:
            bpy.ops.nwo.proxy_instance_edit(proxy=ob.name)
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()
        col.prop(self, "proxy_type", text="Type")
        col.prop(self, "proxy_source", text="Source")
        if self.proxy_source == "existing":
            col.prop_search(self, "proxy_copy", search_data=bpy.data, search_property="meshes")
        col.prop(self, "proxy_edit", text="Edit Proxy")
    
class NWO_ProxyInstanceDelete(bpy.types.Operator):
    bl_idname = "nwo.proxy_instance_delete"
    bl_description = "Deletes a proxy object"
    bl_label = "Instance Proxy Delete"

    proxy : bpy.props.StringProperty()

    def execute(self, context):
        proxy_ob = bpy.data.objects[self.proxy]
        bpy.data.objects.remove(proxy_ob)
        return {'FINISHED'}
    
class NWO_ProxyInstanceCancel(bpy.types.Operator):
    bl_idname = "nwo.proxy_instance_cancel"
    bl_description = "Cancels Proxy Instance Edit"
    bl_label = "Instance Proxy Cancel"

    proxy : bpy.props.StringProperty()

    def execute(self, context):
        context.scene.nwo.instance_proxy_running = False
        return {'FINISHED'}