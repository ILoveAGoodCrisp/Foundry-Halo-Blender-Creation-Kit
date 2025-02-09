from pathlib import Path
import bpy

from ..managed_blam.shader_custom import ShaderCustomTag
from ..managed_blam.shader_halogram import ShaderHalogramTag
from ..managed_blam.shader_foliage import ShaderFoliageTag
from ..managed_blam.shader_terrain import ShaderTerrainTag
from ..managed_blam.material import MaterialTag
from ..managed_blam.shader import ShaderTag
from ..managed_blam.shader_decal import ShaderDecalTag
from .. import utils

class NWO_ShaderToNodes(bpy.types.Operator):
    bl_idname = "nwo.shader_to_nodes"
    bl_label = "Convert Shader to Blender Material Nodes"
    bl_description = "Builds a new node tree for the active material based on the referenced shader/material tag. Will import required bitmaps"
    bl_options = {"UNDO"}
    
    mat_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return not context.scene.nwo.export_in_progress

    def execute(self, context):
        mat = bpy.data.materials.get(self.mat_name, 0)
        if not mat:
            self.report({'WARNING'}, "Material not supplied")
            return {"CANCELLED"}
        shader_path = mat.nwo.shader_path
        full_path = Path(utils.get_tags_path(), shader_path)
        if not full_path.exists():
            self.report({'WARNING'}, "Tag not found")
            return {"CANCELLED"}
        if not shader_path.endswith(('.shader', '.material')):
            self.report({'WARNING'}, f'Tag Type [{utils.dot_partition(shader_path, True)}] is not supported')
            return {"CANCELLED"}
        tag_to_nodes(utils.is_corinth(context), mat, shader_path)
        return {"FINISHED"}

def tag_to_nodes(corinth: bool, mat: bpy.types.Material, tag_path: str, always_extract_bitmaps=False) -> set:
    """Turns a shader/material tag into blender material nodes"""
    print(f"--- Building material nodes for: {mat.name}")
    shader = None
    if corinth:
        with MaterialTag(path=tag_path) as shader:
            shader.to_nodes(mat)
    else:
        shader_type = Path(tag_path).suffix[1:]
        match shader_type:
            case 'shader':
                with ShaderTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
            case 'shader_decal':
                with ShaderDecalTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
            case 'shader_terrain':
                with ShaderTerrainTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
            case 'shader_halogram':
                with ShaderHalogramTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
            case 'shader_foliage':
                with ShaderFoliageTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
            case 'shader_custom':
                with ShaderCustomTag(path=tag_path) as shader:
                    shader.always_extract_bitmaps = always_extract_bitmaps
                    shader.to_nodes(mat)
    
    if shader is None:
        return set()
    else:
        return shader.game_functions