# coding=utf-8
"""
Nick Canales, CC3501, 2020-2
Drawing a Sistema Planetario
"""

import glfw
from OpenGL.GL import *
import numpy as np
import sys
import json
import random as r

import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es


# A class to store the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True

# global controller as communication with the callback function
controller = Controller()

class World(object):
    def __init__(self):
        self.color = []
        self.radius = 0
        self.distance = 0
        self.velocity = 0
        self.satellites = []
        self.parent = None

    def createChilds(self, archivo):
        if archivo["Satellites"] == "Null":
            return
        else:
            child_list = []
            for satellites in archivo["Satellites"]:
                new_c = World()
                new_c.setParams(satellites, self)
                child_list.append(new_c)
            return child_list

    def setParams(self, archivo, parent):
        self.color = archivo["Color"]
        self.radius = archivo["Radius"]
        self.distance = archivo["Distance"]
        self.velocity = archivo["Velocity"]
        self.satellites = World.createChilds(self, archivo)
        self.parent = parent

    def getPradius(self):
        self.parent: World
        if self.parent != None:
            return self.parent.radius

    def getRadius(self):
        return self.radius

    def getDistance(self):
        return self.distance

    def getColor(self):
        return self.color

    def getVelocity(self):
        return self.velocity

    def getSatellites(self):
        return self.satellites

def on_key(window, key, scancode, action, mods):

    if action != glfw.PRESS:
        return
    
    global controller

    if key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon
    
    elif key == glfw.KEY_ESCAPE:
        sys.exit()

    else:
        print('Unknown key')

def jsonLector():
        with open('bodies.json') as f:
            archivo = json.load(f)
        return archivo

sp = jsonLector()
sol = World()
sol.setParams(sp, None)


#sacado de ex_scene_graph
def createColorCircle(N, R, r, g, b):

    # First vertex at the center
    vertices = [0, 0, 0, r, g, b]
    indices = []

    dtheta = 2 * np.pi / N

    for i in range(N):
        theta = i * dtheta

        vertices += [
            # vertex coordinates
            R * np.cos(theta), R * np.sin(theta), 0, r, g, b]

        indices += [0, i, i+2]
    # The final triangle connects back to the second vertex
    indices += [0, N, 1]
    return bs.Shape(vertices, indices)

def createColorCircumference(N, R, r, g, b):
    vertices = []
    indices = []
    dtheta = 2 * np.pi / N
    for i in range(N):
        theta = i * dtheta
        vertices += [
            # vertex coordinates
            R * np.cos(theta), R * np.sin(theta), 0, r, g, b]
        indices += [i, (i + 2) % N, (i + 4) % N]
    return bs.Shape(vertices, indices)

listSatellitesName = []
def createCircle(world):
    world: World
    # basic GPUShapes
    gpuCircleColor = es.toGPUShape(createColorCircle(50, 1, world.getColor()[0], world.getColor()[1], world.getColor()[2]))
    gpuCircumferenceColor = es.toGPUShape(createColorCircumference(70, 1, 0.5, 0.5, 0.5))

    orbit = sg.SceneGraphNode("orbit")
    #orbit

    # Body
    planet = sg.SceneGraphNode("planetBody")
    planet.transform = tr.uniformScale(world.getRadius())
    planet.childs = [gpuCircleColor]


    listSatellites = []
    if world.satellites != None:
        for s in world.satellites:
            s: World
            new_orbit = sg.SceneGraphNode("new_orbit")
            new_orbit.transform = tr.uniformScale(world.getRadius() + s.getDistance() + s.getRadius())
            new_orbit.childs += [gpuCircumferenceColor]
            orbit.childs += [new_orbit]

            satellite = sg.SceneGraphNode("satellite")
            satellite.transform = tr.translate(s.getDistance() + s.getPradius() + s.getRadius(), 0, 0)
            satellite.childs += [createCircle(s)]

            name = "luna" + str(r.random())
            velocity = s.getVelocity()

            sistem = sg.SceneGraphNode(name)
            sistem.childs += [satellite]

            listSatellitesName.append([name, velocity])
            listSatellites.append(sistem)


    # Snowman, the one and only
    planetary = sg.SceneGraphNode("planetary")
    planetary.childs = [orbit, planet]
    for i in listSatellites:
        planetary.childs += [i]

    return planetary


if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Sistema Planetario", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Assembling the shader program (pipeline) with both shaders
    pipeline = es.SimpleTransformShaderProgram()

    pipeline2 = es.SimpleTextureTransformShaderProgram()
    
    # Telling OpenGL to use our shader program



    # Setting up the clear screen color
    glClearColor(0.55, 0.55, 0.85, 1.0)

    # Creating shapes on GPU memory
    world= createCircle(sol)


    # Our shapes here are always fully painted
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    gpuShape = es.toGPUShape(bs.createTextureQuad("cielo-estrellado.jpg", 2, 2), GL_REPEAT, GL_LINEAR)

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()
        
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        for i in listSatellitesName:
            new_node = sg.findNode(world, i[0])
            theta = i[1] * glfw.get_time()
            new_node.transform = tr.rotationZ(theta)

        glUseProgram(pipeline2.shaderProgram)

        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "transform"), 1, GL_TRUE, tr.uniformScale(2))
        pipeline2.drawShape(gpuShape)

        glUseProgram(pipeline.shaderProgram)
        # Drawing the Car
        sg.drawSceneGraphNode(world, pipeline, "transform")

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()
