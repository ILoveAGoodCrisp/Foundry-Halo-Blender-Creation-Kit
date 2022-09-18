import bpy
import json

##############################
####### STRING TABLE #########
##############################
def getStrings():
    stringsList = {}

    temp = ({'string_table' : stringsList})

    return temp

##############################
##### NODES PROPERTIES #######
##############################

def getNodes():
    nodesList = {}

    halo_node_prefixes = ('#','b_','b ','frame_','frame ') # these prefixes indicate a mesh should not be written to meshes_properties

    for node in bpy.data.objects:
        if node.name.startswith(halo_node_prefixes):
            nodesList.update({node.name: getNodesProperties()})

    temp = ({'nodes_properties': nodesList})

    return temp

def getNodesProperties():
    node_props = {
        # OBJECT PROPERTIES
        "bungie_object_type": "_connected_geometry_object_type_frame"

    }

    return node_props

##############################
##### MESHES PROPERTIES ######
##############################

def getMeshes():
    meshesList = {}

    halo_node_prefixes = ('#','b_','b ','frame_','frame ') # these prefixes indicate a mesh should not be written to meshes_properties

    for mesh in bpy.data.meshes:
        if (not mesh.name.startswith(halo_node_prefixes)): # if the name of a mesh starts with this, don't process it.
            meshesList.update({mesh.name: getMeshProperties()})

    temp = ({'meshes_properties': meshesList})

    return temp

def getMeshProperties():
    print("here we go")

    mesh_props = {
        # OBJECT PROPERTIES
        "bungie_object_type": "_connected_geometry_object_type_mesh",
        "bungie_region_name": getRegionName(),
        # FACE PROPERTIES
        "bungie_face_type": getFaceType()

    }

    return mesh_props

def getRegionName():
    return 'region'

def getFaceType():
    return 'eyo'

##############################
#### MATERIAL PROPERTIES #####
##############################

def getMaterials():
    matList = {}

    halo_special_materials = ("+portal","+seamsealer","+sky","+weatherpoly") # some special material names to match legacy
    halo_valid_shader_types =("shader","shader_cortana","shader_custom","shader_decal","shader_foliage","shader_fur","shader_fur_stencil","shader_glass","shader_halogram","shader_mux","shader_mux_material","shader_screen","shader_skin","shader_terrain","shader_water")

    for ob in bpy.data.objects:
        for mat_slot in ob.material_slots:
            halo_material = mat_slot.material.halo_json
            halo_material_name = mat_slot.material.name
            if halo_material.shader_path != halo_material.shader_path.rpartition('.')[2]: # check to fix issue where partition returns full string if no '.' present
                shaderType = halo_material.shader_path.rpartition('.')[2]  
                shaderPath = halo_material.shader_path.rpartition('.')[0]
            else:
                shaderType = "shader"
                shaderPath = halo_material.shader_path
            
            if shaderType not in halo_valid_shader_types:
                shaderType = "shader"

            if shaderPath == "":
                shaderPath = "shaders\invalid"
                
            if (halo_material_name in halo_special_materials):
                shaderType = "override"
                match halo_material_name:
                    case '+portal':
                        shaderPath = "bungie_mesh_type=_connected_geometry_mesh_type_portal"
                    case '+seamsealer':
                        shaderPath = "bungie_face_type=_connected_geometry_face_type_seam_sealer"
                    case '+sky':
                        shaderPath = "bungie_face_type=_connected_geometry_face_type_sky"
                    case '+weatherpoly':
                        shaderPath = "bungie_face_type=_connected_geometry_face_type_weather_polyhedra"

            matList.update({halo_material_name : {"bungie_shader_path": shaderPath, "bungie_shader_type": shaderType}})

    temp = ({'material_properties': matList})

    return temp

import os
from os.path import exists as file_exists
import tempfile
import ctypes
from subprocess import Popen

def export_asset(report, filePath="", export_gr2=False, delete_fbx=False, delete_json=False):
    pathList = filePath.split(".")
    jsonPath = ""
    for x in range(len(pathList)-1):
        jsonPath += pathList[x]
    jsonPath += ".json"

    build_json(jsonPath, delete_json)

    if export_gr2:
        gr2Path = ""
        for x in range(len(pathList)-1):
            gr2Path += pathList[x]
            gr2Path += ".gr2"

        toolPath = bpy.context.preferences.addons['io_scene_halo'].preferences.hrek_path
        toolPath = toolPath.replace('"','')
        toolPath += "\\tool_fast.exe"

        print('\nTool Path... %r' % toolPath)

        build_gr2(toolPath, filePath, jsonPath, gr2Path)
        if(file_exists(gr2Path)):
            report({'INFO'},"GR2 conversion finished!")
        else:
            report({'INFO'},"GR2 conversion failed!")
            ctypes.windll.user32.MessageBoxW(0, "Tool.exe failed to export your GR2 file. Blender may need to be run as an Administrator or there may be an issue with your project settings.", "GR2 EXPORT FAILED", 0)
        
        if delete_fbx:
            os.remove(filePath)
    return {'FINISHED'}

def build_json(jsonPath, delete_json):
    jsonTemp = {}
    jsonTemp.update(getStrings())
    jsonTemp.update(getNodes())
    jsonTemp.update(getMeshes())
    jsonTemp.update(getMaterials())

    if(delete_json):
        temp = tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".json")
        json.dump(jsonTemp, temp)
        temp.flush()
        return temp.name
    else:
        haloJSON = json.dumps(jsonTemp, indent=4)

        jsonFile = open(jsonPath, "w")
        jsonFile.write(haloJSON)
        jsonFile.close()
        return ""

def build_gr2(toolPath, filePath, jsonPath, gr2Path):
    try:            
        if not os.access(filePath, os.R_OK):
            ctypes.windll.user32.MessageBoxW(0, "GR2 Not Exported. Output Folder Is Read-Only! Try running Blender as an Administrator.", "ACCESS VIOLATION", 0)
        else:
            toolCommand = '"{}" fbx-to-gr2 "{}" "{}" "{}"'.format(toolPath, filePath, jsonPath, gr2Path)
            print('\nRunning Tool command... %r' % toolCommand)
            p = Popen(toolCommand)
            p.wait()
    except:
        ctypes.windll.user32.MessageBoxW(0, "GR2 Not Exported. Please check your HREK editing kit path in add-on preferences and try again.", "Invalid HREK Path", 0)
        os.remove(filePath)
        os.remove(jsonPath)
    finally:
        return {'FINISHED'}

def save(operator, context, report,
        filepath="",
        use_selection=False,
        use_visible=False,
        use_active_collection=False,
        batch_mode='OFF',
        use_batch_own_dir=False,
        export_gr2=False,
        delete_fbx=False,
        delete_json=False,
        **kwargs
        ):
    export_asset(report, filepath, export_gr2, delete_fbx, delete_json)
    return {'FINISHED'}

