from ctypes import CDLL, c_uint32, cast, cdll, create_string_buffer, pointer
from pathlib import Path

import bpy
from mathutils import Matrix

from .export_classes import *
from .formats import *

dll = None

def granny_get_log_message_type_string(message_type: c_int) -> c_char_p:
    """Granny logging function"""
    dll.GrannyGetLogMessageTypeString.argtypes=[c_int]
    dll.GrannyGetLogMessageTypeString.restype=c_char_p
    result = dll.GrannyGetLogMessageTypeString(message_type)
    return result

def granny_get_log_message_origin_string(origin: c_int) -> c_char_p:
    """Granny logging function"""
    dll.GrannyGetLogMessageOriginString.argtypes=[c_int]
    dll.GrannyGetLogMessageOriginString.restype=c_char_p
    result = dll.GrannyGetLogMessageOriginString(origin)
    return result
    
def output_error(format_string, *args):
    print(format_string % args)
    
def new_callback_function(Type, Origin, SourceFile, SourceLine, Message, UserData):
    output_error(
        "Error(Granny): type %s from subsystem %s: %s" %
        (granny_get_log_message_type_string(Type),
        granny_get_log_message_origin_string(Origin),
        Message)
    )
    
class MaterialExtendedData(Structure):
    """ Halo material type, ditto """
    _pack_ = 1
    _fields_ = [('bungie_shader_path', c_char_p),
                ('bungie_shader_type',c_char_p),]
    
GrannyCallbackType = CFUNCTYPE(
    None,
    c_int,
    c_int,
    c_char_p,
    c_int,
    c_char_p,
    c_void_p
)

class Granny:
    dll: CDLL
    export_materials: list[Material]
    export_skeletons: list[Skeleton]
    export_vertex_datas: list[VertexData]
    export_triangles: list[Indices]
    export_meshes: list[Mesh]
    export_models: list[Model]
    export_track_groups: list[TrackGroup]
    export_animations: list[Animation]
    
    def __init__(self, granny_dll_path: str | Path, filepath: Path):
        self.dll = cdll.LoadLibrary(str(granny_dll_path))
        global dll
        dll = self.dll
        self.file_info_type = POINTER(GrannyDataTypeDefinition).in_dll(self.dll, "GrannyFileInfoType")
        self.magic_value = POINTER(GrannyFileMagic).in_dll(self.dll, "GrannyGRNFileMV_ThisPlatform")
        self.old_callback = GrannyLogCallback()
        self.filename = str(filepath)
        self._create_callback()
        self._create_file_info()
        
    def from_objects(self, objects: list[bpy.types.Object]):
        """Creates granny representations of blender objects"""
        materials = set()
        skeletons = set()
        for ob in objects:
            if not ob.parent:
                skeletons.add(ob)
            if ob.type != 'MESH': continue
            for mat in ob.data.materials:
                materials.add(mat)
                    
        self.export_materials = [Material(i) for i in materials]
        self.export_skeletons = [Skeleton(i) for i in skeletons]
        
    def save(self):
        data_tree_writer = self._begin_file_data_tree_writing()
        if data_tree_writer:
            if self._write_data_tree_to_file(data_tree_writer):
                self._end_file_data_tree_writing(data_tree_writer)
                
    def create_materials(self):
        length = len(self.export_materials)
        granny_materials = [GrannyMaterial() for _ in range(length)]
        array = (POINTER(GrannyMaterial) * length)()
        # array = Array()
        
        for i, (granny_material, export_material) in enumerate(zip(granny_materials, self.export_materials)):
            array[i] = pointer(granny_material)
            granny_material.name = export_material.name
            export_material.create_properties(granny_material)
            
        self.file_info.material_count = length
        self.file_info.materials = array
        
    def create_skeletons(self, export_info):
        length = len(self.export_skeletons)
        skeletons = [GrannySkeleton() for _ in range(length)]
        array = (POINTER(GrannySkeleton) * length)()
        
        for i, (granny_skeleton, export_skeleton) in enumerate(zip(skeletons, self.export_skeletons)):
            array[i] = pointer(granny_skeleton)
            granny_skeleton.name = export_skeleton.name
            granny_skeleton.lod_type = export_skeleton.lod
            length_bones = len(export_skeleton.bones)
            bones = [GrannyBone() for _ in range(length_bones)]
            bone_array = (GrannyBone * length_bones)(*bones)
            
            for j, (granny_bone, export_bone) in enumerate(zip(bone_array, export_skeleton.bones)):
                granny_bone.name = export_bone.name
                granny_bone.parent_index = export_bone.parent_index
            
            granny_skeleton.bone_count = length_bones
            granny_skeleton.bones = cast(bone_array, POINTER(GrannyBone))
        
        self.file_info.skeleton_count = length
        self.file_info.skeletons = array

    def get_version_string(self) -> str:
        """Returns the granny dll version as a string"""
        self.dll.GrannyGetVersionString.restype=c_char_p
        return self.dll.GrannyGetVersionString().decode('UTF-8')
    
    def get_version(self, major_version: c_int32, minor_version: c_int32, build_number: c_int32, customization: c_int32):
        """Returns the granny dll version as pointers"""
        self.dll.GrannyGetVersion.argtypes=[POINTER(c_int32),POINTER(c_int32),POINTER(c_int32),POINTER(c_int32)]
        return self.dll.GrannyGetVersion()
    
    def _begin_file_data_tree_writing(self):
        self.dll.GrannyBeginFileDataTreeWriting.argtypes=[POINTER(GrannyDataTypeDefinition), c_void_p, c_int32, c_int32]
        self.dll.GrannyBeginFileDataTreeWriting.restype=c_void_p
        result = self.dll.GrannyBeginFileDataTreeWriting(self.file_info_type, pointer(self.file_info), 0, 0)
        return result
    
    def _write_data_tree_to_file(self, writer):
        file_name_bytes = self.filename.encode()
        self.dll.GrannyWriteDataTreeToFile.argtypes=[c_void_p, c_uint32, POINTER(GrannyFileMagic), c_char_p, c_int32]
        self.dll.GrannyWriteDataTreeToFile.restype=c_bool
        result = self.dll.GrannyWriteDataTreeToFile(writer, 0x80000037, self.magic_value, file_name_bytes, 1)
        return result
    
    def _end_file_data_tree_writing(self, writer):
        self.dll.GrannyEndFileDataTreeWriting.argtypes=[c_void_p]
        self.dll.GrannyEndFileDataTreeWriting(writer)
        
    def _create_callback(self):
        new_callback = self.old_callback
        new_callback.function = GrannyCallbackType(new_callback_function)
        new_callback.user_data = None
        self._set_log_callback(new_callback)
        
    def _create_file_info(self):
        self.file_info = GrannyFileInfo()
        self.file_info.art_tool_info = pointer(self._create_art_tool_info())
        self.file_info.exporter_info = pointer(self._create_basic_exporter_tool_info())
        self.file_info.file_name = self.filename.encode()
        self.file_info.texture_count = 0
        self.file_info.textures = None
        self.file_info.material_count = 0
        self.file_info.materials = None
        self.file_info.skeleton_count = 0
        self.file_info.skeletons = None
        self.file_info.vertex_data_count = 0
        self.file_info.vertex_datas = None
        self.file_info.tri_topology_count = 0
        self.file_info.tri_topologies = None
        self.file_info.mesh_count = 0
        self.file_info.meshes = None
        self.file_info.model_count = 0
        self.file_info.models = None
        self.file_info.track_group_count = 0
        self.file_info.track_groups = None
        self.file_info.animation_count = 0
        self.file_info.animations = None
        self.file_info.extended_data.type = None
        self.file_info.extended_data.object = None
        
    def _create_art_tool_info(self) -> GrannyFileArtToolInfo:
        tool_info = GrannyFileArtToolInfo()
        tool_info.art_tool_name = b'Blender'
        tool_info.units_per_meter = 39.370079
        tool_info.origin[:] = [0, 0, 0]
        tool_info.right_vector[:] = [0, -1, 0]
        tool_info.up_vector[:] = [0, 0, 1]
        tool_info.back_vector[:] = [-1, 0, 0]
        tool_info.extended_data.type = None
        tool_info.extended_data.object = None
        return tool_info
    
    def _create_basic_exporter_tool_info(self) -> GrannyFileExporterInfo:
        exporter_info = GrannyFileExporterInfo()
        exporter_info.exporter_name = b'Foundry'
        exporter_info.exporter_major_revision = 2
        exporter_info.exporter_minor_revision = 8
        exporter_info.exporter_build_number = 36
        exporter_info.extended_data.type = None
        exporter_info.extended_data.object = None
        return exporter_info
    
    def _set_log_file_name(self, file_name : str, clear : c_bool) -> c_bool:
        """Sets a file for the granny dll to log to.
        granny_set_log_file_name("c:/blargh.txt", true);
        to turn off: granny_set_log_file_name(0, false);
        """
        file_name_bytes = file_name.encode()
        self.dll.GrannySetLogFileName.argtypes=[c_char_p, c_bool]
        self.dll.GrannySetLogFileName.restype=c_bool
        result = self.dll.GrannySetLogFileName(file_name_bytes, clear)
        return result
    
    def _get_log_callback(self, result : GrannyLogCallback):
        """Granny logging function"""
        self.dll.GrannyGetLogCallback.argtypes=[POINTER(GrannyLogCallback)]
        self.dll.GrannyGetLogCallback(result)
        
    def _set_log_callback(self, result : GrannyLogCallback):
        """Granny logging function"""
        self.dll.GrannySetLogCallback.argtypes=[POINTER(GrannyLogCallback)]
        self.dll.GrannySetLogCallback(result)
        
    def _get_log_message_type_string(self, message_type: c_int) -> c_char_p:
        """Granny logging function"""
        self.dll.GrannyGetLogMessageTypeString.argtypes=[c_int]
        self.dll.GrannyGetLogMessageTypeString.restype=c_char_p
        result = self.dll.GrannyGetLogMessageTypeString(message_type)
        return result

    def _get_log_message_origin_string(self, origin: c_int) -> c_char_p:
        """Granny logging function"""
        self.dll.GrannyGetLogMessageOriginString.argtypes=[c_int]
        self.dll.GrannyGetLogMessageOriginString.restype=c_char_p
        result = self.dll.GrannyGetLogMessageOriginString(origin)
        return result
    
    def _get_log_message_type_string(self, message_type: c_int) -> c_char_p:
        """Granny logging function"""
        self.dll.GrannyGetLogMessageTypeString.argtypes=[c_int]
        self.dll.GrannyGetLogMessageTypeString.restype=c_char_p
        result = self.dll.GrannyGetLogMessageTypeString(message_type)
        return result

    def _get_log_message_origin_string(self, origin: c_int) -> c_char_p:
        """Granny logging function"""
        self.dll.GrannyGetLogMessageOriginString.argtypes=[c_int]
        self.dll.GrannyGetLogMessageOriginString.restype=c_char_p
        result = self.dll.GrannyGetLogMessageOriginString(origin)
        return result