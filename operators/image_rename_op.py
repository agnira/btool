import bpy
from bpy import types
from bpy.props import EnumProperty, StringProperty, BoolProperty, IntProperty


class Btool_rename_images(bpy.types.Operator):
    bl_idname = "btool.rename_images"
    bl_label = "Rename Images"
    bl_description = "Rename selected image datablocks from the Outliner"

    mode: EnumProperty(
        name="Mode",
        items=[
            ("REPLACE_ALL", "Replace All", "Replace all names with a base name"),
            ("FIND_REPLACE", "Find & Replace", "Find and replace text in names"),
        ],
        default="REPLACE_ALL",
    )

    base_name: StringProperty(name="Base Name", default="texture")
    use_numbering: BoolProperty(name="Add _001 Numbering", default=True)
    start_number: IntProperty(name="Start Number", default=1, min=0)

    find_text: StringProperty(name="Find")
    replace_text: StringProperty(name="Replace")

    @classmethod
    def poll(cls, context):
        return any(isinstance(id, bpy.types.Image) for id in context.selected_ids)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mode")
        layout.separator()
        if self.mode == "REPLACE_ALL":
            layout.prop(self, "base_name")
            layout.prop(self, "use_numbering")
            if self.use_numbering:
                layout.prop(self, "start_number")
        else:
            layout.prop(self, "find_text")
            layout.prop(self, "replace_text")

    def execute(self, context):
        images = [
            id for id in context.selected_ids if isinstance(id, bpy.types.Image)
        ]
        if not images:
            self.report({"WARNING"}, "No images selected")
            return {"CANCELLED"}

        if self.mode == "REPLACE_ALL":
            if self.use_numbering:
                count = len(images)
                digits = max(3, len(str(count)))
                for i, img in enumerate(images, self.start_number):
                    img.name = f"{self.base_name}_{i:0{digits}d}"
            else:
                for img in images:
                    img.name = self.base_name
        else:
            for img in images:
                if self.find_text in img.name:
                    img.name = img.name.replace(self.find_text, self.replace_text)

        return {"FINISHED"}
