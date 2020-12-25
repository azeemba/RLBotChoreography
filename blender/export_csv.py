import bpy
import csv

def get_transform(object):
    position, quaternion, scale = object.matrix_world.decompose()
    
    multiplier = 1.0/(sum(scale.to_tuple())/3)
    position = position * multiplier
    return [*position, *quaternion]



def write_some_data(context, filepath, use_some_setting):
    print("Exporting csv transformation")
    selected = context.selected_objects
    # sort for consistent indexing
    selected = sorted(selected, key=lambda x: x.name)
    
    end_frame = 100 # TODO: figure out last frame
    
    with open(filepath, 'w', newline='') as filehandle:
        csv_writer = csv.writer(filehandle)
        csv_writer.writerow(['name', 'frame', 'x', 'y', 'z', 'q1', 'q2', 'q3', 'q4'])
        for i in range(0, end_frame):
            context.scene.frame_set(i)
            for obj in selected:
                transform = get_transform(obj)
                csv_writer.writerow([obj.name, i] + transform)
            
    print("Finished exporting csv_transformation")
    return {'FINISHED'}

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class CSVTransformationPerFrame(Operator, ExportHelper):
    """Outputs Transformation of all selected items per frame"""
    bl_idname = "csv.transformation_per_frame"
    bl_label = "Save Transformation CSV"

    # ExportHelper mixin class uses this
    filename_ext = ".csv"

    filter_glob: StringProperty(
        default="*.csv",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return write_some_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(CSVTransformationPerFrame.bl_idname, text="Export Transformation in CSV")


def register():
    bpy.utils.register_class(CSVTransformationPerFrame)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(CSVTransformationPerFrame)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.csv.transformation_per_frame('INVOKE_DEFAULT')
