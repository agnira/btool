# Btool — Internal Banaspateam Tool

Internal workflow automation tools for [Banaspateam](https://banaspateam.com).

**Location:** Side Panel (N) > Tool > BNSPT  
**Hotkey:** `D` in 3D Viewport opens the main menu. `D` in Outliner opens the image renamer.

---

## Features

### 1. Export Tools
Menu: `export` in the BNSPT panel or D-menu.

Four export modes:
- **fbx** — Exports selected objects as FBX into `//fbx/<collection>/<collection>.fbx`. Unpacks textures before export, repacks after.
- **fbx combine** — Exports the entire blend file as a single FBX into `//fbx/<filename>.fbx`.
- **gltf** — Exports selected objects as GLB into `//gltf/<collection>.glb`. Respects the Options panel settings (see below).
- **gltf batch** — Exports each collection as a separate GLB into `//gltf/<filename>/<collection>/`.

#### Options (sub-panel)
| Property | Description |
|---|---|
| export path | Custom directory for GLTF export (overrides default `//gltf/`) |
| export use vcol | (reserved) |
| export flatten hierarchy | Flattens bone hierarchy in GLTF export |
| stepping interpolation | Uses stepped (constant) keyframe interpolation on baked animations |

### 2. Batch Rename Data
Renames object data-blocks, materials, and ucupaint node trees to match the object name.

**Usage:**
1. Select objects in the 3D Viewport
2. Click `Rename Data` in the BNSPT panel, or use the D-menu > Rename Data

Each selected object will have:
- Its data-block (`mesh`, `armature`, etc.) renamed to the object name
- Its active material renamed to the object name (if any)
- Its ucupaint node tree renamed (if ucupaint addon is available)

### 3. Render Preview
Renders individual preview images of each selected object in isolation.

**Usage:**
1. Select objects in the 3D Viewport
2. Click `Render Preview`
3. Each object is rendered one at a time with all other meshes hidden
4. Output: `//preview/<object_name>.png`

### 4. Rigify Tools

#### Metarig To Applyed Rig
Snaps metarig bone positions to match an applied (DEF) rig.

**Usage:**
1. Select an applied rig armature (name must contain "APPLIED")
2. Click the operator
3. Choose the metarig armature from the search popup
4. All metarig bones (except heels) are snapped to their DEF-bone counterparts

#### Reparent Separated Bone (rigify)
Reparents DEF bones under their ORG counterparts in a rigify armature. Adds Copy Transforms constraints where needed.

**Usage:**
1. Select a rigify armature
2. Click the operator

#### Set Rigify Bones Type
Sets selected pose bones to `basic.super_copy` rigify type with `bone` widget.

**Usage:**
1. Select a rigify armature and enter Pose mode
2. Select the bones to configure
3. Click the operator

### 5. Bones From Vertices
Generates an armature with one bone per selected mesh vertex, pointing along the vertex normal direction.

**Usage:**
1. In Edit mode on a mesh, select vertices
2. Click `Bones From Vertices`
3. Set the bone length in the dialog
4. A new armature is created with bones at each vertex position

### 6. Mixamo Animation Importer
Imports multiple Mixamo FBX animations and transfers them to the target rig using the `mr.import_anim_to_rig` operator.

**Usage:**
1. Select the target armature
2. Click `Import mixamo Animations`
3. Select one or more FBX files in the file browser
4. Each animation is imported, transferred, and the source is cleaned up

### 7. FBX Animation Importer
Imports FBX animation onto the active armature directly.

**Usage:**
1. Select the target armature
2. Click `Import fbx Animations`
3. Select one or more FBX files
4. Each animation is imported and named after the source file

### 8. Compile Tool
Collects all visible renderable collections, combines them into single meshes, bakes ucupaint textures, and removes vertex groups (optional).

**Usage:**
1. Hide all collections you don't want to compile (render visibility)
2. Click `Compile`
3. A new `COMPILED` collection is created with the baked results

### 9. Curve Offset Tool (Animation Tool sub-panel)
Adjusts animation curve offset parameters on selected pose bones.

**Usage:**
1. Select an armature and enter Pose mode
2. Select pose bones
3. In the `Animation Tool` sub-panel, adjust strength, rotation (w/x/y/z), and position (x/y/z) offsets

### 10. Image Batch Renamer (Outliner)
Renames selected image datablocks from the Outliner.

**Usage:**
1. Open the Outliner, switch to Blender File or Data API view mode
2. Select one or more image datablocks
3. Press `D` to open the rename dialog

Two modes:
- **Replace All** — Rename all selected images to a base name. Optionally add `_001`, `_002`, … numbering.
- **Find & Replace** — Find text in image names and replace it.

---

## Shortcuts

| Key | Context | Action |
|---|---|---|
| `D` | 3D Viewport | Opens BNSPT main menu |
| `D` | Outliner (with image(s) selected) | Opens Image Batch Renamer |
