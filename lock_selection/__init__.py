bl_info = {
    "name": "Lock Selection",
    "author": "Krasnoselskiy Vladimir",
    "version": (1, 14),
    "blender": (4, 2, 0),
    "location": "View3D > Tool Panel & Header",
    "description": "Locks selection changes for each object individually",
    "warning": "",
    "doc_url": "",
    "category": "3D View"
}

import bpy
import bmesh

# --- Global variables ---
lock_selection_per_object = {}  # { obj_name : {verts, edges, faces, enabled} }
processing = False  # Recursion protection

# --- Utilities ---

def save_initial_selection(context):
    obj = context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return

    bm = bmesh.from_edit_mesh(obj.data)
    lock_selection_per_object[obj.name] = {
        "verts": [v.index for v in bm.verts if v.select],
        "edges": [e.index for e in bm.edges if e.select],
        "faces": [f.index for f in bm.faces if f.select],
        "enabled": True,
        "initial_selection_saved": True
    }

def restore_locked_selection(context):
    global processing

    if processing:
        return

    try:
        processing = True

        obj = context.active_object
        if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
            return

        bm = bmesh.from_edit_mesh(obj.data)
        data = lock_selection_per_object.get(obj.name)
        if not data:
            return

        # Clear current selection
        bpy.ops.mesh.select_all(action='DESELECT')

        tool_settings = context.tool_settings

        # Restore based on current mode
        if tool_settings.mesh_select_mode[0]:  # Vertex
            for v in bm.verts:
                if v.index in data["verts"]:
                    v.select_set(True)
            for e in bm.edges:
                if e.index in data["edges"]:
                    e.select_set(True)
            for f in bm.faces:
                if f.index in data["faces"]:
                    f.select_set(True)

        if tool_settings.mesh_select_mode[1]:  # Edge
            for e in bm.edges:
                if e.index in data["edges"]:
                    e.select_set(True)
            for f in bm.faces:
                if f.index in data["faces"]:
                    f.select_set(True)

        if tool_settings.mesh_select_mode[2]:  # Face
            for f in bm.faces:
                if f.index in data["faces"]:
                    f.select_set(True)

        bmesh.update_edit_mesh(obj.data)
        context.area.tag_redraw()

    finally:
        processing = False

# --- Hook for monitoring selection changes ---

@bpy.app.handlers.persistent
def on_depsgraph_update(dummy):
    global processing

    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return

    data = lock_selection_per_object.get(obj.name)
    if not data or not data["enabled"] or not data["initial_selection_saved"]:
        return

    bm = bmesh.from_edit_mesh(obj.data)

    current_vert_sel = {v.index for v in bm.verts if v.select}
    current_edge_sel = {e.index for e in bm.edges if e.select}
    current_face_sel = {f.index for f in bm.faces if f.select}

    saved_vert_sel = set(data["verts"])
    saved_edge_sel = set(data["edges"])
    saved_face_sel = set(data["faces"])

    if (current_vert_sel != saved_vert_sel or
        current_edge_sel != saved_edge_sel or
        current_face_sel != saved_face_sel):

        restore_locked_selection(bpy.context)

# --- Operator Alt+K ---

class VIEW3D_OT_lock_selection_toggle(bpy.types.Operator):
    bl_idname = "view3d.lock_selection_toggle"
    bl_label = "Toggle Lock Selection"
    bl_description = "Locks the current selection and restores it when changed for each object separately"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        obj = context.active_object
        if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Works only in Edit Mode")
            return {'CANCELLED'}

        name = obj.name
        if name in lock_selection_per_object and lock_selection_per_object[name]["enabled"]:
            # Disable lock
            lock_selection_per_object[name]["enabled"] = False
        else:
            # Enable and save selection
            save_initial_selection(context)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

# --- Panel in Tool Sidebar ---

class VIEW3D_PT_lock_selection_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_label = 'Lock Selection'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
            sub = layout.column(align=True)
            sub.label(text="Only works in Edit Mode")
            return

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.5
        props = row.operator("view3d.lock_selection_toggle", text="Lock/Unlock", icon='DECORATE_LOCKED')
        row.prop(context.scene, "lock_selection_state_prop", text="", toggle=True)

        sub = layout.column(align=True)
        sub.enabled = False
        sub.label(text="Current state:")

        name = obj.name
        if name in lock_selection_per_object and lock_selection_per_object[name]["enabled"]:
            sub.label(text=f"Selection is locked for '{name}'", icon='CHECKMARK')
        else:
            sub.label(text="No active selection lock", icon='BLANK1')

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Hotkey: Alt + K")

# --- Button in the header ---

def draw_header_button(self, context):
    layout = self.layout
    obj = context.active_object
    if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
        row = layout.row(align=True)
        row.operator("view3d.lock_selection_toggle", text="", icon='DECORATE_LOCKED', depress=obj.name in lock_selection_per_object and lock_selection_per_object[obj.name].get("enabled", False))

# --- Property to reflect lock state in UI ---

def get_lock_state(self):
    obj = bpy.context.active_object
    if obj and obj.name in lock_selection_per_object:
        return lock_selection_per_object[obj.name]["enabled"]
    return False

bpy.types.Scene.lock_selection_state_prop = bpy.props.BoolProperty(
    name="Lock Selection",
    description="Only for displaying the lock state",
    get=get_lock_state
)

class VIEW3D_PT_lock_selection_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="The Lock selection addon is located in the sidebar in the Tool panel.")
        layout.label(text="By default, the Alt+K shortcut is assigned.")
        layout.label(text="There is also a button in the header of the 3D view window.")

        layout.separator()

        box = layout.box()
        box.label(text="Usage Instructions:")
        box.label(text="1. Enter Edit Mode and select mesh elements.")
        box.label(text="2. Press Alt+K to lock selection.")
        box.label(text="3. Any new selection will be blocked.")

# --- Registration ---

addon_keymaps = []

def register():
    bpy.utils.register_class(VIEW3D_OT_lock_selection_toggle)
    bpy.utils.register_class(VIEW3D_PT_lock_selection_panel)
    bpy.utils.register_class(VIEW3D_PT_lock_selection_addon_prefs)

    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    bpy.types.VIEW3D_HT_header.append(draw_header_button)

    # Hotkey Alt+K
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("view3d.lock_selection_toggle", 'K', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi))

def unregister():
    global lock_selection_per_object

    bpy.utils.unregister_class(VIEW3D_OT_lock_selection_toggle)
    bpy.utils.unregister_class(VIEW3d_PT_lock_selection_panel)
    bpy.utils.unregister_class(VIEW3D_PT_lock_selection_addon_prefs)

    bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)

    # Remove keymap entry
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    del bpy.types.Scene.lock_selection_state_prop
    lock_selection_per_object.clear()

if __name__ == "__main__":
    register()