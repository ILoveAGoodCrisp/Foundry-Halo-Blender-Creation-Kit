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

import time
import bpy
import os
import json
import asyncio
import random
from .format_json import NWOJSON
from ..utils.nwo_utils import (
    data_relative,
    disable_prints,
    dot_partition,
    enable_prints,
    get_data_path,
    run_tool,
    print_box,
    sort_alphanum,
    update_job,
    update_progress,
)

#####################################################################################
#####################################################################################
# MAIN FUNCTION


class ProcessScene:
    def __init__(
        self,
        context,
        report,
        sidecar_path,
        sidecar_path_full,
        asset,
        asset_path,
        fbx_exporter,
        nwo_scene,
        sidecar_type,
        output_biped,
        output_crate,
        output_creature,
        output_device_control,
        output_device_machine,
        output_device_terminal,
        output_device_dispenser,
        output_effect_scenery,
        output_equipment,
        output_giant,
        output_scenery,
        output_vehicle,
        output_weapon,
        export_skeleton,
        export_render,
        export_collision,
        export_physics,
        export_markers,
        export_animations,
        export_structure,
        export_design,
        export_sidecar_xml,
        lightmap_structure,
        import_to_game,
        export_gr2_files,
        game_version,
        global_scale,
        use_mesh_modifiers,
        mesh_smooth_type,
        use_triangles,
        use_armature_deform_only,
        mesh_smooth_type_better,
        import_check,
        import_force,
        import_verbose,
        import_draft,
        import_seam_debug,
        import_skip_instances,
        import_decompose_instances,
        import_surpress_errors,
    ):
        self.export_report = self.process(
            context,
            report,
            sidecar_path,
            sidecar_path_full,
            asset,
            asset_path,
            fbx_exporter,
            nwo_scene,
            sidecar_type,
            output_biped,
            output_crate,
            output_creature,
            output_device_control,
            output_device_machine,
            output_device_terminal,
            output_device_dispenser,
            output_effect_scenery,
            output_equipment,
            output_giant,
            output_scenery,
            output_vehicle,
            output_weapon,
            export_skeleton,
            export_render,
            export_collision,
            export_physics,
            export_markers,
            export_animations,
            export_structure,
            export_design,
            export_sidecar_xml,
            lightmap_structure,
            import_to_game,
            export_gr2_files,
            game_version,
            global_scale,
            use_mesh_modifiers,
            mesh_smooth_type,
            use_triangles,
            use_armature_deform_only,
            mesh_smooth_type_better,
            import_check,
            import_force,
            import_verbose,
            import_draft,
            import_seam_debug,
            import_skip_instances,
            import_decompose_instances,
            import_surpress_errors,
        )

    def process(
        self,
        context,
        report,
        sidecar_path,
        sidecar_path_full,
        asset,
        asset_path,
        fbx_exporter,
        nwo_scene,
        sidecar_type,
        output_biped,
        output_crate,
        output_creature,
        output_device_control,
        output_device_machine,
        output_device_terminal,
        output_device_dispenser,
        output_effect_scenery,
        output_equipment,
        output_giant,
        output_scenery,
        output_vehicle,
        output_weapon,
        export_skeleton,
        export_render,
        export_collision,
        export_physics,
        export_markers,
        export_animations,
        export_structure,
        export_design,
        export_sidecar_xml,
        lightmap_structure,
        import_to_game,
        export_gr2_files,
        game_version,
        global_scale,
        use_mesh_modifiers,
        mesh_smooth_type,
        use_triangles,
        use_armature_deform_only,
        mesh_smooth_type_better,
        import_check,
        import_force,
        import_verbose,
        import_draft,
        import_seam_debug,
        import_skip_instances,
        import_decompose_instances,
        import_surpress_errors,
    ):
        if fbx_exporter == "better":
            print("Found Better FBX exporter")

        reports = []
        gr2_count = 0

        if sidecar_type != "MODEL" or (
            sidecar_type == "MODEL"
            and (
                output_biped
                or output_crate
                or output_creature
                or output_device_control
                or output_device_machine
                or output_device_terminal
                or output_effect_scenery
                or output_equipment
                or output_giant
                or output_scenery
                or output_vehicle
                or output_weapon
            )
        ):
            self.gr2_processes = []
            self.exported_files = []
            self.sidecar_paths = {}
            self.sidecar_paths_design = {}
            if export_gr2_files:
                self.max_export = 0.5
                self.first_gr2 = True
                self.skeleton_only = False
                print("\n\nStarting Models Export")
                print(
                    "-------------------------------------------------------------------------\n"
                )

                # make necessary directories
                models_dir = os.path.join(asset_path, "models")
                export_dir = os.path.join(asset_path, "export", "models")
                os.makedirs(models_dir, exist_ok=True)
                os.makedirs(export_dir, exist_ok=True)

                if sidecar_type in (
                    "MODEL",
                    "FP ANIMATION",
                ):  # Added FP animation to this. FP animation only exports the skeleton and animations
                    if sidecar_type == "MODEL":
                        if export_render and nwo_scene.render:
                            self.exported_files.append(
                                self.export_model(
                                    context,
                                    asset_path,
                                    asset,
                                    "render",
                                    nwo_scene.render,
                                    nwo_scene.render_perms,
                                    nwo_scene.selected_perms,
                                    nwo_scene.model_armature,
                                    fbx_exporter,
                                    global_scale,
                                    use_mesh_modifiers,
                                    mesh_smooth_type,
                                    use_triangles,
                                    use_armature_deform_only,
                                    mesh_smooth_type_better,
                                    sidecar_type,
                                    nwo_scene,
                                )
                            )

                        if export_collision and nwo_scene.collision:
                            self.export_model(
                                context,
                                asset_path,
                                asset,
                                "collision",
                                nwo_scene.collision,
                                nwo_scene.collision_perms,
                                nwo_scene.selected_perms,
                                nwo_scene.model_armature,
                                fbx_exporter,
                                global_scale,
                                use_mesh_modifiers,
                                mesh_smooth_type,
                                use_triangles,
                                use_armature_deform_only,
                                mesh_smooth_type_better,
                                sidecar_type,
                                nwo_scene,
                            )

                        if export_physics and nwo_scene.physics:
                            self.export_model(
                                context,
                                asset_path,
                                asset,
                                "physics",
                                nwo_scene.physics,
                                nwo_scene.physics_perms,
                                nwo_scene.selected_perms,
                                nwo_scene.model_armature,
                                fbx_exporter,
                                global_scale,
                                use_mesh_modifiers,
                                mesh_smooth_type,
                                use_triangles,
                                use_armature_deform_only,
                                mesh_smooth_type_better,
                                sidecar_type,
                                nwo_scene,
                            )

                        if export_markers and nwo_scene.markers:
                            self.export_model(
                                context,
                                asset_path,
                                asset,
                                "markers",
                                nwo_scene.markers,
                                None,
                                None,
                                nwo_scene.model_armature,
                                fbx_exporter,
                                global_scale,
                                use_mesh_modifiers,
                                mesh_smooth_type,
                                use_triangles,
                                use_armature_deform_only,
                                mesh_smooth_type_better,
                                sidecar_type,
                                nwo_scene,
                            )

                    if export_skeleton:
                        if not self.skeleton_only:
                            self.remove_all_but_armature(nwo_scene)

                        fbx_path, json_path, gr2_path = self.get_path(
                            asset_path, asset, "skeleton", None, None, None
                        )
                        export_obs = [nwo_scene.model_armature]

                        override = context.copy()
                        override["selected_objects"] = export_obs
                        with context.temp_override(**override):
                            job = "-- skeleton"
                            update_job(job, 0)
                            start = time.perf_counter()
                            if self.export_fbx(
                                fbx_exporter,
                                fbx_path,
                                global_scale,
                                use_mesh_modifiers,
                                mesh_smooth_type,
                                use_triangles,
                                use_armature_deform_only,
                                mesh_smooth_type_better,
                            ):
                                if self.export_json(
                                    json_path,
                                    export_obs,
                                    sidecar_type,
                                    asset,
                                    nwo_scene,
                                ):
                                    self.gr2_processes.append(
                                        self.export_gr2(
                                            fbx_path, json_path, gr2_path
                                        )
                                    )
                                else:
                                    return f"Failed to export skeleton JSON: {json_path}"
                            else:
                                return f"Failed to export skeleton FBX: {fbx_path}"

                            end = time.perf_counter()
                            self.max_export = max(self.max_export, end - start)
                            update_job(job, 1)

                        if "skeleton" in self.sidecar_paths.keys():
                            self.sidecar_paths["skeleton"].append(
                                [
                                    data_relative(fbx_path),
                                    data_relative(json_path),
                                    data_relative(gr2_path),
                                ]
                            )
                        else:
                            self.sidecar_paths["skeleton"] = [
                                [
                                    data_relative(fbx_path),
                                    data_relative(json_path),
                                    data_relative(gr2_path),
                                ]
                            ]

                    if (
                        export_animations != "NONE"
                        and nwo_scene.model_armature
                        and bpy.data.actions
                    ):
                        if not self.skeleton_only:
                            self.remove_all_but_armature(nwo_scene)

                        timeline = context.scene
                        print("\n\nStarting Animations Export")
                        print(
                            "-------------------------------------------------------------------------\n"
                        )
                        for action in bpy.data.actions:
                            action_nwo = action.nwo
                            if action_nwo.export_this and (
                                export_animations == "ALL"
                                or nwo_scene.current_action == action
                            ):
                                animation_name = action.nwo.name_override
                                job = f"-- {animation_name}"
                                start = time.perf_counter()
                                update_job(job, 0)
                                self.get_path(
                                    asset_path,
                                    asset,
                                    "animation",
                                    None,
                                    None,
                                    animation_name,
                                )

                                nwo_scene.model_armature.animation_data.action = (
                                    action
                                )
                                if action.use_frame_range:
                                    timeline.frame_start = int(
                                        action.frame_start
                                    )
                                    timeline.frame_end = int(action.frame_end)
                                    context.scene.frame_set(
                                        int(action.frame_start)
                                    )
                                else:
                                    timeline.frame_start = (
                                        nwo_scene.timeline_start
                                    )
                                    timeline.frame_end = nwo_scene.timeline_end
                                    context.scene.frame_set(
                                        nwo_scene.timeline_start
                                    )

                                event_obs = self.create_event_nodes(
                                    context,
                                    action_nwo.animation_events,
                                    timeline.frame_start,
                                    timeline.frame_end,
                                )
                                if event_obs:
                                    export_obs = event_obs.append(
                                        nwo_scene.model_armature
                                    )
                                else:
                                    export_obs = [nwo_scene.model_armature]

                                override = context.copy()
                                override["selected_objects"] = export_obs

                                with context.temp_override(**override):
                                    if self.export_fbx(
                                        fbx_exporter,
                                        fbx_path,
                                        global_scale,
                                        use_mesh_modifiers,
                                        mesh_smooth_type,
                                        use_triangles,
                                        use_armature_deform_only,
                                        mesh_smooth_type_better,
                                    ):
                                        if self.export_json(
                                            json_path,
                                            export_obs,
                                            sidecar_type,
                                            asset,
                                            nwo_scene,
                                        ):
                                            self.gr2_processes.append(
                                                self.export_gr2(
                                                    fbx_path,
                                                    json_path,
                                                    gr2_path,
                                                )
                                            )
                                        else:
                                            return f"Failed to export skeleton JSON: {json_path}"
                                    else:
                                        return f"Failed to export skeleton FBX: {fbx_path}"

                                end = time.perf_counter()
                                self.max_export = max(
                                    self.max_export, end - start
                                )
                                update_job(job, 1)

                                if "animation" in self.sidecar_paths.keys():
                                    self.sidecar_paths["animation"].append(
                                        [
                                            data_relative(fbx_path),
                                            data_relative(json_path),
                                            data_relative(gr2_path),
                                            animation_name,
                                            action_nwo.animation_type,
                                        ]
                                    )
                                else:
                                    self.sidecar_paths["animation"] = [
                                        [
                                            data_relative(fbx_path),
                                            data_relative(json_path),
                                            data_relative(gr2_path),
                                            animation_name,
                                            action_nwo.animation_type,
                                        ]
                                    ]

                elif sidecar_type == "SCENARIO":
                    if export_structure and nwo_scene.structure:
                        bsps_sorted = sort_alphanum(nwo_scene.structure_bsps)
                        self.export_bsp(
                            context,
                            asset_path,
                            asset,
                            bsps_sorted,
                            "bsp",
                            nwo_scene.structure,
                            nwo_scene.structure_perms,
                            nwo_scene.selected_perms,
                            nwo_scene.selected_bsps,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                    if export_design and nwo_scene.design:
                        design_sorted = sort_alphanum(nwo_scene.design_bsps)
                        self.export_bsp(
                            context,
                            asset_path,
                            asset,
                            design_sorted,
                            "design",
                            nwo_scene.design,
                            nwo_scene.design_perms,
                            nwo_scene.selected_perms,
                            nwo_scene.selected_bsps,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                elif sidecar_type == "SKY":
                    if export_render and nwo_scene.render:
                        self.export_model(
                            context,
                            asset_path,
                            asset,
                            "sky",
                            nwo_scene.render,
                            None,
                            None,
                            nwo_scene.model_armature,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                elif sidecar_type == "DECORATOR SET":
                    if export_render and nwo_scene.render:
                        self.export_model(
                            context,
                            asset_path,
                            asset,
                            "decorator",
                            nwo_scene.render,
                            None,
                            None,
                            None,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                elif sidecar_type == "PREFAB":
                    if nwo_scene.structure:
                        self.export_model(
                            context,
                            asset_path,
                            asset,
                            "prefab",
                            nwo_scene.structure,
                            None,
                            None,
                            None,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                else:  # for particles
                    if export_render and nwo_scene.render:
                        self.export_model(
                            context,
                            asset_path,
                            asset,
                            "particle_model",
                            nwo_scene.render,
                            None,
                            None,
                            None,
                            fbx_exporter,
                            global_scale,
                            use_mesh_modifiers,
                            mesh_smooth_type,
                            use_triangles,
                            use_armature_deform_only,
                            mesh_smooth_type_better,
                            sidecar_type,
                            nwo_scene,
                        )

                from .build_sidecar import Sidecar

                sidecar_result = Sidecar(
                    context,
                    sidecar_path,
                    sidecar_path_full,
                    asset_path,
                    asset,
                    nwo_scene,
                    self.sidecar_paths,
                    self.sidecar_paths_design,
                    sidecar_type,
                    output_biped,
                    output_crate,
                    output_creature,
                    output_device_control,
                    output_device_dispenser,
                    output_device_machine,
                    output_device_terminal,
                    output_effect_scenery,
                    output_equipment,
                    output_giant,
                    output_scenery,
                    output_vehicle,
                    output_weapon,
                )

                reports.append(sidecar_result.message)
                print("\n\nBuilding Intermediary Files")
                print(
                    "-------------------------------------------------------------------------\n"
                )

                completed_p = set()
                total_p = len(self.gr2_processes)
                gr2_count = total_p
                fake_p = 0.0
                rand_div = (self.max_export * 3.3) ** 2

                process = "Running GR2 Conversion"
                update_progress(process, 0)
                while len(completed_p) != total_p and fake_p < 1:
                    for p in self.gr2_processes:
                        if p.poll() is not None:
                            completed_p.add(p)

                    fake_p = fake_p + random.random() / rand_div
                    if fake_p < len(completed_p) / total_p:
                        fake_p = len(completed_p) / total_p

                    update_progress(process, fake_p)

                    time.sleep(0.1)

                update_progress(process, 1)

                job = "Verifying GR2 Files"
                update_job(job, 0)
                for p in self.gr2_processes:
                    p.wait()

                # check that gr2 files exist (since fbx-to-gr2 doesn't return a non zero code on faiL!)
                data_path = get_data_path()
                for lists in self.sidecar_paths.values():
                    for path_set in lists:
                        gr2_file = data_path + path_set[2]
                        if (
                            not os.path.exists(gr2_file)
                            or os.stat(gr2_file).st_size == 0
                        ):
                            print(f"\n\nFailed to build GR2: {gr2_file}")
                            print(f"Retrying export...")
                            fbx_file = data_path + path_set[0]
                            json_file = data_path + path_set[1]
                            self.export_gr2(
                                fbx_file, json_file, gr2_file, False
                            )
                            if (
                                os.path.exists(gr2_file)
                                and os.stat(gr2_file).st_size > 0
                            ):
                                print("Success!")
                            else:
                                print(
                                    "Failed to build GR2 File on Second Attempt. Round 3..."
                                )
                                self.export_gr2(
                                    fbx_file, json_file, gr2_file, False
                                )
                                time.sleep(2)
                                if (
                                    os.path.exists(gr2_file)
                                    and os.stat(gr2_file).st_size > 0
                                ):
                                    print("Success!!")
                                else:
                                    return "Failed to build GR2 File on Third Attempt, Giving Up"

                update_job(job, 1)

                # for p in self.gr2_processes:
                #     p.wait()

                reports.append("Exported " + str(gr2_count) + " GR2 Files")

            from .export_tag import import_sidecar

            if import_to_game:
                if os.path.exists(sidecar_path_full):
                    reports.append(
                        import_sidecar(
                            context,
                            sidecar_path,
                            asset_path,
                            asset,
                            import_check,
                            import_force,
                            import_verbose,
                            import_draft,
                            import_seam_debug,
                            import_skip_instances,
                            import_decompose_instances,
                            import_surpress_errors,
                        )
                    )
                else:
                    reports.append(
                        "Skipped tag export, asset sidecar does not exist"
                    )

            if lightmap_structure:
                from .run_lightmapper import run_lightmapper

                reports.append(
                    run_lightmapper(
                        game_version in ("h4", "h2a"),
                        nwo_scene.structure,
                        asset,
                    )
                )

        else:
            report({"ERROR"}, "No sidecar output tags selected")

        final_report = ""
        for idx, r in enumerate(reports):
            final_report = final_report + str(r)
            if idx + 1 < len(reports):
                final_report = final_report + " | "

        return final_report

    def export_model(
        self,
        context,
        asset_path,
        asset,
        type,
        objects,
        obs_perms,
        sel_perms,
        model_armature,
        fbx_exporter,
        global_scale,
        use_mesh_modifiers,
        mesh_smooth_type,
        use_triangles,
        use_armature_deform_only,
        mesh_smooth_type_better,
        sidecar_type,
        nwo_scene,
    ):
        if obs_perms:
            if sel_perms:
                perms = [p for p in obs_perms if p in sel_perms]
            else:
                perms = obs_perms
        else:
            perms = ["default"]

        for perm in perms:
            fbx_path, json_path, gr2_path = self.get_path(
                asset_path, asset, type, perm, None, None
            )
            if model_armature:
                if obs_perms:
                    export_obs = [
                        ob for ob in objects if ob.nwo.permutation_name == perm
                    ]
                    export_obs.append(model_armature)
                else:
                    export_obs = [ob for ob in objects]
                    export_obs.append(model_armature)
            else:
                if obs_perms:
                    export_obs = [
                        ob for ob in objects if ob.nwo.permutation_name == perm
                    ]
                else:
                    export_obs = [ob for ob in objects]

            if type == "prefab":
                print_text = f"prefab"
            elif type == "particle_model":
                print_text = f"particle Model"
            elif type == "decorator":
                print_text = f"decorator"
            elif type == "sky":
                print_text = f"sky"
            elif type == "markers":
                print_text = f"markers"
            else:
                print_text = f"{perm} {type} model"

            override = context.copy()
            override["selected_objects"] = export_obs

            with context.temp_override(**override):
                job = f"-- {print_text}"
                update_job(job, 0)
                start = time.perf_counter()
                if self.export_fbx(
                    fbx_exporter,
                    fbx_path,
                    global_scale,
                    use_mesh_modifiers,
                    mesh_smooth_type,
                    use_triangles,
                    use_armature_deform_only,
                    mesh_smooth_type_better,
                ):
                    if self.export_json(
                        json_path, export_obs, sidecar_type, asset, nwo_scene
                    ):
                        self.gr2_processes.append(
                            self.export_gr2(fbx_path, json_path, gr2_path)
                        )
                    else:
                        return f"Failed to export {perm} {type} model JSON: {json_path}"
                else:
                    return (
                        f"Failed to export {perm} {type} model FBX: {fbx_path}"
                    )

                end = time.perf_counter()
                self.max_export = max(self.max_export, end - start)

                update_job(job, 1)

            if type in self.sidecar_paths.keys():
                self.sidecar_paths[type].append(
                    [
                        data_relative(fbx_path),
                        data_relative(json_path),
                        data_relative(gr2_path),
                        perm,
                    ]
                )
            else:
                self.sidecar_paths[type] = [
                    [
                        data_relative(fbx_path),
                        data_relative(json_path),
                        data_relative(gr2_path),
                        perm,
                    ]
                ]

    def export_bsp(
        self,
        context,
        asset_path,
        asset,
        obs_bsps,
        type,
        objects,
        obs_perms,
        sel_perms,
        sel_bsps,
        fbx_exporter,
        global_scale,
        use_mesh_modifiers,
        mesh_smooth_type,
        use_triangles,
        use_armature_deform_only,
        mesh_smooth_type_better,
        sidecar_type,
        nwo_scene,
    ):
        if sel_bsps:
            bsps = [b for b in obs_bsps if b in sel_bsps]
        else:
            bsps = obs_bsps

        for bsp in bsps:
            if sel_perms:
                perms = [p for p in obs_perms if p in sel_perms]
            else:
                perms = obs_perms

            for perm in perms:
                fbx_path, json_path, gr2_path = self.get_path(
                    asset_path, asset, type, perm, bsp, None
                )
                export_obs = [
                    ob
                    for ob in objects
                    if ob.nwo.permutation_name == perm
                    and (ob.nwo.bsp_name == bsp)
                ]

                override = context.copy()
                override["selected_objects"] = export_obs

                with context.temp_override(**override):
                    if perm == "default":
                        print_text = f"{bsp} {type}"
                    else:
                        print_text = f"{bsp} {perm} {type}"

                    job = f"-- {print_text}"
                    update_job(job, 0)
                    start = time.perf_counter()
                    if self.export_fbx(
                        fbx_exporter,
                        fbx_path,
                        global_scale,
                        use_mesh_modifiers,
                        mesh_smooth_type,
                        use_triangles,
                        use_armature_deform_only,
                        mesh_smooth_type_better,
                    ):
                        if self.export_json(
                            json_path,
                            export_obs,
                            sidecar_type,
                            asset,
                            nwo_scene,
                        ):
                            self.gr2_processes.append(
                                self.export_gr2(fbx_path, json_path, gr2_path)
                            )
                        else:
                            return f"Failed to export {perm} {type} model JSON: {json_path}"
                    else:
                        return f"Failed to export {perm} {type} model FBX: {fbx_path}"

                    end = time.perf_counter()
                    self.max_export = max(self.max_export, end - start)
                    update_job(job, 1)

                if type == "design":

                    if bsp in self.sidecar_paths_design.keys():
                        self.sidecar_paths[bsp].append(
                            [
                                data_relative(fbx_path),
                                data_relative(json_path),
                                data_relative(gr2_path),
                                perm,
                            ]
                        )
                    else:
                        self.sidecar_paths_design[bsp] = [
                            [
                                data_relative(fbx_path),
                                data_relative(json_path),
                                data_relative(gr2_path),
                                perm,
                            ]
                        ]
                else:
                    if bsp in self.sidecar_paths.keys():
                        self.sidecar_paths[bsp].append(
                            [
                                data_relative(fbx_path),
                                data_relative(json_path),
                                data_relative(gr2_path),
                                perm,
                            ]
                        )
                    else:
                        self.sidecar_paths[bsp] = [
                            [
                                data_relative(fbx_path),
                                data_relative(json_path),
                                data_relative(gr2_path),
                                perm,
                            ]
                        ]

    def get_path(
        self, asset_path, asset_name, tag_type, perm="", bsp="", animation=""
    ):
        """Gets an appropriate new path for the exported fbx file"""
        if bsp:
            if tag_type == "design":
                if perm == "default":
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{bsp}_design'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{bsp}_design'
                else:
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{bsp}_{perm}_design'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{bsp}_{perm}_design'
            else:
                if perm == "default":
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{bsp}'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{bsp}'
                else:
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{bsp}_{perm}'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{bsp}_{perm}'
        else:
            if tag_type == "animations":
                path = os.path.join(
                    asset_path, "animations", dot_partition(animation)
                )
                path_gr2 = os.path.join(
                    asset_path,
                    "export",
                    "animations",
                    dot_partition(animation),
                )

            elif tag_type in (
                "render",
                "collision",
                "physics",
                "markers",
                "skeleton",
                "sky",
                "decorator",
            ):
                if perm == "default" or tag_type in ("markers", "skeleton"):
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{tag_type}'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{tag_type}'
                else:
                    path = f'{os.path.join(asset_path, "models", asset_name)}_{perm}_{tag_type}'
                    path_gr2 = f'{os.path.join(asset_path, "export", "models", asset_name)}_{perm}_{tag_type}'

            else:
                path = os.path.join(asset_path, "models", asset_name)
                path_gr2 = os.path.join(
                    asset_path, "export", "models", asset_name
                )

        return f"{path}.fbx", f"{path}.json", f"{path_gr2}.gr2"

    def remove_all_but_armature(self, nwo_scene):
        self.skeleton_only = True
        bpy.ops.object.select_all(action='SELECT')
        nwo_scene.model_armature.select_set(False)
        bpy.ops.object.delete()

    #####################################################################################
    #####################################################################################
    # ANIMATION EVENTS

    def create_event_nodes(self, context, events, frame_start, frame_end):
        animation_events = []
        scene_coll = context.scene.collection.objects
        for event in events:
            # create the event node to store event info
            event_ob = bpy.data.objects.new("animation_event", None)
            scene_coll.link()
            nwo = event_ob.nwo
            # Set this node to be an animation event
            nwo.is_animation_event = True
            # Set up the event node with the action start and end frame and id
            nwo.frame_start = frame_start + 0.4999
            nwo.frame_end = frame_end + 0.4999
            # add the user defined properties from the action
            nwo.event_id = event.event_id
            nwo.event_type = event.event_type
            nwo.wrinkle_map_face_region = event.wrinkle_map_face_region
            nwo.wrinkle_map_effect = event.wrinkle_map_effect
            nwo.footstep_type = event.footstep_type
            nwo.footstep_effect = event.footstep_effect
            nwo.ik_chain = event.ik_chain
            nwo.ik_active_tag = event.ik_active_tag
            nwo.ik_target_tag = event.ik_target_tag
            nwo.ik_target_marker = event.ik_target_marker
            nwo.ik_target_usage = event.ik_target_usage
            nwo.ik_proxy_target_id = event.ik_proxy_target_id
            nwo.ik_pole_vector_id = event.ik_pole_vector_id
            nwo.ik_effector_id = event.ik_effector_id
            nwo.cinematic_effect_tag = event.cinematic_effect_tag
            nwo.cinematic_effect_effect = event.cinematic_effect_effect
            nwo.cinematic_effect_marker = event.cinematic_effect_marker
            nwo.object_function_name = event.object_function_name
            nwo.object_function_effect = event.object_function_effect
            nwo.frame_frame = event.frame_frame
            nwo.frame_name = event.frame_name
            nwo.frame_trigger = event.frame_trigger
            nwo.import_frame = event.import_frame
            nwo.import_name = event.import_name
            nwo.text = event.text
            # set event node name
            event_ob.name = f"event_node_{str(nwo.event_id)}"
            # add it to the list
            animation_events.append(event_ob)
            # duplicate for frame range
            if event.multi_frame == "range" and event.frame_range > 1:
                for i in range(
                    min(event.frame_range - 1, frame_end - event.frame_frame)
                ):
                    event_ob_copy = event_ob.copy()
                    scene_coll.link(event_ob_copy)
                    copy_nwo = event_ob_copy.nwo
                    copy_nwo.event_id += 1
                    copy_nwo.frame_frame += 1
                    copy_nwo.name = f"event_{str(copy_nwo.event_id)}"
                    animation_events.append(event_ob_copy)

        return animation_events

    #####################################################################################
    #####################################################################################
    # FBX

    def export_fbx(
        self,
        fbx_exporter,
        fbx_filepath,
        global_scale,
        use_mesh_modifiers,
        mesh_smooth_type,
        use_triangles,
        use_armature_deform_only,
        mesh_smooth_type_better,
    ):  # fbx_exporter
        disable_prints()

        if fbx_exporter == "better":
            bpy.ops.better_export.fbx(
                filepath=fbx_filepath,
                check_existing=False,
                my_fbx_unit="m",
                use_selection=True,
                use_visible=True,
                use_only_deform_bones=use_armature_deform_only,
                use_apply_modifiers=use_mesh_modifiers,
                use_triangulate=use_triangles,
                my_scale=global_scale,
                use_optimize_for_game_engine=False,
                use_ignore_armature_node=False,
                my_edge_smoothing=mesh_smooth_type_better,
                my_material_style="Blender",
            )
        else:
            bpy.ops.export_scene.fbx(
                filepath=fbx_filepath,
                check_existing=False,
                use_selection=True,
                use_visible=True,
                global_scale=global_scale,
                apply_scale_options="FBX_SCALE_UNITS",
                use_mesh_modifiers=use_mesh_modifiers,
                mesh_smooth_type=mesh_smooth_type,
                use_triangles=use_triangles,
                add_leaf_bones=False,
                use_armature_deform_only=use_armature_deform_only,
                bake_anim_use_all_bones=False,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                bake_anim_force_startend_keying=False,
                bake_anim_simplify_factor=0,
                axis_forward="X",
                axis_up="Z",
            )

        enable_prints()
        return os.path.exists(fbx_filepath)

    #####################################################################################
    #####################################################################################
    # JSON

    def export_json(
        self, json_path, export_obs, sidecar_type, asset_name, nwo_scene
    ):
        """Exports a json file by passing the currently selected objects to the NWOJSON class, and then writing the resulting dictionary to a .json file"""
        json_props = NWOJSON(
            export_obs,
            sidecar_type,
            asset_name,
            nwo_scene.model_armature,
            None,
            nwo_scene.skeleton_bones,
            nwo_scene.regions_dict,
            nwo_scene.global_materials_dict,
        )
        with open(json_path, "w") as j:
            json.dump(json_props.json_dict, j, indent=4)

        return os.path.exists(json_path)

    #####################################################################################
    #####################################################################################
    # GR2

    def export_gr2(self, fbx_path, json_path, gr2_path, asyncr=True):
        if self.first_gr2:
            self.first_gr2 = False
        else:
            time.sleep(0.5)

        # clear existing gr2, so we can test if export failed
        if os.path.exists(gr2_path):
            os.remove(gr2_path)
        if asyncr:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(gr2(fbx_path, json_path, gr2_path))
        else:
            return run_tool(
                [
                    "fbx-to-gr2",
                    data_relative(fbx_path),
                    data_relative(json_path),
                    data_relative(gr2_path),
                ],
                False,
                True,
            )


async def gr2(fbx_path, json_path, gr2_path):
    return run_tool(
        [
            "fbx-to-gr2",
            data_relative(fbx_path),
            data_relative(json_path),
            data_relative(gr2_path),
        ],
        True,
        True,
    )
