# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2022 Generalkidd & Crisp
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

from datetime import datetime
from xml.etree.ElementTree import SubElement
import bpy
import os
from os.path import exists as file_exists
import getpass

import xml.etree.cElementTree as ET
import xml.dom.minidom

EKPath = bpy.context.preferences.addons['io_scene_halo'].preferences.hrek_path

#clean editing kit path
EKPath = EKPath.replace('"','')
EKPath = EKPath.strip('\\')


def export_xml(report, filePath="", export_sidecar=False, sidecar_type='MODEL', asset_path=''):
    print('asset path = ' + asset_path)
    full_path = asset_path
    asset_path = CleanAssetPath(asset_path)
    asset_name = asset_path.rpartition('\\')[2]

    if export_sidecar and asset_path != '':
        if sidecar_type == 'MODEL':
            GenerateModelSidecar(asset_path, asset_name, full_path)

def CleanAssetPath(path):
    path = path.replace('"','')
    path = path.strip('\\')
    path = path.replace(EKPath + '\\data\\','')

    return path

def GenerateModelSidecar(asset_path, asset_name, full_path):
    m_encoding = 'UTF-8'

    print("beep boop I'm writing a model sidecar")

    metadata = ET.Element("Metadata")
    WriteHeader(metadata)
    GetObjectOutputTypes(metadata, "model", asset_path, asset_name, GetModelTags())
    WriteFolders(metadata)
    WriteFaceCollections(metadata, True, True)
    WriteModelContents(metadata, asset_path, asset_name)

    dom = xml.dom.minidom.parseString(ET.tostring(metadata))
    xml_string = dom.toprettyxml()
    part1, part2 = xml_string.split('?>')

    with open(full_path + '\\' + asset_name + '.sidecar.xml', 'w') as xfile:
        xfile.write(part1 + 'encoding=\"{}\"?>\n'.format(m_encoding) + part2)
        xfile.close()

def GenerateStructureSidecar(asset_path):
    print(asset_path)
    m_encoding = 'UTF-8'

    metadata = ET.Element("Metadata")
    WriteHeader(metadata)

    dom = xml.dom.minidom.parseString(ET.tostring(metadata))
    xml_string = dom.toprettyxml()
    part1, part2 = xml_string.split('?>')

    with open(asset_path + 'temp.sidecar.xml', 'w') as xfile:
        xfile.write(part1 + 'encoding=\"{}\"?>\n'.format(m_encoding) + part2)
        xfile.close()

def GenerateDecoratorSidecar(asset_path):
    print(asset_path)

def GenerateParticleSidecar(asset_path):
    print(asset_path)

def WriteHeader(metadata):
    header = ET.SubElement(metadata, "Header")
    ET.SubElement(header, "MainRev").text = "0"
    ET.SubElement(header, "PointRev").text = "6"
    ET.SubElement(header, "Description").text = "Created using the Halo Blender Toolset"
    ET.SubElement(header, "Created").text = str(datetime.today().strftime('%Y-%m-%d'))
    ET.SubElement(header, "By").text = getpass.getuser()
    ET.SubElement(header, "DirectoryType").text = "TAE.Shared.NWOAssetDirectory"
    ET.SubElement(header, "Schema").text = "1"

def GetModelTags():
    # PLACEHOLDER
    tags = ['model']

    if True: 
        tags.append('biped')
    if True:
        tags.append('crate')
    if True:
        tags.append('creature')
    if True:
        tags.append('device_control')
    if True:
        tags.append('device_machine')
    if True:
        tags.append('device_terminal')
    if True:
        tags.append('effect_scenery')
    if True:
        tags.append('equipment')
    if True:
        tags.append('giant')
    if True:
        tags.append('scenery')
    if True:
        tags.append('vehicle')
    if True:
        tags.append('weapon')

    return tags

def GetObjectOutputTypes(metadata, type, asset_path, asset_name, output_tags):
    asset = ET.SubElement(metadata, "Asset", Name=asset_name, Type=type)
    tagcollection = ET.SubElement(asset, "OutputTagCollection")

    for tag in output_tags:
        ET.SubElement(tagcollection, "OutputTag", Type=tag).text = asset_path + '\\' + asset_name

def WriteFolders(metadata):
    folders = ET.SubElement(metadata, "Folders")

    ET.SubElement(folders, "Reference").text = "\\reference"
    ET.SubElement(folders, "Temp").text = "\\temp"
    ET.SubElement(folders, "SourceModels").text = "\\models\\work"
    ET.SubElement(folders, "GameModels").text = "\\models"
    ET.SubElement(folders, "GamePhysicsModels").text = "\\models"
    ET.SubElement(folders, "GameCollisionModels").text = "\\models"
    ET.SubElement(folders, "ExportModels").text = "\\export\\models"
    ET.SubElement(folders, "ExportPhysicsModels").text = "\\export\\models"
    ET.SubElement(folders, "ExportCollisionModels").text = "\\export\\models"
    ET.SubElement(folders, "SourceAnimations").text = "\\animations\\work"
    ET.SubElement(folders, "AnimationsRigs").text = "\\animations\\rigs"
    ET.SubElement(folders, "GameAnimations").text = "\\animations"
    ET.SubElement(folders, "ExportAnimations").text = "\\export\\animations"
    ET.SubElement(folders, "SourceBitmaps").text = "\\bitmaps"
    ET.SubElement(folders, "GameBitmaps").text = "\\bitmaps"
    ET.SubElement(folders, "CinemaSource").text = "\\cinematics"
    ET.SubElement(folders, "CinemaExport").text = "\\export\\cinematics"
    ET.SubElement(folders, "ExportBSPs").text = "\\models"
    ET.SubElement(folders, "SourceBSPs").text = "\\models"
    ET.SubElement(folders, "Scripts").text = "\\scripts"

def WriteFaceCollections(metadata, regions=False, materials=False):
    if(regions or materials):
        faceCollections = ET.SubElement(metadata, "FaceCollections")

        if(regions):
            region_list = ["default",""]
            f1 = ET.SubElement(faceCollections, "FaceCollection", Name="regions", StringTable="connected_geometry_regions_table", Description="model regions")

            FaceCollectionsEntries = ET.SubElement(f1, "FaceCollectionEntries")
            ET.SubElement(FaceCollectionsEntries, "FaceCollectionEntry", Index="0", Name="default", Active="true")

            count = 1
            for ob in bpy.data.objects:
                region = ob.halo_json.Region_Name
                if region not in region_list:
                    ET.SubElement(FaceCollectionsEntries, "FaceCollectionEntry", Index=str(count), Name=region, Active="true")
                    region_list.append(region)
                    count += 1
        if(materials):
            mat_list = ["default",""]
            f2 = ET.SubElement(faceCollections, "FaceCollection", Name="global materials overrides", StringTable="connected_geometry_global_material_table", Description="Global material overrides")

            FaceCollectionsEntries2 = ET.SubElement(f2, "FaceCollectionEntries")
            ET.SubElement(FaceCollectionsEntries2, "FaceCollectionEntry", Index="0", Name="default", Active="true")

            count = 1
            for ob in bpy.data.objects:
                material = ob.halo_json.Face_Global_Material
                if material not in mat_list:
                        ET.SubElement(FaceCollectionsEntries2, "FaceCollectionEntry", Index=str(count), Name=material, Active="true")
                        mat_list.append(material)
                        count += 1

def WriteModelContents(metadata, asset_path, asset_name):
    ##### RENDER #####
    contents = ET.SubElement(metadata, "Contents")
    content = ET.SubElement(contents, "Content", Name=asset_name, Type='model')
    object = ET.SubElement(content, 'ContentObject', Name='', Type="render_model")

    for perm in bpy.data.collections:
        if perm.name == 'Collection':
            perm = 'default'
        else:
            perm = perm.name

        network = ET.SubElement(object, 'ContentNetwork' ,Name=perm, Type="")
        ET.SubElement(network, 'InputFile').text = GetInputFilePath(asset_path, asset_name, perm, 'render')
        ET.SubElement(network, 'IntermediateFile').text = Name=GetIntermediateFilePath(asset_path, asset_name, perm, 'render')

    output = ET.SubElement(content, 'OutputTagCollection')
    ET.SubElement(output, 'OutputTag', Type='render_model').text = asset_path + '\\' + asset_name

    ##### PHYSICS #####
    if SceneHasPhysicsObject():
        object = ET.SubElement(content, 'ContentObject', Name='', Type="physics_model")

        for perm in bpy.data.collections:
            if perm.name == 'Collection':
                perm = 'default'
            else:
                perm = perm.name

            network = ET.SubElement(object, 'ContentNetwork' ,Name=perm, Type="")
            ET.SubElement(network, 'InputFile').text = GetInputFilePath(asset_path, asset_name, perm, 'physics')
            ET.SubElement(network, 'IntermediateFile').text = GetIntermediateFilePath(asset_path, asset_name, perm, 'physics')

    output = ET.SubElement(content, 'OutputTagCollection')
    ET.SubElement(output, 'OutputTag', Type='physics_model').text = asset_path + '\\' + asset_name

    ##### COLLISION #####    
    if SceneHasCollisionObject():
        object = ET.SubElement(content, 'ContentObject', Name='', Type="collision_model")

        for perm in bpy.data.collections:
            if perm.name == 'Collection':
                perm = 'default'
            else:
                perm = perm.name

            network = ET.SubElement(object, 'ContentNetwork' ,Name=perm, Type="")
            ET.SubElement(network, 'InputFile').text = GetInputFilePath(asset_path, asset_name, perm, 'collision')
            ET.SubElement(network, 'IntermediateFile').text = GetIntermediateFilePath(asset_path, asset_name, perm, 'collision')

    output = ET.SubElement(content, 'OutputTagCollection')
    ET.SubElement(output, 'OutputTag', Type='collision_model').text = asset_path + '\\' + asset_name

    ##### SKELETON #####
    object = ET.SubElement(content, 'ContentObject', Name='', Type="skeleton")
    network = ET.SubElement(object, 'ContentNetwork' ,Name='default', Type="")
    ET.SubElement(network, 'InputFile').text = GetInputFilePath(asset_path, asset_name, perm, 'skeleton')
    ET.SubElement(network, 'IntermediateFile').text = GetIntermediateFilePath(asset_path, asset_name, perm, 'skeleton')
    output = ET.SubElement(content, 'OutputTagCollection')
    
    ##### MARKERS #####
    if SceneHasMarkers():
        object = ET.SubElement(content, 'ContentObject', Name='', Type="markers")

        for perm in bpy.data.collections:
            if perm.name == 'Collection':
                perm = 'default'
            else:
                perm = perm.name

            network = ET.SubElement(object, 'ContentNetwork' ,Name='default', Type="")
            ET.SubElement(network, 'InputFile').text = GetInputFilePath(asset_path, asset_name, perm, 'markers')
            ET.SubElement(network, 'IntermediateFile').text = GetIntermediateFilePath(asset_path, asset_name, perm, 'markers')
        
        output = ET.SubElement(content, 'OutputTagCollection')

def GetInputFilePath(asset_path, asset_name, perm, type):
    path = asset_path + '\\models\\' + asset_name
    if type != 'skeleton' and type != 'markers':
        if perm != 'default':
            path = path + '_' + perm
    path = path + '_' + type + '.fbx'

    return path

def GetIntermediateFilePath(asset_path, asset_name, perm, type):
    path = asset_path + '\\export\\models\\' + asset_name
    if type != 'skeleton' and type != 'markers':
        if perm != 'default':
            path = path + '_' + perm
    path = path + '_' + type + '.gr2'

    return path

def SceneHasCollisionObject():
    boolean = False

    for ob in bpy.data.objects:
        if ob.name.startswith('@') or ob.halo_json.ObjectMesh_Type == 'COLLISION':
            boolean = True
    
    return boolean

def SceneHasPhysicsObject():
    boolean = False

    for ob in bpy.data.objects:
        if ob.name.startswith('$') or ob.halo_json.ObjectMesh_Type == 'PHYSICS':
            boolean = True
    
    return boolean

def SceneHasMarkers():
    boolean = False

    for ob in bpy.data.objects:
        if ob.name.startswith('#') or ob.halo_json.Object_Type_All == 'MARKER' or ob.halo_json.Object_Type_No_Mesh == 'MARKER':
            boolean = True
    
    return boolean

# def IntermediateFileExists(folderName):
#     filePath = "fullPath" + "\\" + folderName

#     for fname in os.listdir(filePath):
#         if fname.endswith('.gr2'):
#             return True
#         else:
#             return False

# def GetModelContentObjects(metadata):
#     temp = []
#     ContentObjects = ET.SubElement(metadata, "Content", Name="assetName", Type="model")

#     if(IntermediateFileExists("render")):
#         CreateContentObject(ContentObjects, "render")

#     if(IntermediateFileExists("physics")):
#         CreateContentObject(ContentObjects, "physics")

#     if(IntermediateFileExists("collision")):
#         CreateContentObject(ContentObjects, "collision")

#     if(IntermediateFileExists("markers")):
#         CreateContentObject(ContentObjects, "markers")

#     if(IntermediateFileExists("skeleton")):
#         CreateContentObject(ContentObjects, "skeleton")

#     if(IntermediateFileExists("animations\\JMM") or IntermediateFileExists("animations\\JMA") or IntermediateFileExists("animations\\JMT") or IntermediateFileExists("animations\\JMZ") or IntermediateFileExists("animations\\JMV")
#         or IntermediateFileExists("animations\\JMO (Keyframe)") or IntermediateFileExists("animations\\JMO (Pose)") or IntermediateFileExists("animations\\JMR (Object)") or IntermediateFileExists("animations\\JMR (Local)")):
#         animations = ET.SubElement(ContentObjects, "ContentObject", Name="", Type="model_animation_graph")

#         if(IntermediateFileExists("animations\\JMM")):
#             CreateContentObject(animations, "animations\\JMM", "Base", "ModelAnimationMovementData", "None", "", "")

#         if(IntermediateFileExists("animations\\JMA")):
#             CreateContentObject(animations, "animations\\JMA", "Base", "ModelAnimationMovementData", "XY", "", "")

#         if(IntermediateFileExists("animations\\JMT")):
#             CreateContentObject(animations, "animations\\JMT", "Base", "ModelAnimationMovementData", "XYYaw", "", "")

#         if(IntermediateFileExists("animations\\JMZ")):
#             CreateContentObject(animations, "animations\\JMZ", "Base", "ModelAnimationMovementData", "XYZYaw", "", "")

#         if(IntermediateFileExists("animations\\JMV")):
#             CreateContentObject(animations, "animations\\JMV", "Base", "ModelAnimationMovementData", "XYZFullRotation", "", "")

#         if(IntermediateFileExists("animations\\JMO (Keyframe)")):
#             CreateContentObject(animations, "animations\\JMO (Keyframe)", "Overlay", "ModelAnimationOverlayType", "Keyframe", "ModelAnimationOverlayBlending", "Additive")

#         if(IntermediateFileExists("animations\\JMO (Pose)")):
#             CreateContentObject(animations, "animations\\JMO (Pose)", "Overlay", "ModelAnimationOverlayType", "Pose", "ModelAnimationOverlayBlending", "Additive")

#         if(IntermediateFileExists("animations\\JMR (Local)")):
#             CreateContentObject(animations, "animations\\JMR (Local)", "Overlay", "ModelAnimationOverlayType", "keyframe", "ModelAnimationOverlayBlending", "ReplacementLocalSpace")

#         if(IntermediateFileExists("animations\\JMR (Object)")):
#             CreateContentObject(animations, "animations\\JMR (Object)", "Overlay", "ModelAnimationOverlayType", "keyframe", "ModelAnimationOverlayBlending", "ReplacementObjectSpace")

#         r2 = ET.SubElement(animations, "OutputTagCollection")
#         ET.SubElement(r2, "OutputTag", Type="frame_event_list").text = "dataPath" + "\\" + "assetName"
#         ET.SubElement(r2, "OutputTag", Type="model_animation_graph").text = "dataPath" + "\\" + "assetName"

# def CreateContentObject(ContentObjects, type):
#     files = []
#     path = "fullPath" + "\\" + type
    
#     for (root, dirs, file) in os.walk(path):
#         for fi in file:
#             if '.gr2' in fi:
#                 files.add(fi)
    
#     if(type == "markers" or type == "skeleton"):
#         ET.SubElement(ContentObjects, "ContentObject", Name="", Type=type)
#     else:
#         ET.SubElement(ContentObjects, "ContentObject", Name="", Type=str(type + "_model"))

#     for f in files:
#         r1 = ET.SubElement(ContentObjects, "ContentNetwork", Name=getFileNames(f), Type="")
#         ET.SubElement(r1, "InputFile").text = "dataPath" + "\\" + type + "\\" + getFileNames(f) + "inputFileType"
#         ET.SubElement(r1, "IntermediateFile").text = "dataPath" + "\\" + type + "\\" + getFileNames(f)
    
#     if(type == "markers" or type == "skeleton"):
#         ET.SubElement(ContentObjects, "OutputTagCollection")
#     else:
#         r2 = ET.SubElement(ContentObjects, "OutputTagCollection")
#         ET.SubElement(r2, "OutputTag", Type=str(type + "_model")).text = "dataPath" + "\\" + "assetName"

# def CreateContentObject(animations, type1, type2, type3, type4, type5, type6):
#     files = []
#     path = "fullPath" + "\\" + type
    
#     for (root, dirs, file) in os.walk(path):
#         for fi in file:
#             if '.gr2' in fi:
#                 files.add(fi)
    
#     for f in files:
#         if(type5 == "" or type6 == ""):
#             r1 = ET.SubElement(animations, "ContentNetwork", Name=getFileNames(f), Type=type2, type3=type4)
#             ET.SubElement(r1, "InputFile").text = "dataPath" + "\\" + type1 + "\\" + getFileNames(f) + "inputFileType"
#             ET.SubElement(r1, "IntermediateFile").text = "dataPath" + "\\" + type1 + "\\" + getFileNames(f)
#         else:
#             r1 = ET.SubElement(animations, "ContentNetwork", Name=getFileNames(f), Type=type2, type3=type4, type5=type6)
#             ET.SubElement(r1, "InputFile").text = "dataPath" + "\\" + type1 + "\\" + getFileNames(f) + "inputFileType"
#             ET.SubElement(r1, "IntermediateFile").text = "dataPath" + "\\" + type1 + "\\" + getFileNames(f)

# def getFileNames(file):
#     t = []
#     return ""


def save(operator, context, report,
        filepath="",
        use_selection=False,
        use_visible=False,
        use_active_collection=False,
        batch_mode='OFF',
        use_batch_own_dir=False,
        export_sidecar=False,
        sidecar_type='MODEL',
        asset_path='',
        **kwargs
        ):
    export_xml(report, filepath, export_sidecar, sidecar_type, asset_path)
    return {'FINISHED'}