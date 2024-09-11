from collections import defaultdict
from enum import Enum
from math import degrees
import os
from pathlib import Path
import tempfile
import time
import bpy
from mathutils import Matrix

from .import_sidecar import SidecarImport

from .tag_builder import build_tags

from .build_sidecar_granny import Sidecar

from .export_info import ExportInfo

from ..props.mesh import NWO_MeshPropertiesGroup

from ..props.object import NWO_ObjectPropertiesGroup

from .virtual_geometry import VirtualMaterial, VirtualMesh, VirtualNode, VirtualScene

from ..granny import Granny
from .. import utils
from ..ui.bar import NWO_HaloExportPropertiesGroup
from ..props.scene import NWO_ScenePropertiesGroup
from ..constants import GameVersion, VALID_MESHES, VALID_OBJECTS
from ..tools.asset_types import AssetType

class ExportTagType(Enum):
    RENDER = 0
    COLLISION = 1
    PHYSICS = 2
    MARKERS = 3
    SKELETON = 4
    ANIMATION = 5
    SKY = 6
    DECORATOR = 7
    STRUCTURE = 8
    STRUCTURE_DESIGN = 9
        
class ExportScene:
    '''Scene to hold all the export objects'''
    def __init__(self, context, sidecar_path_full, sidecar_path, asset_type, asset_name, asset_path, corinth, export_settings, scene_settings):
        self.context = context
        self.asset_type = AssetType[asset_type.upper()]
        self.asset_name = asset_name
        self.asset_path = asset_path
        self.sidecar_path = sidecar_path
        self.corinth = corinth
        self.tags_dir = Path(utils.get_tags_path())
        self.data_dir = Path(utils.get_data_path())
        self.root_dir = self.data_dir.parent
        self.depsgraph: bpy.types.Depsgraph = None
        self.virtual_scene: VirtualScene = None
        self.no_parent_objects = []
        self.default_region: str = context.scene.nwo.regions_table[0].name
        self.default_permutation: str = context.scene.nwo.permutations_table[0].name
        
        self.regions = [i.name for i in context.scene.nwo.regions_table]
        self.permutations = [i.name for i in context.scene.nwo.permutations_table]
        self.global_materials = set()
        self.global_materials_list = []
        
        self.reg_name = 'BSP' if self.asset_type.supports_bsp else 'region'
        self.perm_name = 'layer' if self.asset_type.supports_bsp else 'permutation'
        
        self.selected_bsps = set()
        self.selected_permutations = set()
        
        self.game_version = 'corinth' if corinth else 'reach'
        self.export_settings = export_settings
        self.scene_settings = scene_settings
        self.sidecar = Sidecar(sidecar_path_full, sidecar_path, asset_path, asset_name, self.asset_type, scene_settings, corinth, context)
        
        self.project_root = Path(utils.get_tags_path()).parent
        
        os.chdir(tempfile.gettempdir())
        
        self.granny = Granny(Path(self.project_root, "granny2_x64.dll"))
        
    def ready_scene(self):
        utils.exit_local_view(self.context)
        self.context.view_layer.update()
        utils.set_object_mode(self.context)
        self.disabled_collections = utils.disable_excluded_collections(self.context)
        
    def get_initial_export_objects(self):
        self.depsgraph = self.context.evaluated_depsgraph_get()
        if self.asset_type == AssetType.ANIMATION:
            self.export_objects = {ob for ob in self.depsgraph.objects if ob.nwo.export_this and ob.type == "ARMATURE"}
        else:
            self.export_objects = {ob for ob in self.depsgraph.objects if ob.nwo.export_this and ob.type in VALID_OBJECTS}
            
        self.virtual_scene = VirtualScene(self.asset_type, self.depsgraph, self.corinth, self.tags_dir, self.granny)
        
        # Create default material
        if self.corinth:
            default_material = VirtualMaterial("invalid", r"shaders\invalid.material", self.virtual_scene)
        else:
            default_material = VirtualMaterial("invalid", r"shaders\invalid.shader", self.virtual_scene)
            
        self.virtual_scene.materials["invalid"] = default_material
            
    def setup_skeleton(self):
        armature = utils.get_rig(self.context)
        if armature:
            self.virtual_scene.set_skeleton(armature)
    
    def create_virtual_geometry(self):
        process = "--- Creating Virtual Geometry"
        ob_halo_data = {}
        for idx, ob in enumerate(self.export_objects):
            result = self.get_halo_props(ob)
            if result is None:
                continue
            props, region, permutation = result
            ob_halo_data[ob] = (props, region, permutation)
        
        self.global_materials_list = list(self.global_materials - {'default'})
        self.global_materials_list.insert(0, 'default')
        
        self.export_info = ExportInfo(self.regions, self.global_materials_list).create_info()
        self.virtual_scene.regions = self.regions
        self.virtual_scene.global_materials = self.global_materials_list
        
        len_export_obs = len(ob_halo_data)
        with utils.Spinner():
            utils.update_job_count(process, "", 0, len_export_obs)
            for idx, (ob, (props, region, permutation)) in enumerate(ob_halo_data.items()):
                self.virtual_scene.add(ob, props, region, permutation)
                if not ob.parent:
                    self.no_parent_objects.append(ob)
                utils.update_job_count(process, "", idx, len_export_obs)
            utils.update_job_count(process, "", len_export_obs, len_export_obs)
            
    def get_halo_props(self, ob):
        props = {}
        region = self.default_region
        permutation = self.default_permutation
        nwo = ob.nwo
        object_type = utils.get_object_type(ob)
        
        if object_type == '_connected_geometry_object_type_none':
            return 
        
        props["bungie_object_type"] = object_type
        is_light = ob.type == 'LIGHT'
        is_mesh = ob.type == 'MESH'
        instanced_object = (object_type == '_connected_geometry_object_type_mesh' and nwo.mesh_type == '_connected_geometry_mesh_type_object_instance')
        if self.asset_type.supports_permutations:
            if not instanced_object and (is_mesh or is_light or self.asset_type.supports_bsp or nwo.marker_uses_regions):
                reg = utils.true_region(nwo)
                if reg in self.regions:
                    region = reg
                else:
                    self.warning_hit = True
                    utils.print_warning(f"Object [{ob.name}] has {self.reg_name} [{reg}] which is not present in the {self.reg_name}s table. Setting {self.reg_name} to: {self.default_region}")
                    
            if (is_light or self.asset_type.supports_bsp) and not instanced_object:
                perm = utils.true_permutation(nwo)
                if perm in self.permutations:
                    permutation = perm
                else:
                    self.warning_hit = True
                    utils.print_warning(f"Object [{ob.name}] has {self.perm_name} [{perm}] which is not presented in the {self.perm_name}s table. Setting {self.perm_name} to: {self.default_permutation}")
                    
            elif nwo.marker_uses_regions and nwo.marker_permutation_type == 'include' and nwo.marker_permutations:
                marker_perms = [item.name for item in nwo.marker_permutations]
                for perm in marker_perms:
                    if perm not in self.permutations:
                        self.warning_hit = True
                        utils.print_warning(f"Object [{ob.name}] has {self.perm_name} [{perm}] in its include list which is not presented in the {self.perm_name}s table. Ignoring {self.perm_name}")
            
        if object_type == '_connected_geometry_object_type_mesh':
            if nwo.mesh_type == '':
                nwo.mesh_type = '_connected_geometry_mesh_type_default'
            if utils.type_valid(nwo.mesh_type, self.asset_type.name.lower(), self.game_version):
                props = self._setup_mesh_properties(ob, ob.nwo, self.asset_type.supports_bsp, props, region)
                if props is None:
                    return
                
            else:
                self.warning_hit = True
                return utils.print_warning(f"{ob.name} has invalid mesh type [{nwo.mesh_type}] for asset [{self.asset_type}]. Skipped")
                
        elif object_type == '_connected_geometry_object_type_marker':
            if nwo.marker_type == '':
                nwo.marker_type = '_connected_geometry_marker_type_model'
            if utils.type_valid(nwo.marker_type, self.asset_type.name.lower(), self.game_version):
                props = self._setup_marker_properties(ob, ob.nwo, props, region)
                if props is None:
                    return
            else:
                self.warning_hit = True
                return utils.print_warning(f"{ob.name} has invalid marker type [{nwo.mesh_type}] for asset [{self.asset_type}]. Skipped")
        
        return props, region, permutation
    
    def _set_global_material_prop(self, ob: bpy.types.Object, props: dict, global_material=""):
        if not global_material:
            global_material = ob.data.nwo.face_global_material.strip().replace(' ', "_")
        if global_material:
            if self.corinth and props.get("bungie_mesh_type") in ('_connected_geometry_mesh_type_poop', '_connected_geometry_mesh_type_poop_collision'):
                props["bungie_mesh_global_material"] = global_material
                props["bungie_mesh_poop_collision_override_global_material"] = "1"
            else:
                props["bungie_face_global_material"] = global_material
                
            self.global_materials.add(global_material)

        return global_material
    
    def _setup_mesh_properties(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, supports_bsp: bool, props: dict, region: str):
        mesh_type = ob.data.nwo.mesh_type
        mesh = ob.data
        data_nwo: NWO_MeshPropertiesGroup = mesh.nwo
        
        if supports_bsp:
            # The ol switcheroo
            if mesh_type == '_connected_geometry_mesh_type_default':
                mesh_type = '_connected_geometry_mesh_type_poop'
            elif mesh_type == '_connected_geometry_mesh_type_structure':
                mesh_type = '_connected_geometry_mesh_type_default'
                if not self.corinth:
                    if data_nwo.render_only:
                        props["bungie_face_mode"] = '_connected_geometry_face_mode_render_only'
                    elif data_nwo.sphere_collision_only:
                        props["bungie_face_mode"] = '_connected_geometry_face_mode_sphere_collision_only'
                    elif data_nwo.collision_only:
                        props["bungie_face_mode"] = '_connected_geometry_face_mode_collision_only'
                        
        props["bungie_mesh_type"] = mesh_type
        
        if mesh_type == "_connected_geometry_mesh_type_physics":
            props = self._setup_physics_props(ob, nwo, props)
        elif mesh_type == '_connected_geometry_mesh_type_object_instance':
            props = self._setup_instanced_object_props(ob, nwo, props, region)
        elif mesh_type == '_connected_geometry_mesh_type_poop':
            props = self._setup_poop_props(ob, nwo, data_nwo, props)
        elif mesh_type == '_connected_geometry_mesh_type_default' and self.corinth and self.asset_type == 'scenario':
            props["bungie_face_type"] = '_connected_geometry_face_type_sky'
        elif mesh_type == '_connected_geometry_mesh_type_seam':
            props["bungie_mesh_seam_associated_bsp"] = (f"{self.asset_name}_{region}")
        elif mesh_type == "_connected_geometry_mesh_type_portal":
            props["bungie_mesh_portal_type"] = nwo.portal_type
            if nwo.portal_ai_deafening:
                props["bungie_mesh_portal_ai_deafening"] = "1"
            if nwo.portal_blocks_sounds:
                props["bungie_mesh_portal_blocks_sound"] = "1"
            if nwo.portal_is_door:
                props["bungie_mesh_portal_is_door"] = "1"
        elif mesh_type == "_connected_geometry_mesh_type_water_physics_volume":
            # ob["bungie_mesh_tessellation_density"] = nwo.mesh_tessellation_density
            props["bungie_mesh_water_volume_depth"] = utils.jstr(nwo.water_volume_depth)
            props["bungie_mesh_water_volume_flow_direction"] = utils.jstr(degrees(nwo.water_volume_flow_direction))
            props["bungie_mesh_water_volume_flow_velocity"] = utils.jstr(nwo.water_volume_flow_velocity)
            props["bungie_mesh_water_volume_fog_murkiness"] = utils.jstr(nwo.water_volume_fog_murkiness)
            if self.corinth:
                props["bungie_mesh_water_volume_fog_color"] = utils.color_rgba_str(nwo.water_volume_fog_color)
            else:
                props["bungie_mesh_water_volume_fog_color"] = utils.color_argb_str(nwo.water_volume_fog_color)
            
        elif mesh_type in ("_connected_geometry_mesh_type_poop_vertical_rain_sheet", "_connected_geometry_mesh_type_poop_rain_blocker"):
            props["bungie_face_mode"] = '_connected_geometry_face_mode_render_only'
            
        elif mesh_type == "_connected_geometry_mesh_type_planar_fog_volume":
            props["bungie_mesh_fog_appearance_tag"] = utils.relative_path(nwo.fog_appearance_tag)
            props["bungie_mesh_fog_volume_depth"] = utils.jstr(nwo.fog_volume_depth)
            
        elif mesh_type == "_connected_geometry_mesh_type_soft_ceiling":
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_boundary_surface"
            props["bungie_mesh_boundary_surface_type"] = '_connected_geometry_boundary_surface_type_soft_ceiling'
            props["bungie_mesh_boundary_surface_name"] = utils.dot_partition(ob.name)
            
        elif mesh_type == "_connected_geometry_mesh_type_soft_kill":
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_boundary_surface"
            props["bungie_mesh_boundary_surface_type"] = '_connected_geometry_boundary_surface_type_soft_kill'
            props["bungie_mesh_boundary_surface_name"] = utils.dot_partition(ob.name)
            
        elif mesh_type == "_connected_geometry_mesh_type_slip_surface":
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_boundary_surface"
            props["bungie_mesh_boundary_surface_type"] = '_connected_geometry_boundary_surface_type_slip_surface'
            props["bungie_mesh_boundary_surface_name"] = utils.dot_partition(ob.name)
            
        elif mesh_type == "_connected_geometry_mesh_type_lightmap_only":
            nwo.lightmap_resolution_scale_active = False
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_poop"
            self._setup_poop_props(ob)
            if data_nwo.no_shadow:
                props["bungie_face_mode"] = '_connected_geometry_face_mode_render_only'
            else:
                props["bungie_face_mode"] = '_connected_geometry_face_mode_lightmap_only'
            props["bungie_mesh_poop_lighting"] = "_connected_geometry_poop_lighting_single_probe"
            props["bungie_mesh_poop_pathfinding"] = "_connected_poop_instance_pathfinding_policy_none"
            
        elif mesh_type == "_connected_geometry_mesh_type_lightmap_exclude":
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_obb_volume"
            props["bungie_mesh_obb_type"] = "_connected_geometry_mesh_obb_volume_type_lightmapexclusionvolume"
            
        elif mesh_type == "_connected_geometry_mesh_type_streaming":
            props["bungie_mesh_type"] = "_connected_geometry_mesh_type_obb_volume"
            props["bungie_mesh_obb_type"] = "_connected_geometry_mesh_obb_volume_type_streamingvolume"
            
        elif mesh_type == '_connected_geometry_mesh_type_collision' and self.asset_type in {AssetType.SCENARIO, AssetType.PREFAB}:
            if self.corinth:
                props["bungie_mesh_type"] = '_connected_geometry_mesh_type_poop_collision'
                props["bungie_mesh_poop_collision_type"] = data_nwo.poop_collision_type
            elif ob.parent and ob.parent.type in VALID_MESHES and ob.parent.data.nwo.mesh_type == '_connected_geometry_mesh_type_default':
                props["bungie_mesh_type"] = '_connected_geometry_mesh_type_poop_collision'
            else:
                props["bungie_mesh_type"] = '_connected_geometry_mesh_type_poop'
                props["bungie_mesh_poop_lighting"] = "_connected_geometry_poop_lighting_single_probe"
                props["bungie_mesh_poop_pathfinding"] = "_connected_poop_instance_pathfinding_policy_cutout"
                props["bungie_mesh_poop_imposter_policy"] = "_connected_poop_instance_imposter_policy_never"
                nwo.reach_poop_collision = True
                if data_nwo.sphere_collision_only:
                    props["bungie_face_mode"] = '_connected_geometry_face_mode_sphere_collision_only'
                else:
                    props["bungie_face_mode"] = '_connected_geometry_face_mode_collision_only'
        
        elif self.asset_type == AssetType.PREFAB:
            props["bungie_mesh_type"] = '_connected_geometry_mesh_type_poop'
            self._setup_poop_props(ob)
            
        elif self.asset_type == AssetType.DECORATOR_SET:
            props["bungie_mesh_type"] = '_connected_geometry_mesh_type_decorator'
            props["bungie_mesh_decorator_lod"] = str(decorator_int(ob))
            
        uses_global_mat = self.asset_type.supports_global_materials and (props.get("bungie_mesh_type") in ("_connected_geometry_mesh_type_collision", "_connected_geometry_mesh_type_physics", "_connected_geometry_mesh_type_poop", "_connected_geometry_mesh_type_poop_collision") or self.asset_type == 'scenario' and not self.corinth and ob.get("bungie_mesh_type") == "_connected_geometry_mesh_type_default")
        if uses_global_mat:
            global_material = self._set_global_material_prop(ob, props)
            if global_material:
                self.global_materials.add(global_material)
                
        for idx, face_prop in enumerate(data_nwo.face_props):
            if face_prop.region_name_override:
                region = face_prop.region_name
                if region not in self.regions:
                    utils.print_warning(f"Object [{ob.name}] has {self.reg_name} [{region}] on face property index {idx} which is not present in the {self.reg_name}s table. Setting {self.reg_name} to: {self.default_region}")
            if uses_global_mat and face_prop.face_global_material_override:
                mat = face_prop.face_global_material.strip().replace(' ', "_")
                if mat:
                    self.global_materials.add(mat)

        return props
        
    def _setup_physics_props(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict):
        prim_type = nwo.mesh_primitive_type
        props["bungie_mesh_primitive_type"] = prim_type
        if prim_type != '_connected_geometry_primitive_type_none':
            # self.physics_prims.add(ob)
            pass
        elif self.corinth and nwo.mopp_physics:
            props["bungie_mesh_primitive_type"] = "_connected_geometry_primitive_type_mopp"
            props["bungie_havok_isshape"] = "1"
            
        return props
    
    def _setup_instanced_object_props(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict, region: str):
        props["bungie_marker_all_regions"] = utils.bool_str(not nwo.marker_uses_regions)
        if nwo.marker_uses_regions:
            props["bungie_marker_region"] = region
            props["bungie_face_region"] = region
            m_perms = nwo.marker_permutations
            if m_perms:
                m_perm_set = set()
                for perm in m_perms:
                    m_perm_set.add(perm.name)
                m_perm_json_value = f'''#({', '.join('"' + p + '"' for p in m_perm_set)})'''
                if nwo.marker_permutation_type == "exclude":
                    props["bungie_marker_exclude_from_permutations"] = m_perm_json_value
                else:
                    props["bungie_marker_include_in_permutations"] = m_perm_json_value
                
        return props
    
    def _setup_poop_props(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, data_nwo: NWO_MeshPropertiesGroup, props: dict):
        props["bungie_mesh_poop_lighting"] = nwo.poop_lighting
        props["bungie_mesh_poop_pathfinding"] = nwo.poop_pathfinding
        props["bungie_mesh_poop_imposter_policy"] = nwo.poop_imposter_policy
        if (
            nwo.poop_imposter_policy
            != "_connected_poop_instance_imposter_policy_never"
        ):
            if not nwo.poop_imposter_transition_distance_auto:
                props["bungie_mesh_poop_imposter_transition_distance"] = utils.jstr(nwo.poop_imposter_transition_distance)
            if self.corinth:
                nwo["bungie_mesh_poop_imposter_brightness"] = utils.jstr(nwo.poop_imposter_brightness)
        if data_nwo.render_only:
            props["bungie_face_mode"] = '_connected_geometry_face_mode_render_only'
            if self.corinth:
                props["bungie_mesh_poop_collision_type"] = '_connected_geometry_poop_collision_type_none'
            else:
                props["bungie_mesh_poop_is_render_only"] = "1"
        elif nwo.poop_render_only:
            if self.corinth:
                props["bungie_mesh_poop_collision_type"] = '_connected_geometry_poop_collision_type_none'
            else:
                props["bungie_mesh_poop_is_render_only"] = "1"
                
        elif not self.corinth and data_nwo.sphere_collision_only:
            props["bungie_face_mode"] = '_connected_geometry_face_mode_sphere_collision_only'
        elif self.corinth:
            props["bungie_mesh_poop_collision_type"] = data_nwo.poop_collision_type
        if nwo.poop_does_not_block_aoe:
            props["bungie_mesh_poop_does_not_block_aoe"] = "1"
        if nwo.poop_excluded_from_lightprobe:
            props["bungie_mesh_poop_excluded_from_lightprobe"] = "1"
            
        if data_nwo.decal_offset:
            props["bungie_mesh_poop_decal_spacing"] = "1" 
        if data_nwo.precise_position:
            props["bungie_mesh_poop_precise_geometry"] = "1"

        if self.corinth:
            props["bungie_mesh_poop_lightmap_resolution_scale"] = str(nwo.poop_lightmap_resolution_scale)
            props["bungie_mesh_poop_streamingpriority"] = nwo.poop_streaming_priority
            props["bungie_mesh_poop_cinema_only"] = utils.bool_str(nwo.poop_cinematic_properties == '_connected_geometry_poop_cinema_only')
            props["bungie_mesh_poop_exclude_from_cinema"] = utils.bool_str(nwo.poop_cinematic_properties == '_connected_geometry_poop_cinema_exclude')
            if nwo.poop_remove_from_shadow_geometry:
                props["bungie_mesh_poop_remove_from_shadow_geometry"] = "1"
            if nwo.poop_disallow_lighting_samples:
                props["bungie_mesh_poop_disallow_object_lighting_samples"] = "1"
                
        return props
        
    def _setup_marker_properties(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict, region: str):
        marker_type = nwo.marker_type
        props["bungie_marker_type"] = marker_type
        props["bungie_marker_model_group"] = nwo.marker_model_group
        if self.asset_type in ('model', 'sky'):
            props["bungie_marker_all_regions"] = utils.bool_str(not nwo.marker_uses_regions)
            if nwo.marker_uses_regions:
                props["bungie_marker_region"] = region
                m_perms = nwo.marker_permutations
                if m_perms:
                    m_perm_set = set()
                    for perm in m_perms:
                        m_perm_set.add(perm.name)
                    m_perm_json_value = f'''#({', '.join('"' + p + '"' for p in m_perm_set)})'''
                    if nwo.marker_permutation_type == "exclude":
                        props["bungie_marker_exclude_from_permutations"] = m_perm_json_value
                    else:
                        props["bungie_marker_include_in_permutations"] = m_perm_json_value
                        
            if marker_type == "_connected_geometry_marker_type_hint":
                if self.corinth:
                    scale = ob.matrix_world.to_scale()
                    max_abs_scale = max(abs(scale.x), abs(scale.y), abs(scale.z))
                    props["bungie_marker_hint_length"] = utils.jstr(ob.empty_display_size * 2 * max_abs_scale)

                ob.name = "hint_"
                if nwo.marker_hint_type == "bunker":
                    ob.name += "bunker"
                elif nwo.marker_hint_type == "corner":
                    ob.name += "corner_"
                    if nwo.marker_hint_side == "right":
                        ob.name += "right"
                    else:
                        ob.name += "left"

                else:
                    if nwo.marker_hint_type == "vault":
                        ob.name += "vault_"
                    elif nwo.marker_hint_type == "mount":
                        ob.name += "mount_"
                    else:
                        ob.name += "hoist_"

                    if nwo.marker_hint_height == "step":
                        ob.name += "step"
                    elif nwo.marker_hint_height == "crouch":
                        ob.name += "crouch"
                    else:
                        ob.name += "stand"
                        
            elif marker_type == "_connected_geometry_marker_type_pathfinding_sphere":
                props["bungie_mesh_primitive_sphere_radius"] = get_marker_sphere_size(ob)
                props["bungie_marker_pathfinding_sphere_vehicle_only"] = utils.bool_str(nwo.marker_pathfinding_sphere_vehicle)
                props["bungie_marker_pathfinding_sphere_remains_when_open"] = utils.bool_str(nwo.pathfinding_sphere_remains_when_open)
                props["bungie_marker_pathfinding_sphere_with_sectors"] = utils.bool_str(nwo.pathfinding_sphere_with_sectors)
                
            elif marker_type == "_connected_geometry_marker_type_physics_constraint":
                props["bungie_marker_type"] = nwo.physics_constraint_type
                parent = nwo.physics_constraint_parent
                if (
                    parent is not None
                    and parent.type == "ARMATURE"
                    and nwo.physics_constraint_parent_bone != ""
                ):
                    props["bungie_physics_constraint_parent"] = (
                        nwo.physics_constraint_parent_bone
                    )

                elif parent is not None:
                    props["bungie_physics_constraint_parent"] = str(
                        nwo.physics_constraint_parent.parent_bone
                    )
                child = nwo.physics_constraint_child
                if (
                    child is not None
                    and child.type == "ARMATURE"
                    and nwo.physics_constraint_child_bone != ""
                ):
                    props["bungie_physics_constraint_child"] = (
                        nwo.physics_constraint_child_bone
                    )

                elif child is not None:
                    props["bungie_physics_constraint_child"] = str(
                        nwo.physics_constraint_child.parent_bone
                    )
                props["bungie_physics_constraint_use_limits"] = utils.bool_str(
                    nwo.physics_constraint_uses_limits
                )
                if nwo.physics_constraint_uses_limits:
                    if nwo.physics_constraint_type == "_connected_geometry_marker_type_physics_hinge_constraint":
                        props["bungie_physics_constraint_hinge_min"] = utils.jstr(degrees(nwo.hinge_constraint_minimum))
                        props["bungie_physics_constraint_hinge_max"] = utils.jstr(degrees(nwo.hinge_constraint_maximum))
                    else:
                        props["bungie_physics_constraint_cone_angle"] = utils.jstr(degrees(nwo.cone_angle))
                        props["bungie_physics_constraint_plane_min"] = utils.jstr(degrees(nwo.plane_constraint_minimum))
                        props["bungie_physics_constraint_plane_max"] = utils.jstr(degrees(nwo.plane_constraint_maximum))
                        props["bungie_physics_constraint_twist_start"] = utils.jstr(degrees(nwo.twist_constraint_start))
                        props["bungie_physics_constraint_twist_end"] = utils.jstr(degrees(nwo.twist_constraint_end))
                
            elif marker_type == "_connected_geometry_marker_type_target":
                props["bungie_mesh_primitive_sphere_radius"] = get_marker_sphere_size(ob, nwo)
                
            elif marker_type == "_connected_geometry_marker_type_effects":
                props["bungie_marker_type"] = "_connected_geometry_marker_type_model"
                if not ob.name.startswith("fx_"):
                    ob.name = "fx_" + ob.name
                    
            elif marker_type == "_connected_geometry_marker_type_garbage":
                if not self.corinth:
                    props["bungie_marker_type"] = "_connected_geometry_marker_type_model"
                props["bungie_marker_velocity"] = utils.vector_str(nwo.marker_velocity)
        
        elif self.asset_type in ("scenario", "prefab"):
            if marker_type == "_connected_geometry_marker_type_game_instance":
                tag_name = nwo.marker_game_instance_tag_name.lower()
                props["bungie_marker_game_instance_tag_name"] = tag_name
                if self.corinth and tag_name.endswith(
                    ".prefab"
                ):
                    props["bungie_marker_type"] = "_connected_geometry_marker_type_prefab"
                    if nwo.prefab_pathfinding != "no_override":
                        props["bungie_mesh_poop_pathfinding"] = nwo.prefab_pathfinding
                    if nwo.prefab_lightmap_res > 0:
                        props["bungie_mesh_poop_lightmap_resolution_scale"] = str(nwo.prefab_lightmap_res)
                    if nwo.prefab_lighting != "no_override":
                        props["bungie_mesh_poop_lighting"] = nwo.prefab_lighting
                    if nwo.prefab_imposter_policy != "no_override":
                        props["bungie_mesh_poop_imposter_policy"] = nwo.prefab_imposter_policy
                        if nwo.prefab_imposter_policy != "_connected_poop_instance_imposter_policy_never":
                            if nwo.prefab_imposter_brightness > 0:
                                props["bungie_mesh_poop_imposter_brightness"] = utils.jstr(nwo.prefab_imposter_brightness)
                            if not nwo.prefab_imposter_transition_distance_auto:
                                props["bungie_mesh_poop_imposter_transition_distance"] = utils.jstr(nwo.prefab_imposter_transition_distance_auto)
                                
                    if nwo.prefab_streaming_priority != "no_override":
                        props["bungie_mesh_poop_streamingpriority"] = nwo.prefab_streaming_priority
                    
                    if nwo.prefab_cinematic_properties == '_connected_geometry_poop_cinema_only':
                        props["bungie_mesh_poop_cinema_only"] = "1"
                    elif nwo.prefab_cinematic_properties == '_connected_geometry_poop_cinema_exclude':
                        props["bungie_mesh_poop_exclude_from_cinema"] = "1"
                        
                    if nwo.prefab_render_only:
                        props["bungie_mesh_poop_is_render_only"] = "1"
                    if nwo.prefab_does_not_block_aoe:
                        props["bungie_mesh_poop_does_not_block_aoe"] = "1"
                    if nwo.prefab_excluded_from_lightprobe:
                        props["bungie_mesh_poop_excluded_from_lightprobe"] = "1"
                    if nwo.prefab_decal_spacing:
                        props["bungie_mesh_poop_decal_spacing"] = "1"
                    if nwo.prefab_remove_from_shadow_geometry:
                        props["bungie_mesh_poop_remove_from_shadow_geometry"] = "1"
                    if nwo.prefab_disallow_lighting_samples:
                        props["bungie_mesh_poop_disallow_object_lighting_samples"] = "1"       
                        
                elif (
                    self.corinth
                    and tag_name.endswith(
                        ".cheap_light"
                    )
                ):
                    props["bungie_marker_type"] = "_connected_geometry_marker_type_cheap_light"
                elif (
                    self.corinth
                    and tag_name.endswith(".light")
                ):
                    props["bungie_marker_type"] = "_connected_geometry_marker_type_light"
                elif (
                    self.corinth
                    and tag_name.endswith(".leaf")
                ):
                    props["bungie_marker_type"] = "_connected_geometry_marker_type_falling_leaf"
                else:
                    props["bungie_marker_game_instance_variant_name"] = nwo.marker_game_instance_tag_variant_name
                    if self.corinth:
                        props["bungie_marker_always_run_scripts"] = utils.bool_str(nwo.marker_always_run_scripts)
            
            elif marker_type == "_connected_geometry_marker_type_envfx":
                props["bungie_marker_looping_effect"] = nwo.marker_looping_effect
                
            elif marker_type == "_connected_geometry_marker_type_lightCone":
                props["bungie_marker_light_tag"] = nwo.marker_light_cone_tag
                props["bungie_marker_light_color"] = utils.color_3p_str(nwo.marker_light_cone_color)
                props["bungie_marker_light_cone_width"] = utils.jstr(nwo.marker_light_cone_alpha)
                props["bungie_marker_light_cone_length"] = utils.jstr(nwo.marker_light_cone_width)
                props["bungie_marker_light_color_alpha"] = utils.jstr(nwo.marker_light_cone_length)
                props["bungie_marker_light_cone_intensity"] = utils.jstr(nwo.marker_light_cone_intensity)
                props["bungie_marker_light_cone_curve"] = nwo.marker_light_cone_curve
                
        return props
            
    def create_virtual_tree(self):
        '''Creates a tree of object relations'''
        for ob in self.no_parent_objects:
            self.virtual_scene.add_model(ob)
                
        # for ob in self.export_objects:
        #     if not ob.parent: continue
        #     ob_node = self.virtual_scene.nodes.get(ob.name)
        #     if not ob_node:
        #         self.export_objects.remove(ob)
        #         continue
                
        #     if ob.parent_type == 'BONE' and ob.parent_bone:
        #         parent = self.virtual_scene.nodes.get(ob.parent_bone)
        #     else:
        #         parent = self.virtual_scene.nodes.get(ob.parent.name)
            
        #     if parent:
        #         ob_node.parent = parent
        #     elif self.virtual_scene.skeleton_node: # No valid parent found in export objects, parent this to the root skeleton if there is one
        #         ob_node.parent = self.virtual_scene.skeleton_node
        
    def get_selected_sets(self):
        '''
        Get selected bsps/permutations from the objects selected at export
        '''
        sel_perms = self.export_settings.export_all_perms == "selected"
        sel_bsps = self.export_settings.export_all_bsps == "selected"
        if not (sel_bsps or sel_perms):
            return
        current_selection = {node for node in self.virtual_scene.nodes if node.selected}
        if not current_selection:
            return
        for node in current_selection:
            if sel_bsps:
                self.selected_bsps.add(node.region)
            if sel_perms:
                self.selected_permutations.add(node.permutation)
            
    
    def export_files(self):
        # make necessary directories
        #self.models_dir = Path(self.asset_path, "models")
        self.models_export_dir = Path(self.asset_path, "export", "models")
        # if not self.models_dir.exists():
        #     self.models_dir.mkdir(parents=True, exist_ok=True)
        if not self.models_export_dir.exists():
            self.models_export_dir.mkdir(parents=True, exist_ok=True)
            
        if self.asset_type.supports_animations:
            # self.animations_dir = Path(self.asset_path, "animations")
            self.animations_export_dir = Path(self.asset_path, "export", "animations")
            # if not self.animations_dir.exists():
            #     self.animations_dir.mkdir(parents=True, exist_ok=True)
            if not self.animations_export_dir.exists():
                self.animations_export_dir.mkdir(parents=True, exist_ok=True)
                
        self._process_animations()
        self._process_models()
                
    def _process_animations(self):
        pass
    
    def _process_models(self):
        self._create_export_groups()
        self._export_models()
    
    def _create_export_groups(self):
        self.groups = defaultdict(list)
        for node in self.virtual_scene.nodes.values():
            self.groups[node.group].append(node)
    
    def _export_models(self):
        if not self.groups: return
        
        print("\n\nStarting Models Export")
        print(
            "-----------------------------------------------------------------------\n"
        )
        for name, nodes in self.groups.items():
            granny_path = self._get_export_path(name)
            perm = nodes[0].permutation
            region = nodes[0].region
            tag_type = nodes[0].tag_type
            self.sidecar.add_file_data(tag_type, perm, region, granny_path, bpy.data.filepath)
            # if not self.export_settings.selected_perms or perm in self.export_settings.selected_perms:
            job = f"--- {name}"
            utils.update_job(job, 0)
            if self.virtual_scene.skeleton_node:
                nodes_dict = {node.name: node for node in nodes + [self.virtual_scene.skeleton_node]}
            else:
                nodes_dict = {node.name: node for node in nodes}
            self._export_granny_model(granny_path, nodes_dict)
            utils.update_job(job, 1)
            
                
        # for permutation in self.permutations:
        #     granny_path = self._get_export_path(tag_type, permutation=permutation)
        #     self.sidecar_info.append(SidecarData(granny_path, self.data_dir, permutation))
            
        #     if not sel_perms or perm in sel_perms:
        #         if model_armature:
        #             if obs_perms:
        #                 export_obs = [ob for ob in objects if ob.nwo.permutation_name == perm]
        #                 export_obs.append(model_armature)
        #             else:
        #                 export_obs = [ob for ob in objects]
        #                 export_obs.append(model_armature)
        #         else:
        #             if obs_perms:
        #                 export_obs = [ob for ob in objects if ob.nwo.permutation_name == perm]
        #             else:
        #                 export_obs = [ob for ob in objects]
            
    def _export_granny_model(self, filepath: Path, virtual_objects: dict[VirtualNode]):
        self.granny.new(filepath)
        start = time.perf_counter()
        tree_start = time.perf_counter()
        print("from tree start")
        self.granny.from_tree(self.virtual_scene, virtual_objects)
        print("from tree", time.perf_counter() - tree_start)
        creation_start = time.perf_counter()
        print("creation start")
        self.granny.create_materials()
        self.granny.create_skeletons(export_info=self.export_info)
        self.granny.create_vertex_data()
        self.granny.create_tri_topologies()
        self.granny.create_meshes()
        self.granny.create_models()
        print("creation", time.perf_counter() - creation_start)
        print("transform")
        self.granny.transform()
        print("save")
        self.granny.save()
        print("done")
        end = time.perf_counter()
        print("granny time: ", end - start)
        if filepath.exists():
            os.startfile(r"F:\Modding\granny\granny_common_2_9_12_0_release\bin\win32\gr2_viewer.exe", arguments=str(filepath))
        
    def _export_granny_animation(self, filepath: Path, virtual_objects: list[VirtualNode]):
        granny = Granny(Path(self.project_root, "granny2_x64.dll"), filepath)
        granny.from_tree(self.virtual_scene, virtual_objects)
        granny.create_skeletons(export_info=self.export_info)
        granny.create_models()
        # granny.create_track_groups()
        # granny.create_animations()
        granny.transform()
        granny.save()
        
            
    def _get_export_path(self, name: str, animation=False):
        """Gets the path to save a particular file to"""
        if animation:
            return Path(self.animations_export_dir, f"{name}.gr2")
        else:
            return Path(self.models_export_dir, f"{self.asset_name}_{name}.gr2")
        # if self.asset_type == AssetType.SCENARIO:
        #     if tag_type == ExportTagType.STRUCTURE_DESIGN:
        #         if permutation.lower() == 'default':
        #             return Path(self.models_export_dir, f"{self.asset_name}_{region.name}_design.gr2")
        #         else:
        #             return Path(self.models_export_dir, f"{self.asset_name}_{region}_{permutation.name}_design.gr2")
        #     else:
        #         if permutation.is_default:
        #             return Path(self.models_export_dir, f"{self.asset_name}_{region.name}.gr2")
        #         else:
        #             return Path(self.models_export_dir, f"{self.asset_name}_{region.name}_{permutation.name}.gr2")
        # else:
        #     if tag_type == ExportTagType.ANIMATION:
        #         return Path(self.animations_export_dir, f"{animation}.gr2")
        #     else:
        #         if permutation.lower() == 'default' or tag_type in {ExportTagType.MARKERS, ExportTagType.SKELETON}:
        #             return Path(self.models_export_dir, f"{self.asset_name}_{tag_type.name.lower()}.gr2")
        #         else:
        #             return Path(self.models_export_dir, f"{self.asset_name}_{permutation.name}_{tag_type.name.lower()}.gr2")
        
    def write_sidecar(self):
        self.sidecar.has_armature = bool(self.virtual_scene.skeleton_node)
        self.sidecar.regions = self.regions
        self.sidecar.global_materials = self.global_materials_list
        self.sidecar.structure = self.virtual_scene.structure
        self.sidecar.design = self.virtual_scene.design
        self.sidecar.build()
        
    def preprocess_tags(self): ...
    
    def invoke_tool_import(self):
        sidecar_importer = SidecarImport(self.asset_path, self.asset_name, self.asset_type, self.sidecar_path, self.scene_settings, self.export_settings, self.selected_bsps, self.corinth, self.virtual_scene.structure)
        # if self.asset_type in {AssetType.SCENARIO, AssetType.PREFAB}:
        #     sidecar_importer.save_lighting_infos()
        sidecar_importer.run()
        # if sidecar_importer.lighting_infos:
        #     sidecar_importer.restore_lighting_infos()
        if self.asset_type == AssetType.ANIMATION:
            sidecar_importer.cull_unused_tags()
            
    def postprocess_tags(self):
        pass
        
    
def get_marker_sphere_size(ob):
    scale = ob.matrix_world.to_scale()
    max_abs_scale = max(abs(scale.x), abs(scale.y), abs(scale.z))
    return utils.jstr(ob.empty_display_size * max_abs_scale)

def decorator_int(ob):
    match ob.nwo.decorator_lod:
        case "high":
            return 1
        case "medium":
            return 2
        case "low":
            return 3
        case _:
            return 4