#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import AmbientLight, DirectionalLight, LightAttrib
from panda3d.core import TextNode
from panda3d.core import LPoint3, LVector3, BitMask32
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from echo3d_api import *
from utils import *
import argparse
import random

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#  This tutorial shows how to retrieve 3D models from echo3D  #
#  using Python, and load them into a Panda3d game. 
#  
#  
#  
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class PizzaDemo(ShowBase):
    
    """
    Game initialization
    """
    def __init__(self, api_key, security_key):
        # Creates a window and sets up everything we need for rendering into it.
        ShowBase.__init__(self)

        self.accept('escape', ExitGame)
        self.loadUI()
        self.disableMouse()  # Disble mouse camera control
        camera.setPosHpr(0, -20, 18, 0, -40, 0)  # Set the camera
        self.setupLights()  # Setup default lighting
        self.setUpCollisionDetection()
        
        self.taskMgr.add(self.retrieveModelsFromEcho3D(api_key, security_key))

    """
    Adds the title and instruction text on screen
    """
    def loadUI(self):
        self.title = OnscreenText(text="Echo3D Python Tutorial - Pizza Maker",
                                  style=1, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
                                  pos=(0, 0.90), scale = .07)
        self.loadingText = OnscreenText(text="",
                                    style=1, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), 
                                    pos=(0, 0), scale = .07)
        self.escapeEvent = OnscreenText(text="ESC: Quit", parent=base.a2dTopLeft,
                                        style=1, fg=(1, 1, 1, 1), pos=(0.06, -1.95),
                                        align=TextNode.ALeft, scale = .05)
        self.mouse1Event = OnscreenText(text="It's pizza time! Pick up and drag toppings anywhere onto or off your pizza.",
                                        style=1, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
                                        pos=(0, 0.80), scale = .05)

    """
    Create areas with collision detection that enable 
    users to pick up and move toppings around the pizza.
    """
    def setUpCollisionDetection(self):
        self.picker = CollisionTraverser() 
        self.pq = CollisionHandlerQueue() 
        # Make a collision node for our picker ray
        self.pickerNode = CollisionNode('mouseRay')
        # Attach that node to the camera since the ray will need to be positioned
        # relative to it
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        # Everything to be picked will use bit 1. This way if we were doing other
        # collision we could separate it
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        # Add it to the collision node
        self.pickerNode.addSolid(self.pickerRay)
        # Register the ray as something that can cause collisions
        self.picker.addCollider(self.pickerNP, self.pq)
        self.picker.showCollisions(render)

    """
    Retrieve 3D models from echo3D, show loading progress throughout,
    and initialize game environment on completion. 
    """
    async def retrieveModelsFromEcho3D(self, apiKey, securityKey):
        api = Echo3DAPI(api_key=apiKey, security_key=securityKey)

        # Iterate through constants and 
        # retrieve asset from echo3D
        for model in MODELS:
            await self.updateLoadingText(model)
            api.retrieve(MODELS[model])

        self.loadingText.destroy()
        self.initializePizzaMakingEnvironment()
            
        return 0

    """
    Position echo3D models into the correct locations for the ideal pizza making experience
    """      
    def initializePizzaMakingEnvironment(self):

        # Keeps track of locations a topping can be placed
        self.squares = [None for i in range(68)]
        # Keeps track of where each topping has been placed
        self.toppings = [None for i in range(64)]

        # For each of the 4 plates (a,b,c,d) with extra pizza toppings, 
        # we create a variable to help keep track of how many 
        # toppings have been used from each plate. 
        self.PLATE_A_IDX = 64
        self.PLATE_B_IDX = 84
        self.PLATE_C_IDX = 104
        self.PLATE_D_IDX = 124
        
        self.loadEnvironmentModels()
        self.loadSquaresForCollisions()

        # Start the task that handles grabbing and releasing toppings
        self.mouseTask = taskMgr.add(self.mouseTask, 'mouseTask')
        self.accept("mouse1", self.grabTopping)  # left-click grabs a topping
        self.accept("mouse1-up", self.releaseTopping)  # releasing places it
    
    """
    Set up the environment including skybox, empty pizza, and plates for extra toppings
    """
    def loadEnvironmentModels(self):
        # Now we create the pizza board and its toppings
        self.environment = render.attachNewNode("environment")
        self.skybox = loader.loadModel(getModelFilePath("Skybox.glb")) 
        self.skybox.reparentTo(self.environment)
        self.skybox.setHpr(20)

        self.plate = loader.loadModel(getModelFilePath("plate.obj"))
        self.plate.reparentTo(self.environment)
        self.plate.setPos(LPoint3(0,0,-1.4))
        self.plate.setScale(14)
        self.plate.setHpr(0,90,0)

        self.pizza = loader.loadModel(getModelFilePath("emptyPizza.obj"))
        self.pizza.reparentTo(self.environment)
        self.pizza.setPos(LPoint3(-4.5,2.3,-0.44))
        self.pizza.setScale(0.45)

        self.mushroomPlate = None
        self.pepperoniPlate = None
        self.broccoliPlate = None
        self.pepperPlate = None

        self.createToppingPlate(self.mushroomPlate, SquarePos(64), Mushroom)
        self.createToppingPlate(self.pepperoniPlate, SquarePos(65), Pepperoni)
        self.createToppingPlate(self.broccoliPlate, SquarePos(66), Broccoli)
        self.createToppingPlate(self.pepperPlate, SquarePos(67), Pepper)

    """
    Create a plate with extra pizza toppings
    """
    def createToppingPlate(self, plate, pos, ToppingClass,):
        plate = loader.loadModel(getModelFilePath("plate.obj"))
        plate.reparentTo(self.environment)
        plate.setPos(pos+LPoint3(0,0,-0.21))
        plate.setScale(5)
        plate.setHpr(0,90,0)

        newToppings = [None for i in range(20)]
        
        for i in range(10):
            rnd = random.uniform(-1, 1)
            newToppings[i] = ToppingClass(i)
            newToppings[i].obj.setPos(LPoint3(pos.x+rnd, pos.y+rnd, pos.z))

        self.toppings.extend(newToppings)

    """
    Position collideable squares onto the empty pizza 
    and each of the four extra topping plates
    """
    def loadSquaresForCollisions(self):
        # By attaching all of the squares to their own root, we can do the collision pass
        # just on the squares and save the time of checking the rest of the scene
        self.squareRoot = render.attachNewNode("squareRoot")
        # This will represent the index of the currently highlited square
        self.hiSq = False
        # This wil represent the index of the square where currently dragged topping
        # was grabbed from
        self.dragging = False
            
        # Iterate through a range to position squares
        # Between 0 and 64 handles squares on the empty pizza
        # Between 64 and 68 handles squares for each of the four topping plates
        for i in range(68):
            # Position squares into the shape of 
            # a circle by skipping certain locations
            arr = [0,1,6,7,8,15]
            shouldSkipLocation = False
            for j in arr:
                if (j == i or 63-j == i):
                    shouldSkipLocation = True
            
            if (shouldSkipLocation):
                continue

            # Load, parent, and position the model (a single square polygon)
            self.squares[i] = loader.loadModel("./square")
            self.squares[i].reparentTo(self.squareRoot)
            self.squares[i].setPos(SquarePos(i))
            # Set the model itself to be collideable with the ray. 
            self.squares[i].find("**/polygon").node().setIntoCollideMask(
                BitMask32.bit(1))
            # Set a tag on the square's node so we can look up what square this is
            # later during the collision pass
            self.squares[i].find("**/polygon").node().setTag('square', str(i))

            # Add a random topping to the given pizza square
            if i < 64: 
                rnd = random.randint(0,6)
                if (rnd == 0):
                    self.toppings[i] = Broccoli(i)
                elif (rnd == 1):
                    self.toppings[i] = Pepperoni(i)
                elif (rnd == 2):
                    self.toppings[i] = Mushroom(i)
                elif (rnd == 3):
                    self.toppings[i] = Pepper(i)

    """
    Swap the position of two toppings
    """
    def swapToppings(self, fr, to, hiSq):
        temp = self.toppings[fr]
        self.toppings[fr] = self.toppings[to]
        self.toppings[to] = temp
        if self.toppings[fr]:
            self.toppings[fr].square = fr
            self.toppings[fr].obj.setPos(SquarePos(fr))
        if self.toppings[to]:
            self.toppings[to].square = hiSq
            self.toppings[to].obj.setPos(SquarePos(hiSq))

    """
    Handle dragging toppings and collisions with squares
    """
    def mouseTask(self, task):

        # Check to see if we can access the mouse. We need it to do anything else
        if self.mouseWatcherNode.hasMouse():
            # get the mouse position
            mpos = self.mouseWatcherNode.getMouse()

            # Set the position of the ray based on the mouse position
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())

            # If we are dragging something, set the position of the object
            # to be at the appropriate point over the plane of the board
            if self.dragging is not False:
                # Gets the point described by pickerRay.getOrigin(), which is relative to
                # camera, relative instead to render
                nearPoint = render.getRelativePoint(camera, self.pickerRay.getOrigin())
                # Same thing with the direction of the ray
                nearVec = render.getRelativeVector(camera, self.pickerRay.getDirection())
                self.toppings[self.dragging].obj.setPos(PointAtZ(.5, nearPoint, nearVec))

            # Do the actual collision pass 
            self.picker.traverse(self.squareRoot)
            if self.pq.getNumEntries() > 0:
                # if we have hit something, sort the hits so that the closest is first
                self.pq.sortEntries()
                i = int(self.pq.getEntry(0).getIntoNode().getTag('square'))
                self.hiSq = i

        return Task.cont
    
    """
    Update the UI as models load
    """
    async def updateLoadingText(self, model):
        # Update loading text and pause the task to trigger rerender
        self.loadingText.setText("Loading...\nRetrieving "+model+" from echo3D.\n")
        await Task.pause(0.1) 

    """ 
    Handle picking up a topping
    """
    def grabTopping(self):
        # If a square is highlighted and it has a topping, set it to dragging mode
        if (self.hiSq is False):
            return
        
        # Given the index of a square,
        # get the corresponding topping index
        toppingIdx = -1
        if (self.hiSq >= 64):
            if (self.hiSq == 64):
                toppingIdx = self.PLATE_A_IDX
                self.PLATE_A_IDX = self.PLATE_A_IDX + 1
            if (self.hiSq == 65):
                toppingIdx = self.PLATE_B_IDX
                self.PLATE_B_IDX = self.PLATE_B_IDX + 1
            if (self.hiSq == 66):
                toppingIdx = self.PLATE_C_IDX
                self.PLATE_C_IDX = self.PLATE_C_IDX + 1
            if (self.hiSq == 67):
                toppingIdx = self.PLATE_D_IDX
                self.PLATE_D_IDX = self.PLATE_D_IDX + 1
        else:
            toppingIdx = self.hiSq

        # Set the topping to be dragging and 
        # record its current square
        if self.toppings[toppingIdx]:
            self.dragging = toppingIdx
            self.hiSq = False

    """
    Handle releasing a topping
    """
    def releaseTopping(self):
        # If we are not on a square, return it to its original
        # position. Otherwise, swap it with the topping in the new square
        # Make sure we really are dragging something
        if self.dragging is not False:
            # We have let go of the topping, but we are not on a square
            if self.hiSq is False:
                self.toppings[self.dragging].obj.setPos(
                    SquarePos(self.dragging))
            else:
                # Given the index of a square,
                # get the corresponding topping index
                toppingIdx = -1
                if (self.hiSq >= 64):
                    if (self.hiSq == 64):
                        self.PLATE_A_IDX = self.PLATE_A_IDX - 1
                        toppingIdx = self.PLATE_A_IDX
                    if (self.hiSq == 65):
                        self.PLATE_B_IDX = self.PLATE_B_IDX - 1
                        toppingIdx = self.PLATE_B_IDX
                    if (self.hiSq == 66):
                        self.PLATE_C_IDX = self.PLATE_C_IDX - 1
                        toppingIdx = self.PLATE_C_IDX
                    if (self.hiSq == 67):
                        self.PLATE_D_IDX = self.PLATE_D_IDX - 1
                        toppingIdx = self.PLATE_D_IDX
                else:
                    toppingIdx = self.hiSq

                # Otherwise, swap the toppings
                self.swapToppings(self.dragging, toppingIdx, self.hiSq)

        # We are no longer dragging anything
        self.dragging = False

    """
    Position lights around the scene
    """
    def setupLights(self):  
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.3, .25, .25, .3))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 8, -2.5))
        directionalLight.setColor((0.9, 0.8, 0.9, 1))
        render.setLight(render.attachNewNode(directionalLight))
        render.setLight(render.attachNewNode(ambientLight))


""""""""""""
# Classes #
""""""""""""
"""
Class for a topping. This just handles loading the model and setting initial position
"""
class Topping(object):
    def __init__(self, square):
        self.obj = loader.loadModel(self.model)
        self.obj.reparentTo(render)
        self.obj.setPos(SquarePos(square))
        self.obj.setScale(self.scale)
        self.obj.setHpr(random.randrange(360), self.rot[1], self.rot[2])


"""
Classes for each type of topping. 
These can of course be updated depending on your needs. 
"""
class Broccoli(Topping):
    model = getModelFilePath("broccoli.obj")
    scale = 1.5
    rot = [0, 0, 0]

class Mushroom(Topping):
    model = getModelFilePath("mushroom.obj")
    scale = 4
    rot = [0, 0, 0]

class Pepper(Topping):
    model = getModelFilePath("paprikaSlice.obj")
    scale = 4
    rot = [0, 90, 0]

class Pepperoni(Topping):
    model = getModelFilePath("pepperoni.obj")
    scale = 4
    rot = [0, 90, 0]


""""""""""""""""""""""""
# Parse user arguments #
""""""""""""""""""""""""
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key', type=str,
                        help='Your Echo3D api key')
    parser.add_argument('security_key', type=str,
                        help='Your Echo3D security key')
    
    args = parser.parse_args()

    # Do the main initialization and start 3D rendering
    demo = PizzaDemo(args.api_key, args.security_key)
    demo.run()

    return 0


if __name__ == '__main__':
    main()
