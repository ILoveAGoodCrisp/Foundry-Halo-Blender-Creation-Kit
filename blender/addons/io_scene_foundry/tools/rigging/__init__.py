# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2024 Crisp
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

import bpy
from mathutils import Vector

bone_x = 0, 0.1, 0
bone_x_negative = 0, -0.1, 0
bone_y = -0.1, 0, 0
bone_y_negative = 0.1, 0, 0

pedestal_name, aim_pitch_name, aim_yaw_name = 'pedestal', 'aim_pitch', 'aim_yaw'
pedestal_control_name, aim_control_name = 'CTRL_pedestal', 'CTRL_aim'
pedestal_shape_name, aim_shape_name = 'pedestal_shape', 'aim_shape'

pedestal_shape_vert_coords = [(0.809309, 0.60584, 0.0), (0.756688, 0.674648, 0.0), (0.690572, 0.74488, 0.0), (0.625647, 0.799433, 0.0), (0.552399, 0.849233, 0.0), (0.472018, 0.893502, 1e-06), (0.385693, 0.931465, 1e-06), (0.294613, 0.962344, 1e-06), (0.199964, 0.985363, 1e-06), (0.10294, 0.999742, 1e-06), (0.004724, 1.004709, 1e-06), (-0.093539, 0.999675, 1e-06), (-0.190899, 0.984823, 1e-06), (-0.28646, 0.960528, 1e-06), (-0.379317, 0.927159, 1e-06), (-0.468572, 0.885094, 1e-06), (-0.553322, 0.834703, 0.0), (-0.63267, 0.776358, 0.0), (-0.705711, 0.710436, 0.0), (-0.771635, 0.637395, 0.0), (-0.829979, 0.558048, 0.0), (-0.880369, 0.473297, 0.0), (-0.922439, 0.384043, 0.0), (-0.955806, 0.291185, 0.0), (-0.980101, 0.195624, 0.0), (-0.99495, 0.098263, 0.0), (-0.999985, -0.0, -0.0), (-0.99495, -0.098263, -0.0), (-0.980101, -0.195624, -0.0), (-0.955806, -0.291185, -0.0), (-0.922439, -0.384043, -0.0), (-0.880369, -0.473297, -0.0), (-0.829979, -0.558048, -0.0), (-0.771635, -0.637395, -0.0), (-0.705711, -0.710435, -0.0), (-0.63267, -0.776358, -0.0), (-0.553322, -0.834703, -0.0), (-0.468572, -0.885094, -1e-06), (-0.379317, -0.927159, -1e-06), (-0.28646, -0.960527, -1e-06), (-0.190899, -0.984823, -1e-06), (-0.093538, -0.999675, -1e-06), (0.004724, -1.004709, -1e-06), (0.102987, -0.999675, -1e-06), (0.200348, -0.984823, -1e-06), (0.295908, -0.960527, -1e-06), (0.388767, -0.92716, -1e-06), (0.478021, -0.885094, -1e-06), (0.562772, -0.834703, -0.0), (0.642119, -0.776358, -0.0), (0.71516, -0.710435, -0.0), (0.768886, -0.652072, -0.0), (0.817734, -0.589496, -0.0), (0.861507, -0.523183, -0.0), (0.90001, -0.4536, -0.0), (1.13563, -0.4536, -0.0), (1.13563, -0.9072, -1e-06), (2.042828, -0.0, -0.0), (1.135629, 0.9072, 1e-06), (1.13563, 0.4536, 0.0), (0.902965, 0.454077, 0.0), (0.859238, 0.528559, 0.0)]
aim_shape_vert_coords = [(1.955878, 0.885051, 0.0), (1.95143, -0.887275, 0.0), (2.307979, 0.003538, 0.0), (3.72598, 0.0, 0.0)]
pedestal_shape_faces = [[61, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]]
aim_shape_faces = [[1, 3, 0, 2]]

class HaloRig:
    def __init__(self, context: bpy.types.Context, scale, forward, has_pedestal_control=False, has_pose_bones=False, has_aim_control=False, set_scene_rig_props=False):
        self.context = context
        self.scale = scale
        self.forward = forward
        self.has_pedestal_control = has_pedestal_control
        self.has_pose_bones = has_pose_bones
        self.has_aim_control = has_aim_control
        self.set_scene_rig_props = set_scene_rig_props
    
    def build_and_apply_control_shapes(self, pedestal=None, pedestal_control=None, pitch=None, yaw=None, aim_control=None):
        if self.has_pedestal_control:
            if pedestal is None:
                pedestal: bpy.types.PoseBone = self.rig_ob.pose.bones.get(pedestal_name)
            if pedestal_control is None:
                pedestal_control: bpy.types.PoseBone = self.rig_ob.pose.bones.get(pedestal_control_name)
            shape_ob = bpy.data.objects.get(pedestal_shape_name)
            if shape_ob is None:
                shape_data = bpy.data.meshes.new(pedestal_shape_name)
                verts = [Vector(co) for co in pedestal_shape_vert_coords]
                shape_data.from_pydata(vertices=verts, edges=[], faces=pedestal_shape_faces)
                shape_ob = bpy.data.objects.new(pedestal_shape_name, shape_data)
            
            shape_ob.nwo.export_this = False
            pedestal_control.custom_shape = shape_ob
            pedestal_control.custom_shape_scale_xyz *= self.scale
            pedestal_control.use_custom_shape_bone_size = False
            con = pedestal.constraints.new('COPY_TRANSFORMS')
            con.target = self.rig_ob
            con.subtarget = pedestal_control_name
            con.target_space = 'LOCAL_OWNER_ORIENT'
            con.owner_space = 'LOCAL'
        
        if self.has_pose_bones and self.has_aim_control:
            if aim_control is None:
                aim_control: bpy.types.PoseBone = self.rig_ob.pose.bones.get(aim_control_name)
            shape_ob = bpy.data.objects.get(aim_shape_name)
            if shape_ob is None:
                shape_data = bpy.data.meshes.new(aim_shape_name)
                verts = [Vector(co) for co in aim_shape_vert_coords]
                shape_data.from_pydata(vertices=verts, edges=[], faces=aim_shape_faces)
                shape_ob = bpy.data.objects.new(aim_shape_name, shape_data)
            
            shape_ob.nwo.export_this = False
            aim_control.custom_shape = shape_ob
            aim_control.custom_shape_scale_xyz *= self.scale
            aim_control.use_custom_shape_bone_size = False
            con = aim_control.constraints.new('LIMIT_SCALE')
            con.use_min_x = True
            con.use_min_y = True
            con.use_min_z = True
            con.use_max_x = True
            con.use_max_y = True
            con.use_max_z = True
            con.min_x = 1
            con.min_y = 1
            con.min_z = 1
            con.max_x = 1
            con.max_y = 1
            con.max_z = 1
            con.use_transform_limit = True
            con.owner_space = 'LOCAL'
            
            con = aim_control.constraints.new('LIMIT_LOCATION')
            con.use_min_x = True
            con.use_min_y = True
            con.use_min_z = True
            con.use_max_x = True
            con.use_max_y = True
            con.use_max_z = True
            con.use_transform_limit = True
            con.owner_space = 'LOCAL'
            
            if pitch is None:
                pitch: bpy.types.PoseBone = self.rig_ob.pose.bones.get(aim_pitch_name)
            con = pitch.constraints.new('COPY_ROTATION')
            con.target = self.rig_ob
            con.subtarget = aim_control.name
            # con.use_x = False
            # con.use_z = False
            con.target_space = 'LOCAL_OWNER_ORIENT'
            con.owner_space = 'LOCAL'
            
            if yaw is None:
                yaw: bpy.types.PoseBone = self.rig_ob.pose.bones.get(aim_yaw_name)
            con = yaw.constraints.new('COPY_ROTATION')
            con.target = self.rig_ob
            con.subtarget = aim_control.name
            # con.use_x = False
            # con.use_y = False
            con.target_space = 'LOCAL_OWNER_ORIENT'
            con.owner_space = 'LOCAL'
            
    
    def build_bones(self, pedestal=None, pitch=None, yaw=None, build_pedestal_control=True, build_aim_control=True):
        bone_tail = globals()[f"bone_{self.forward.replace('-', '_negative')}"]
        bpy.ops.object.editmode_toggle()
        if pedestal is None:
            pedestal = self.rig_data.edit_bones.new(pedestal_name)
            pedestal.tail = bone_tail
        else:
            pedestal = self.rig_data.edit_bones.get(pedestal)
            
        if self.set_scene_rig_props and self.has_pose_bones and not self.context.scene.nwo.node_usage_pedestal:
            self.context.scene.nwo.node_usage_pedestal = pedestal_name
        if self.has_pedestal_control:
            pedestal_control = self.rig_data.edit_bones.new(pedestal_control_name)
            pedestal_control.use_deform = False
            pedestal_control.tail = bone_tail
            if self.set_scene_rig_props:
                self.context.scene.nwo.control_pedestal = pedestal_name
            
        if self.has_pose_bones:
            if pitch is None:
                pitch = self.rig_data.edit_bones.new(aim_pitch_name)
                pitch.parent = pedestal
                pitch.tail = bone_tail
            else:
                pitch = self.rig_data.edit_bones.get(pitch)
            
            if yaw is None:
                yaw = self.rig_data.edit_bones.new(aim_yaw_name)
                yaw.parent = pedestal
                yaw.tail = bone_tail
            else:
                yaw = self.rig_data.edit_bones.get(yaw)
                
            if self.set_scene_rig_props:
                if not self.context.scene.nwo.node_usage_pose_blend_pitch:
                    self.context.scene.nwo.node_usage_pose_blend_pitch = aim_pitch_name
                if not self.context.scene.nwo.node_usage_pose_blend_yaw:
                    self.context.scene.nwo.node_usage_pose_blend_yaw = aim_yaw_name
            if self.has_aim_control:
                aim_control = self.rig_data.edit_bones.new(aim_control_name)
                aim_control.use_deform = False
                aim_control.parent = pedestal
                aim_control.tail = bone_tail
                if self.set_scene_rig_props and not self.context.scene.nwo.control_aim:
                    self.context.scene.nwo.control_aim = aim_control_name

        bpy.ops.object.editmode_toggle()
        
        
    def build_bone_collections(self):
        deform_collection = self.rig_data.collections.new('halo_deform_bones')
        deform_collection.assign(self.rig_data.bones.get(pedestal_name))
        if self.has_pose_bones:
            deform_collection.assign(self.rig_data.bones.get(aim_pitch_name))
            deform_collection.assign(self.rig_data.bones.get(aim_yaw_name))
            
        if self.has_pedestal_control or self.has_aim_control:
            # deform_collection.is_visible = False
            control_collection = self.rig_data.collections.new('halo_control_bones')
            if self.has_pedestal_control:
                control_collection.assign(self.rig_data.bones.get(pedestal_control_name))
                
            if self.has_aim_control:
                control_collection.assign(self.rig_data.bones.get(aim_control_name))
                
    def make_parent(self, child_bone_name):
        bpy.ops.object.editmode_toggle()
        pedestal = self.rig_data.edit_bones.get(pedestal_name)
        child_bone = self.rig_data.edit_bones.get(child_bone_name)
        child_bone.parent = pedestal
        bpy.ops.object.editmode_toggle()
            
    
    def build_armature(self):
        self.rig_data = bpy.data.armatures.new('Armature')
        self.rig_ob = bpy.data.objects.new('Armature', self.rig_data)
        self.context.scene.collection.objects.link(self.rig_ob)
        self.context.view_layer.objects.active = self.rig_ob
        self.rig_ob.select_set(True)
        if self.set_scene_rig_props and not self.context.scene.nwo.main_armature:
            self.context.scene.nwo.main_armature = self.rig_ob