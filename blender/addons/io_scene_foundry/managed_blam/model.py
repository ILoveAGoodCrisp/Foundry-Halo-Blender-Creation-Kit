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

from pathlib import Path

import bpy
from ..managed_blam import Tag

class ModelTag(Tag):
    tag_ext = 'model'
    
    def _read_fields(self):
        self.reference_render_model = self.tag.SelectField("Reference:render model")
        self.reference_collision_model = self.tag.SelectField("Reference:collision model")
        self.reference_animation = self.tag.SelectField("Reference:animation")
        self.reference_physics_model = self.tag.SelectField("Reference:physics_model")
        self.block_variants = self.tag.SelectField("Block:variants")
        
    def get_model_paths(self) -> tuple[str]:
        """Returns full string paths from model tag dependencies: render, collision, animation, physics"""
        render = ""
        collision = ""
        animation  = ""
        physics = ""
        render_path = self.reference_render_model.Path
        if render_path:
            render = render_path.Filename
            
        collision_path = self.reference_collision_model.Path
        if collision_path:
            collision = collision_path.Filename
            
        animation_path = self.reference_animation.Path
        if animation_path:
            animation = animation_path.Filename
            
        physics_path = self.reference_physics_model.Path
        if physics_path:
            physics = physics_path.Filename
            
        return render, collision, animation, physics
        
    def set_model_overrides(self, render_model, collision_model, model_animation_graph, physics_model):
        if render_model and self._tag_exists(render_model):
            self.reference_render_model.Path = self._TagPath_from_string(render_model)
            self.tag_has_changes = True
        if collision_model and self._tag_exists(collision_model):
            self.reference_collision_model.Path = self._TagPath_from_string(collision_model)
            self.tag_has_changes = True
        if model_animation_graph and self._tag_exists(model_animation_graph):
            self.reference_animation.Path = self._TagPath_from_string(model_animation_graph)
            self.tag_has_changes = True
        if physics_model and self._tag_exists(physics_model):
            self.reference_physics_model.Path = self._TagPath_from_string(physics_model)
            self.tag_has_changes = True
            
    def get_model_variants(self):
        return [v.SelectField("name").GetStringData() for v in self.block_variants.Elements]
    
    def set_asset_paths(self):
        asset_render_model = Path(self.asset_dir, self.asset_name).with_suffix(".render_model")
        if self._tag_exists(asset_render_model):
            self.reference_render_model.Path = self._TagPath_from_string(asset_render_model)
        else:
            self.reference_render_model.Path = None
        
        asset_collision_model = Path(self.asset_dir, self.asset_name).with_suffix(".collision_model")
        if self._tag_exists(asset_collision_model):
            self.reference_collision_model.Path = self._TagPath_from_string(asset_collision_model)
        else:
            self.reference_collision_model.Path = None
        
        asset_model_animation_graph = Path(self.asset_dir, self.asset_name).with_suffix(".model_animation_graph")
        if self._tag_exists(asset_model_animation_graph):
            self.reference_animation.Path = self._TagPath_from_string(asset_model_animation_graph)
        else:
            self.reference_animation.Path = None
        
        asset_physics_model = Path(self.asset_dir, self.asset_name).with_suffix(".physics_model")
        if self._tag_exists(asset_physics_model):
            self.reference_physics_model.Path = self._TagPath_from_string(asset_physics_model)
        else:
            self.reference_physics_model.Path = None
            
        self.tag_has_changes = True
        
    def assign_lighting_info_tag(self, lighting_info_path: str):
        if not self.corinth: return
        info_tag_path = self._TagPath_from_string(lighting_info_path)
        info_field = self.tag.SelectField("Lighting Info")
        if info_field.Path != info_tag_path:
            info_field.Path = info_tag_path
            self.tag_has_changes = True