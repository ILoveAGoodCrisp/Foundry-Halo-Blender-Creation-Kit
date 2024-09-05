from collections import defaultdict
from enum import Enum
import os
from pathlib import Path
import tempfile
import time
import bpy
from mathutils import Matrix

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
    
class SidecarData:
    gr2_path: Path
    blend_path: Path
    permutation: str
    
    def __init__(self, gr2_path: Path, data_dir: Path, permutation: str):
        self.gr2_path = gr2_path.relative_to(data_dir)
        self.blend_path = Path(bpy.data.filepath).relative_to(data_dir)
        self.permutation = permutation
        
class ExportScene:
    '''Scene to hold all the export objects'''
    context: bpy.types.Context
    asset_type: AssetType
    asset_name: str
    asset_path: Path
    corinth: bool
    game_version: GameVersion
    scene_settings: NWO_ScenePropertiesGroup
    export_settings: NWO_HaloExportPropertiesGroup
    tags_dir: Path
    data_dir: Path
    root_dir: Path
    warning_hit: bool
    bsps_with_structure: set
    disabled_collections: set[bpy.types.Collection]
    export_objects: list[bpy.types.Object]
    permutations: list[str]
    regions: list[str]
    global_materials: list[str]
    
    def __init__(self, context, asset_type, asset_name, asset_path, corinth, export_settings):
        self.context = context
        self.asset_type = AssetType[asset_type.upper()]
        self.asset_name = asset_name
        self.asset_path = asset_path
        self.corinth = corinth
        self.tags_dir = Path(utils.get_tags_path())
        self.data_dir = Path(utils.get_data_path())
        self.root_dir = self.data_dir.parent
        self.depsgraph: bpy.types.Depsgraph = None
        self.virtual_scene: VirtualScene = None
        self.no_parent_objects = []
        self.default_region = context.scene.nwo.regions_table[0].name
        self.default_permutation = context.scene.nwo.permutations_table[0].name
        
        self.game_version = 'corinth' if corinth else 'reach'
        self.export_settings = export_settings
        self.sidecar_info: list[SidecarData] = []
        
        self.project_root = Path(utils.get_tags_path()).parent
        
        os.chdir(tempfile.gettempdir())
        
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
            
        self.virtual_scene = VirtualScene(self.asset_type, self.depsgraph)
        
        # Create default material
        if self.corinth:
            default_material = VirtualMaterial(r"shaders\invalid.material")
        else:
            default_material = VirtualMaterial(r"shaders\invalid.shader")
            
        self.virtual_scene.materials["invalid"] = default_material
            
    def setup_skeleton(self):
        armature = utils.get_rig(self.context)
        if armature:
            self.virtual_scene.set_skeleton(armature)
    
    def create_virtual_geometry(self):
        process = "--- Creating Virtual Geometry"
        len_export_obs = len(self.export_objects)
        with utils.Spinner():
            utils.update_job_count(process, "", 0, len_export_obs)
            for idx, ob in enumerate(self.export_objects):
                props, region, permutation = self.get_halo_props(ob)
                if props is not None:
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
        instanced_object = (object_type == '_connected_geometry_object_type_mesh' and nwo.mesh_type == '_connected_geometry_mesh_type_object_instance')
        
        if self.asset_type.supports_permutations:
            if not instanced_object and (is_light or self.asset_type.supports_bsp or nwo.marker_uses_regions):
                reg = utils.true_region(nwo)
                if reg in self.regions:
                    self.virtual_scene.regions.add(reg)
                    region = utils.true_region(nwo)
                else:
                    self.warning_hit = True
                    utils.print_warning(f"Object [{ob.name}] has {self.reg_name} [{reg}] which is not present in the {self.reg_name}s table. Setting {self.reg_name} to: {self.default_region}")
                    
            if (is_light or self.asset_type.supports_bsp) and not instanced_object:
                perm = utils.true_permutation(nwo)
                if perm in self.permutations:
                    self.virtual_scene.permutations.add(perm)
                    permutation = utils.true_permutation(nwo)
                else:
                    self.warning_hit = True
                    utils.print_warning(f"Object [{ob.name}] has {self.perm_name} [{perm}] which is not presented in the {self.perm_name}s table. Setting {self.perm_name} to: {self.default_permutation}")
                    
            elif nwo.marker_uses_regions and nwo.marker_permutation_type == 'include' and nwo.marker_permutations:
                marker_perms = [item.name for item in nwo.marker_permutations]
                for perm in marker_perms:
                    if perm in self.permutations:
                        self.virtual_scene.permutations.add(perm)
                    else:
                        self.warning_hit = True
                        utils.print_warning(f"Object [{ob.name}] has {self.perm_name} [{perm}] in its include list which is not presented in the {self.perm_name}s table. Ignoring {self.perm_name}")
            
        if object_type == '_connected_geometry_object_type_mesh':
            if nwo.mesh_type == '':
                nwo.mesh_type = '_connected_geometry_mesh_type_default'
            if utils.type_valid(nwo.mesh_type, self.asset_type.name.lower(), self.game_version):
                props = self._setup_mesh_properties(ob, ob.nwo, self.asset_type.supports_bsp, props)
                if props is None:
                    return
                
            else:
                self.warning_hit = True
                return utils.print_warning(f"{ob.name} has invalid mesh type [{nwo.mesh_type}] for asset [{self.asset_type}]. Skipped")
                
        elif object_type == '_connected_geometry_object_type_marker':
            if nwo.marker_type == '':
                nwo.marker_type = '_connected_geometry_marker_type_model'
            if utils.type_valid(nwo.marker_type, self.asset_type.name.lower(), self.game_version):
                props = self._setup_marker_properties(ob, ob.nwo, props)
                if props is None:
                    return
            else:
                self.warning_hit = True
                return utils.print_warning(f"{ob.name} has invalid marker type [{nwo.mesh_type}] for asset [{self.asset_type}]. Skipped")
        # add region/global_mat to sets
        uses_global_mat = self.asset_type.supports_global_materials and (props.get("bungie_mesh_type") in ("_connected_geometry_mesh_type_collision", "_connected_geometry_mesh_type_physics", "_connected_geometry_mesh_type_poop", "_connected_geometry_mesh_type_poop_collision") or self.asset_type == 'scenario' and not self.corinth and ob.get("bungie_mesh_type") == "_connected_geometry_mesh_type_default")
        if uses_global_mat:
            self.global_materials.add(props.get("bungie_face_global_material"))
        
        return props, region, permutation
    
    def _setup_mesh_properties(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, supports_bsp: bool, props: dict):
        mesh_type = ob.data.nwo.mesh_type
        mesh = ob.data
        data_nwo: NWO_MeshPropertiesGroup = mesh.nwo
        
        if supports_bsp:
            # The ol switcheroo
            if mesh_type == '_connected_geometry_mesh_type_default':
                mesh_type = '_connected_geometry_mesh_type_poop'
            elif mesh_type == '_connected_geometry_mesh_type_structure':
                self.bsps_with_structure.add(props.get("bungie_region_name"))
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
            props = self._setup_instanced_object_props(ob, nwo, props)
        elif mesh_type == '_connected_geometry_mesh_type_poop':
            self._setup_poop_props(ob)
        elif mesh_type == '_connected_geometry_mesh_type_default' and self.corinth and self.asset_type == 'scenario':
            props["bungie_face_type"] = '_connected_geometry_face_type_sky'
        
        return props
        
    def _setup_physics_props(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict):
        prim_type = nwo.mesh_primitive_type
        props["bungie_mesh_primitive_type"] = prim_type
        if prim_type != '_connected_geometry_primitive_type_none':
            self.physics_prims.add(ob)
        elif self.corinth and nwo.mopp_physics:
            props["bungie_mesh_primitive_type"] = "_connected_geometry_primitive_type_mopp"
            props["bungie_havok_isshape"] = "1"
            
        return props
    
    def _setup_instanced_object_props(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict):
        props["bungie_marker_all_regions"] = utils.bool_str(not nwo.marker_uses_regions)
        if nwo.marker_uses_regions:
            props["bungie_marker_region"] = ob.nwo.region_name
            props["bungie_face_region"] = utils.true_region(nwo)
            self.validated_regions.add(nwo.region_name)
            m_perms = nwo.marker_permutations
            if m_perms:
                m_perm_set = set()
                for perm in m_perms:
                    self.validated_permutations.add(perm.name)
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
        
    def _setup_marker_properties(self, ob: bpy.types.Object, nwo: NWO_ObjectPropertiesGroup, props: dict):
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
                
        self.export_info = ExportInfo(list(self.virtual_scene.regions), list(self.virtual_scene.global_materials)).create_info()
                
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
            self.sidecar_info.append(SidecarData(granny_path, self.data_dir, nodes[0].permutation))
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
        granny = Granny(Path(self.project_root, "granny2_x64.dll"), filepath)
        start = time.perf_counter()
        tree_start = time.perf_counter()
        print("from tree start")
        granny.from_tree(self.virtual_scene, virtual_objects)
        print("from tree", time.perf_counter() - tree_start)
        creation_start = time.perf_counter()
        print("creation start")
        granny.create_materials()
        granny.create_skeletons(export_info=self.export_info)
        granny.create_vertex_data()
        granny.create_tri_topologies()
        granny.create_meshes()
        granny.create_models()
        print("creation", time.perf_counter() - creation_start)
        print("transform")
        granny.transform()
        print("save")
        granny.save()
        print("done")
        end = time.perf_counter()
        print("granny time: ", end - start)
        
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