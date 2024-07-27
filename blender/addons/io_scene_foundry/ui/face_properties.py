from math import radians
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
)
from ..utils import bpy_enum_seam, true_region


class NWO_FaceProperties_ListItems(PropertyGroup):
    layer_name: StringProperty()
    face_count: IntProperty(
        options=set(),
    )
    layer_color: FloatVectorProperty(
        subtype="COLOR_GAMMA",
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0,
        max=1,
        options=set(),
    )
    name: StringProperty()
    face_two_sided_override: BoolProperty()
    face_transparent_override: BoolProperty()
    face_draw_distance_override: BoolProperty()
    region_name_override: BoolProperty()
    face_global_material_override: BoolProperty()
    ladder_override: BoolProperty()
    slip_surface_override: BoolProperty()
    breakable_override: BoolProperty()
    decal_offset_override: BoolProperty()
    no_shadow_override: BoolProperty()
    precise_position_override: BoolProperty()
    no_lightmap_override: BoolProperty()
    no_pvs_override: BoolProperty()
    # lightmap
    lightmap_additive_transparency_override: BoolProperty()
    lightmap_resolution_scale_override: BoolProperty()
    lightmap_type_override: BoolProperty()
    lightmap_analytical_bounce_modifier_override: BoolProperty()
    lightmap_general_bounce_modifier_override: BoolProperty()
    lightmap_translucency_tint_color_override: BoolProperty()
    lightmap_lighting_from_both_sides_override: BoolProperty()
    # material lighting
    emissive_override: BoolProperty()
    # Collision stuff
    render_only_override: BoolProperty()
    collision_only_override: BoolProperty()
    sphere_collision_only_override: BoolProperty()
    player_collision_only_override: BoolProperty()
    bullet_collision_only_override: BoolProperty()

    def scene_bsps(self, context):
        bsp_list = []
        for ob in context.scene.objects:
            bsp = true_region(ob.nwo)
            if bsp not in bsp_list and bsp != true_region(context.object.nwo):
                bsp_list.append(bsp)

        items = []
        for index, bsp in enumerate(bsp_list):
            items.append(bpy_enum_seam(bsp, index))

        return items
    
    render_only_ui: BoolProperty()
    collision_only_ui: BoolProperty()
    sphere_collision_only_ui: BoolProperty()
    player_collision_only_ui: BoolProperty()
    bullet_collision_only_ui: BoolProperty()

    face_two_sided_ui: BoolProperty(
        name="Two Sided",
        description="Render the backfacing normal of this mesh, or if this mesh is collision, prevent open edges being treated as such in game",
        options=set(),
    )

    face_transparent_ui: BoolProperty(
        name="Transparent",
        description="Game treats this mesh as being transparent. If you're using a shader/material which has transparency, set this flag",
        options=set(),
    )

    face_two_sided_type_ui: EnumProperty(
        name="Two Sided Policy",
        description="Set how the game should render the opposite side of mesh faces",
        options=set(),
        items=[
            ("two_sided", "Default", "No special properties"),
            ("mirror", "Mirror", "Mirror backside normals from the frontside"),
            ("keep", "Keep", "Keep the same normal on each face side"),
        ]
    )

    region_name_ui: StringProperty(
        name="Region",
        default="default",
        description="The name of the region these faces should be associated with",
    )
    
    face_draw_distance_ui: EnumProperty(
        name="Draw Distance Limit",
        options=set(),
        description="Controls the distance at which the assigned faces will stop rendering",
        items=[
            ('_connected_geometry_face_draw_distance_detail_mid', 'Medium', ''),
            ('_connected_geometry_face_draw_distance_detail_close', 'Close', ''),
        ]
    )


    face_global_material_ui: StringProperty(
        name="Collision Material",
        default="",
        description="Set the Collision Material of this mesh. If the Collision Material name matches a valid material defined in tags\globals\globals.globals then this mesh will automatically take the correct Collision Material response type, otherwise, the Collision Material override can be manually defined in the .model tag",
    )

    ladder_ui: BoolProperty(
        name="Ladder",
        options=set(),
        description="Makes faces climbable",
        default=True,
    )

    slip_surface_ui: BoolProperty(
        name="Slip Surface",
        options=set(),
        description="Assigned faces will be non traversable by the player. Used to ensure the player can not climb a surface regardless of slope angle",
        default=True,
    )

    decal_offset_ui: BoolProperty(
        name="Decal Offset",
        options=set(),
        description="Provides a Z bias to the faces that will not be overridden by the plane build.  If placing a face coplanar against another surface, this flag will prevent Z fighting",
        default=True,
    )
    
    no_shadow_ui: BoolProperty(
        name="No Shadow",
        options=set(),
        description="Prevents faces from casting shadows",
        default=True,
    )

    precise_position_ui: BoolProperty(
        name="Precise Position",
        options=set(),
        description="Disables compression of vertices during export, resulting in more accurate (and expensive) meshes in game. Only use this when you need to",
        default=True,
    )

    no_lightmap_ui: BoolProperty(
        name="Exclude From Lightmap",
        options=set(),
        description="",
        default=True,
    )

    no_pvs_ui: BoolProperty(
        name="Invisible To PVS",
        options=set(),
        description="",
        default=True,
    )

    #########

    # LIGHTMAP

    lightmap_additive_transparency_ui: FloatVectorProperty(
        name="Additive Transparency",
        options=set(),
        description="Overrides the amount and color of light that will pass through the surface. Tint color will override the alpha blend settings in the shader.",
        default=(1.0, 1.0, 1.0),
        subtype="COLOR",
        min=0.0,
        max=1.0,
    )

    lightmap_resolution_scale_ui: IntProperty(
        name="Resolution Scale",
        options=set(),
        description="Determines how much texel space the faces will be given on the lightmap.  1 means less space for the faces, while 7 means more space for the faces. The relationships can be tweaked in the .scenario tag",
        default=3,
        min=0,
        max=7,
    )

    lightmap_photon_fidelity_ui: EnumProperty(
        name="Photon Fidelity",
        options=set(),
        description="",
        default="_connected_material_lightmap_photon_fidelity_normal",
        items=[
            (
                "_connected_material_lightmap_photon_fidelity_normal",
                "Normal",
                "",
            ),
            (
                "_connected_material_lightmap_photon_fidelity_medium",
                "Medium",
                "",
            ),
            ("_connected_material_lightmap_photon_fidelity_high", "High", ""),
            ("_connected_material_lightmap_photon_fidelity_none", "None", ""),
        ],
    )

    # Lightmap_Chart_Group: IntProperty(
    #     name="Lightmap Chart Group",
    #     options=set(),
    #     description="",
    #     default=3,
    #     min=1,
    # )

    lightmap_type_ui: EnumProperty(
        name="Lightmap Type",
        options=set(),
        description="Sets how this should be lit while lightmapping",
        default="_connected_material_lightmap_type_per_pixel",
        items=[
            ("_connected_material_lightmap_type_per_pixel", "Per Pixel", ""),
            ("_connected_material_lightmap_type_per_vertex", "Per Vetex", ""),
        ],
    )

    lightmap_analytical_bounce_modifier_ui: FloatProperty(
        name="Lightmap Analytical Bounce Modifier",
        options=set(),
        description="0 will bounce no energy.  1 will bounce full energy.  Any value greater than 1 will exaggerate the amount of bounced light.  Affects 1st bounce only",
        default=1,
        soft_max=1,
        min=0,
        subtype="FACTOR",
    )

    lightmap_general_bounce_modifier_ui: FloatProperty(
        name="Lightmap General Bounce Modifier",
        options=set(),
        description="0 will bounce no energy.  1 will bounce full energy.  Any value greater than 1 will exaggerate the amount of bounced light.  Affects 1st bounce only",
        default=1,
        soft_max=1,
        min=0,
        subtype="FACTOR",
    )

    lightmap_translucency_tint_color_ui: FloatVectorProperty(
        name="Translucency Tint Color",
        options=set(),
        description="",
        default=(1.0, 1.0, 1.0),
        subtype="COLOR",
        min=0.0,
        max=1.0,
    )

    lightmap_lighting_from_both_sides_ui: BoolProperty(
        name="Lighting From Both Sides",
        options=set(),
        description="",
        default=True,
    )

    # MATERIAL LIGHTING
    
    def update_lighting_attenuation_falloff(self, context):
        if not context.scene.nwo.transforming:
            if self.material_lighting_attenuation_falloff_ui > self.material_lighting_attenuation_cutoff_ui:
                self.material_lighting_attenuation_cutoff_ui = self.material_lighting_attenuation_falloff_ui
            
    def update_lighting_attenuation_cutoff(self, context):
        if not context.scene.nwo.transforming:
            if self.material_lighting_attenuation_cutoff_ui < self.material_lighting_attenuation_falloff_ui:
                self.material_lighting_attenuation_falloff_ui = self.material_lighting_attenuation_cutoff_ui

    material_lighting_attenuation_cutoff_ui: FloatProperty(
        name="Light Cutoff",
        options=set(),
        description="Determines how far light travels before it stops. Leave this at 0 to for realistic light falloff/cutoff",
        min=0,
        default=0,
        update=update_lighting_attenuation_cutoff,
        subtype='DISTANCE',
        unit='LENGTH',
    )

    material_lighting_attenuation_falloff_ui: FloatProperty(
        name="Light Falloff",
        options=set(),
        description="Determines how far light travels before its power begins to falloff",
        min=0,
        default=0,
        update=update_lighting_attenuation_falloff,
        subtype='DISTANCE',
        unit='LENGTH',
    )

    material_lighting_emissive_focus_ui: FloatProperty(
        name="Material Lighting Emissive Focus",
        options=set(),
        description="Controls the spread of the light. 180 degrees will emit light in a hemisphere from each point, 0 degrees will emit light nearly perpendicular to the surface",
        min=0,
        default=radians(180), 
        max=radians(180),
        subtype="ANGLE",
    )

    material_lighting_emissive_color_ui: FloatVectorProperty(
        name="Emissive Color",
        options=set(),
        description="The RGB value of the emitted light",
        default=(1.0, 1.0, 1.0),
        subtype="COLOR",
        min=0.0,
        max=1.0,
    )

    material_lighting_emissive_per_unit_ui: BoolProperty(
        name="Emissive Per Unit",
        options=set(),
        description="When an emissive surface is scaled, determines if the amount of emitted light should be spread out across the surface or increased/decreased to keep a regular amount of light emission per unit area",
        default=False,
    )

    material_lighting_emissive_power_ui: FloatProperty(
        name="Emissive Power",
        options=set(),
        description="The intensity of the emissive surface",
        min=0,
        default=5,
    )

    material_lighting_emissive_quality_ui: FloatProperty(
        name="Emissive Quality",
        options=set(),
        description="Controls the quality of the shadows cast by a complex occluder. For instance, a light casting shadows of tree branches on a wall would require a higher quality to get smooth shadows",
        default=1,
        min=0,
    )

    material_lighting_use_shader_gel_ui: BoolProperty(
        name="Use Shader Gel",
        options=set(),
        description="",
        default=False,
    )

    material_lighting_bounce_ratio_ui: FloatProperty(
        name="Lighting Bounce Ratio",
        options=set(),
        description="0 will bounce no energy. 1 will bounce full energy. Any value greater than 1 will exaggerate the amount of bounced light. Affects 1st bounce only",
        default=1,
        min=0,
    )
