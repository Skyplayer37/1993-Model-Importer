import bpy
from bpy_extras.io_utils import ImportHelper 
from bpy.types import Operator
import bmesh

bl_info = {
    "name": "Import 1993 3D",
    "description": "Imports 3D models found on a 1993 shareware disc into Blender.",
    "author": "Skyplayer",
    "version": (1, 0),
    #"blender": (3, 3, 0),
    "blender": (2, 80, 0),
    "location": "Import > 1993-3D",
    "warning": "", # used for warning icon and text in addons panel
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


############ Grease Pencil Code https://towardsdatascience.com/blender-2-8-grease-pencil-scripting-and-generative-art-cbbfd3967590 ######################
def get_grease_pencil(gpencil_obj_name='GPencil') -> bpy.types.GreasePencil:
    """
    Return the grease-pencil object with the given name. Initialize one if not already present.
    :param gpencil_obj_name: name/key of the grease pencil object in the scene
    """

    # If not present already, create grease pencil object
    if gpencil_obj_name not in bpy.context.scene.objects:
        bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), type='EMPTY')
        # rename grease pencil
        bpy.context.scene.objects[-1].name = gpencil_obj_name

    # Get grease pencil object
    gpencil = bpy.context.scene.objects[gpencil_obj_name]

    return gpencil


def get_grease_pencil_layer(gpencil: bpy.types.GreasePencil, gpencil_layer_name='GP_Layer',
                            clear_layer=False) -> bpy.types.GPencilLayer:
    """
    Return the grease-pencil layer with the given name. Create one if not already present.
    :param gpencil: grease-pencil object for the layer data
    :param gpencil_layer_name: name/key of the grease pencil layer
    :param clear_layer: whether to clear all previous layer data
    """

    # Get grease pencil layer or create one if none exists
    if gpencil.data.layers and gpencil_layer_name in gpencil.data.layers:
        gpencil_layer = gpencil.data.layers[gpencil_layer_name]
    else:
        gpencil_layer = gpencil.data.layers.new(gpencil_layer_name, set_active=True)

    if clear_layer:
        gpencil_layer.clear()  # clear all previous layer data

    # bpy.ops.gpencil.paintmode_toggle()  # need to trigger otherwise there is no frame

    return gpencil_layer


# Util for default behavior merging previous two methods
def init_grease_pencil(gpencil_obj_name='GPencil', gpencil_layer_name='GP_Layer',
                       clear_layer=True) -> bpy.types.GPencilLayer:
    gpencil = get_grease_pencil(gpencil_obj_name)
    gpencil_layer = get_grease_pencil_layer(gpencil, gpencil_layer_name, clear_layer=clear_layer)
    return gpencil_layer

#grease pencil, lets see if we can approximate the original color
def draw_line(gp_frame, p0: tuple, p1: tuple,color:int):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    
    gp_stroke.material_index = int(color)
    gp_stroke.line_width = 750
    
    print(colors)
    if colorCheck(color) == True:
        print("adding a new material")
        ob = bpy.context.active_object  # Must be a GPencil object
        print(ob)
        mat = bpy.data.materials.new(name=color)
        bpy.data.materials.create_gpencil_data(mat)
        ob.data.materials.append(mat)
    # Define stroke geometry
    
    gp_stroke.points.add(count=2)
    gp_stroke.points[0].co = p0
    gp_stroke.points[1].co = p1
    return gp_stroke
############################################################################################


colors = [0]

#do we already have this color recorded?
def colorCheck(c):
    if colors.count(c) == 0:
        #if not, create a new material slot for it
        colors.append(c)
        return True
    else: 
        return False

def import_1993(path):
    name = path.split('\\')[-1].split('/')[-1]
    mesh = bpy.data.meshes.new( name ) # create a new mesh
    # parse the file
    file = open(path, 'r')

    linenum = 0
    pointsamount = 0
    connectamount = 0
    #x,y,z pos
    vertices = [[0,0,0]]
    #vert 1, vert 2, color
    edges = [[0,0,0]]
    
    
    lastvert = 0
    
    gp_layer = init_grease_pencil()
    gp_frame = gp_layer.frames.new(0)

    for line in file:
            linenum += 1
            words = line.split()
            #do we have anything at all?
            if len(words) == 0 or words[0].startswith('#'):
                pass
            else:
                #alright, where are we?
                if linenum == 1:
                    #the first value is the number of verts in the model
                    pointsamount = float(words[0])
                elif int(linenum) < pointsamount + 2:
                        #then are the new verts themselves
                        x, y, z = float(words[0]), float(words[1]), float(words[2])
                        vertices.append((x, y, z))
                elif int(linenum) == pointsamount + 2:
                    #then the amount of edges
                    connectamount = int(words[0])
                elif int(linenum) > pointsamount + 2:
                    #then the edges
                    #the format gives two values here: first a vertice index, then a color
                    #each vertice is either a draw or a move from the last
                    #if theres any color, its drawn. if color is 0, its just a move
                    #like a dot-to-dot, on 0 you lift your pencil
                    if words[1] == 0:
                        lastvert = 0
                        pass
                    else:
                        x = lastvert
                        y = words[0]
                        edges.append((x,y,words[1]))
                        lastvert = y
                        
                        
#create a Bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
#assign the verts
    for newvert in vertices:
        bm.verts.new(newvert)
#assign the edges
#draws from x to y
    for newedge in edges:
        x = int(newedge[0])
        y = int(newedge[1])
        #check if the color is new
        colorCheck(int(newedge[2]))
        
        #time to draw the edge!
        bm.verts.ensure_lookup_table()
        if x != y:
            try:
                bm.edges.new((bm.verts[x],bm.verts[y]))
                #grease pencil
                draw_line(gp_frame, vertices[x],vertices[y],newedge[2])
            except ValueError:
                print("skipping redundant")
                
    #fill in the faces to the best of our abilities      
    #bmesh.ops.holes_fill(bm, edges, sides)
#update the mesh, delete the bmesh        
    bm.to_mesh(mesh)
    bm.free()
#add it to the scene via an object in a collection
    new_object = bpy.data.objects.new(name, mesh)
    new_collection = bpy.data.collections.new('new_collection')
    bpy.context.scene.collection.children.link(new_collection)

    new_collection.objects.link(new_object)

#snippet that runs the file browser on use to get the model
class OT_TestOpenFilebrowser(Operator, ImportHelper):
    bl_idname = "test.open_filebrowser"
    bl_label = "Open the file browser (yay)"
    def execute(self, context):
        import_1993(self.filepath)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OT_TestOpenFilebrowser)
def unregister():
    bpy.utils.unregister_class(OT_TestOpenFilebrowser)
    
#running the script manually (not as an addon) calls this
if __name__ == "__main__":
    register()
    # test call 
    bpy.ops.test.open_filebrowser('INVOKE_DEFAULT')