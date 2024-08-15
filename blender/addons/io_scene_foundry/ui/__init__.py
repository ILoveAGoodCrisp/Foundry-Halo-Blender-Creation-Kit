import bpy

from . import bar, node_editor, outliner, viewport, panel
from .panel import animation, asset, help, material, object, scene, sets, setting, tools

classes = [
    bar.NWO_MT_ProjectChooserMenuDisallowNew,
    bar.NWO_MT_ProjectChooserMenu,
    bar.NWO_OT_ProjectChooser,
    bar.NWO_HaloLauncherExplorerSettings,
    bar.NWO_HaloLauncherGameSettings,
    bar.NWO_HaloLauncherGamePruneSettings,
    bar.NWO_HaloLauncherFoundationSettings,
    bar.NWO_HaloExportSettings,
    bar.NWO_HaloExportSettingsScope,
    bar.NWO_HaloExportSettingsFlags,
    bar.NWO_HaloExport,
    bar.NWO_HaloExportPropertiesGroup,
    bar.NWO_OT_StartFoundry,
    node_editor.NWO_OT_HaloMaterialNodes,
    node_editor.NWO_OT_HaloMaterialTilingNode,
    outliner.NWO_OT_PermutationListCollection,
    outliner.NWO_OT_RegionListCollection,
    outliner.NWO_ApplyCollectionType,
    outliner.NWO_ApplyCollectionMenu,
    viewport.NWO_MT_PIE_ApplyTypeMesh,
    viewport.NWO_PIE_ApplyTypeMesh,
    viewport.NWO_OT_ApplyTypeMeshSingle,
    viewport.NWO_OT_ApplyTypeMesh,
    viewport.NWO_MT_PIE_ApplyTypeMarker,
    viewport.NWO_PIE_ApplyTypeMarker,
    viewport.NWO_OT_ApplyTypeMarkerSingle,
    viewport.NWO_OT_ApplyTypeMarker,
    animation.NWO_UL_AnimProps_Events,
    animation.NWO_OT_DeleteAnimation,
    animation.NWO_OT_UnlinkAnimation,
    animation.NWO_OT_SetTimeline,
    animation.NWO_OT_List_Add_Animation_Rename,
    animation.NWO_OT_List_Remove_Animation_Rename,
    animation.NWO_OT_NewAnimation,
    animation.NWO_OT_AnimationRenameMove,
    animation.NWO_UL_AnimationRename,
    animation.NWO_UL_AnimationList,
    animation.NWO_OT_AnimationEventSetFrame,
    animation.NWO_OT_AnimationFramesSyncToKeyFrames,
    animation.NWO_OT_List_Add_Animation_Event,
    animation.NWO_OT_List_Remove_Animation_Event,
    animation.NWO_OT_AnimationEventMove,
    asset.NWO_UL_IKChain,
    asset.NWO_OT_AddIKChain,
    asset.NWO_OT_RemoveIKChain,
    asset.NWO_OT_MoveIKChain,
    asset.NWO_UL_ObjectControls,
    asset.NWO_OT_RemoveObjectControl,
    asset.NWO_OT_BatchAddObjectControls,
    asset.NWO_OT_BatchRemoveObjectControls,
    asset.NWO_OT_SelectObjectControl,
    asset.NWO_OT_ClearAsset,
    asset.NWO_OT_RegisterIcons,
    material.NWO_OT_MaterialOpenTag,
    material.NWO_OpenImageEditor,
    material.NWO_DuplicateMaterial,
    object.NWO_MT_FaceLayerAddMenu,
    object.NWO_MT_FacePropAddMenu,
    object.NWO_UL_FacePropList,
    object.NWO_OT_UpdateLayersFaceCount,
    object.NWO_OT_EditMode,
    object.NWO_OT_FacePropRemove,
    object.NWO_OT_FacePropAdd,
    object.NWO_OT_FacePropAddFaceMode,
    object.NWO_OT_FacePropAddLightmap,
    object.NWO_OT_FaceLayerAdd,
    object.NWO_OT_FaceLayerRemove,
    object.NWO_OT_FaceLayerAssign,
    object.NWO_OT_FaceLayerSelect,
    object.NWO_OT_FaceLayerMove,
    object.NWO_OT_FaceLayerAddFaceMode,
    object.NWO_OT_FaceLayerAddLightmap,
    object.NWO_OT_FaceLayerColor,
    object.NWO_OT_FaceLayerColorAll,
    object.NWO_OT_RegionListFace,
    object.NWO_OT_GlobalMaterialRegionListFace,
    object.NWO_OT_GlobalMaterialMenuFace,
    object.NWO_MT_RegionsMenuSelection,
    object.NWO_MT_SeamBackfaceMenu,
    object.NWO_MT_RegionsMenu,
    object.NWO_MT_FaceRegionsMenu,
    object.NWO_MT_PermutationsMenuSelection,
    object.NWO_MT_PermutationsMenu,
    object.NWO_MT_MarkerPermutationsMenu,
    object.NWO_MT_MeshTypes,
    object.NWO_MT_MarkerTypes,
    object.NWO_UL_FaceMapProps,
    object.NWO_OT_FaceDefaultsToggle,
    object.NWO_MT_MeshPropAddMenu,
    object.NWO_OT_MeshPropRemove,
    object.NWO_OT_MeshPropAddLightmap,
    object.NWO_MT_GlobalMaterialMenu,
    object.NWO_OT_GlobalMaterialGlobals,
    object.NWO_OT_RegionList,
    object.NWO_OT_GlobalMaterialRegionList,
    object.NWO_OT_GlobalMaterialList,
    object.NWO_OT_PermutationList,
    object.NWO_OT_BSPListSeam,
    object.NWO_OT_BSPList,
    object.NWO_UL_MarkerPermutations,
    object.NWO_OT_List_Add_MarkerPermutation,
    object.NWO_OT_List_Remove_MarkerPermutation,
    object.NWO_OT_MeshPropAdd,
    panel.NWO_FoundryPanelProps,
    panel.NWO_FoundryPanelPopover,
    panel.NWO_HotkeyDescription,
    panel.NWO_OpenURL,
    panel.NWO_OT_FoundryTip,
    panel.NWO_OT_PanelUnpin,
    panel.NWO_OT_PanelSet,
    panel.NWO_OT_PanelExpand,
    sets.NWO_RegionsContextMenu,
    sets.NWO_PermutationsContextMenu,
    sets.NWO_UL_Regions,
    sets.NWO_UL_Permutations,
]

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object_context_menu.append(viewport.object_context_apply_types)
    bpy.types.VIEW3D_MT_object_context_menu.append(viewport.object_context_sets)
    bpy.types.OUTLINER_MT_collection.append(viewport.collection_context)
    bpy.types.NODE_MT_add.append(node_editor.node_context_menu)
    bpy.types.VIEW3D_HT_tool_header.append(bar.draw_foundry_toolbar)
    bpy.types.NODE_HT_header.append(bar.draw_foundry_nodes_toolbar)
    bpy.types.VIEW3D_MT_mesh_add.append(viewport.add_halo_scale_model_button)
    bpy.types.VIEW3D_MT_armature_add.append(viewport.add_halo_armature_buttons)
    bpy.types.OUTLINER_HT_header.append(viewport.create_halo_collection)
    bpy.types.VIEW3D_MT_object.append(viewport.add_halo_join)
    bpy.types.TOPBAR_MT_file_import.append(bar.menu_func_import)
    
    bpy.types.Scene.nwo_export = bpy.props.PointerProperty(
        type=bar.NWO_HaloExportPropertiesGroup, name="Halo Export", description=""
    )
    
def unregister():
    del bpy.types.Scene.nwo_export
    bpy.types.TOPBAR_MT_file_import.remove(bar.menu_func_import)
    bpy.types.VIEW3D_HT_tool_header.remove(bar.draw_foundry_toolbar)
    bpy.types.NODE_HT_header.remove(bar.draw_foundry_nodes_toolbar)
    bpy.types.VIEW3D_MT_mesh_add.remove(viewport.add_halo_scale_model_button)
    bpy.types.VIEW3D_MT_armature_add.remove(viewport.add_halo_armature_buttons)
    bpy.types.VIEW3D_MT_object.remove(viewport.add_halo_join)
    bpy.types.OUTLINER_HT_header.remove(viewport.create_halo_collection)
    bpy.types.NODE_MT_add.remove(node_editor.node_context_menu)
    bpy.types.OUTLINER_MT_collection.remove(viewport.collection_context)
    bpy.types.VIEW3D_MT_object_context_menu.remove(viewport.object_context_sets)
    bpy.types.VIEW3D_MT_object_context_menu.remove(viewport.object_context_apply_types)
    for cls in reversed(classes): bpy.utils.unregister_class(cls)