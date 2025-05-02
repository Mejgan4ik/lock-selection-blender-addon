# Lock Selection – Blender Addon

🔒 A Blender addon that allows you to lock mesh selection in Edit Mode and restore it when attempting to change the selection.

## 🧾 Description

This addon lets you lock your current mesh selection so that any attempt to select new elements will be ignored. You can still transform (`G`, `R`, `S`) locked selections.

The locked state is saved per-object basis, so you can have different locked selections on multiple objects.

## 🔧 Features

- [x] Lock selection with a single click or shortcut.
- [x] Restore original selection if changed.
- [x] Works separately for each object.
- [x] Supports vertex, edge and face selection modes.
- [x] Does not interfere with transformations (`G`, `R`, `S`)
- [x] UI buttons in Tool Panel and View3D Header
- [x] Shortcut: `Alt + K`
- [x] Fully compatible with Blender 4.2

## 🛠 Installation

### Option 1: Install as Extension (.zip)

1. Go to `Edit > Preferences > Extensions`
2. Click `Install From Disk...`
3. Select the `.zip` file generated from this repository.

### Option 2: Manual Install

1. Copy the `lock_selection` folder into your Blender scripts directory: Scripts/addons/
2. Enable the addon in `Edit > Preferences > Add-ons`

## 🎬 Usage

1. Enter **Edit Mode**
2. Select vertices, edges or faces
3. Press `Alt+K` to lock selection
4. Try selecting other elements → The selection will revert back
