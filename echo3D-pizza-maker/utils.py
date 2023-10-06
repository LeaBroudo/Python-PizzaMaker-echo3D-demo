from model_constants import MODELS
from panda3d.core import LPoint3
import sys
import shutil

"""""""""""""""""""""
# Helper Functions #
"""""""""""""""""""""

"""
Given a line (vector plus origin point) and a desired z value, this function
will give us the point on the line where the desired z value is what we want.
This is how we know where to position an object in 3D space based on a 2D mouse
position. It also assumes that we are dragging in the XY plane.
"""
def PointAtZ(z, point, vec):
    return point + vec * ((z - point.getZ()) / vec.getZ())

"""
Handy function for getting the proper position for a given square
"""
def SquarePos(i):
    # last 4 squares correspond to each topping plate, 
    # and not the empty pizza
    if (i >= 64):
        return LPoint3(-8+((i%64)*5),8,0)
    return LPoint3((i % 8) - 3.5, int(i // 8) - 3.5, 0)
    
"""
This will exit the game and delete 
models retrieved from echo3D
"""
def ExitGame():
    shutil.rmtree('./downloads')
    sys.exit()

"""
Returns the path to an asset retrieved from echo3D
"""
def getModelFilePath(modelName):
    return "downloads/"+MODELS[modelName]+"/"+modelName
        
