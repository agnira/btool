# Btool — AGENTS.md

Blender 4.2+ add-on (extension) — `blender_manifest.toml`, not legacy `bl_info`-only packaging.

## Structure

```
__init__.py     — register()/unregister() entrypoint; calls operators.register(), ui.register(), timetracker_op.register_tracker()
operators/      — one file per operator family; __init__.py exports classes tuple + register/unregister
ui.py           — panels (UI_PT_BT), sub-panels, menus, keymaps, scene property registration
utils.py        — shared helpers (rigify duplication, export option dicts, reparenting, UV reorder)
```

## Operator & naming conventions

| Element | Convention | Example |
|---|---|---|
| Operator class | `Btool_` prefix | `Btool_export` |
| bl_idname | `btool.` prefix | `btool.export` |
| Panel class | `UI_PT_` prefix | `UI_PT_BT` |
| Scene props | `b_e_` (export), `a_curve_` (animation offset) | `b_e_export_path`, `a_curve_strength` |

All operator classes registered via `operators/__init__.py`. Add new operators to the `classes` tuple there.

Time tracker is **not** in the classes tuple — registered separately via `register_tracker()/unregister_tracker()` in `__init__.py`.

## Key shortcuts

| Key | Context | Action |
|---|---|---|
| `D` | 3D Viewport | Opens `BT_MT_menu` (BNSPT) |
| `D` | Outliner (image selected) | Opens `btool.rename_images` |

Registered in `ui.py:register()` via addon keyconfig.

## UI panel

Side Panel (`N`) > Tool > BNSPT. Sub-panels: Options, Mixamo, Animation Tool.

## External add-on dependencies

- **ucupaint** — required by compile tool (`y_*` operators), rename data
- **Might Rigger** — required by Mixamo animation import (`mr.import_anim_to_rig`)

## Notable quirks

- `metarig_to_applied` checks for `"APPLIED"` in armature name (spelling intentional — "Applyed" in UI label)
- `utils.py:SKIPPED_REPARENT_BONES` — hardcoded set of ORG bones excluded from reparenting
- `utils.py:duplicate_rig()` creates a copy of a rigify rig with Copy Transforms constraints, bakes animation, removes constraints
- FBX export unpacks textures, exports, then repacks
- GLTF export applies per-collection; batch mode nests under `//gltf/<filename>/<collection>/`
- `Btool_compile` depends on ucupaint node baking; requires collections visible for render (hides non-visible ones)
- Render preview moves each object to origin temporarily, renders, restores position

## No tests, no CI, no linting/typecheck config

Pure Python addon without any test runner, CI, or code quality tooling. Only `__pycache__` in `.gitignore`.
