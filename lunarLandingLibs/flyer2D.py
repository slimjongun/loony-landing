import numpy as np 
import pygame
import math

import os
if os.getcwd() == 'C:\\Users\\Nardo\\Documents\\GitHub\\loony-landing\\lunarLandingLibs':
    import vectorAlgebra as va
else:
    import lunarLandingLibs.vectorAlgebra as va 
    # ^ this feels very hack-y and unprofessional but it gets the job done.


class Flyer(object):
    # Flyer is a class that captures all the fundamental information
    # required to do calculations involving rigid bodies. Because it makes 
    # modeling much easier, Flyers must be convex polygons or circles (maybe 
    # we'll extend this to ellipses).
    
    # A rigid body models a physical object with size, shape, and mass, that 
    # doesn't bend or break. It's a good approximation of, say, a wrench, and a
    # bad approximation of a water balloon. Unlike a particle (think a point with 
    # mass and position and velocity and nothing else), since it has size and 
    # shape, it can rotate and collide at angles.
    
    # tbh im not sure why i named it "Flyer." Maybe it sounds friendlier than RB?
    def __init__(self, x, y, mass, vertices=None): 
        self.pos = np.array([x, y])
        self.mass = mass
        self.angle = 0
        self.angularV = 0        
        self.v = np.array([0, 0])

        if vertices == None: 
            self.vertices = None
            self.r = 50
        else:
            self.vertices = [None] * len(vertices)
            self.r = 0
            for i in range(0, len(vertices)):
                self.vertices[i] = np.array(vertices[i])
                self.r = max(np.linalg.norm(self.pos - self.vertices[i]), self.r)
        self.momentOfInertia = self.getMomentOfInertia()
        self.Surface = pygame.Surface((2 * self.r, 2 * self.r))
        self.Surface.convert_alpha()
        self.Surface.set_colorkey((0, 0, 0)) #black is transparent.
        self.color = (255, 255, 255)

    def __repr__(self):
        return str(self.vertices)

    def getMomentOfInertia(self):
        if self.vertices == None: 
            return math.pi * (self.r**4) / 2  
        j = 0
        def segmentMoment(a, b):
            foo = (a[0] * b[1] - a[1] * b[0]) / 12
            momentAboutX = foo * (a[1]**2 + a[1] * b[1] + b[1]**2)
            momentAboutY = foo * (a[0]**2 + a[0] * b[0] + b[0]**2)
            return momentAboutX + momentAboutY
        self.sortVertices()
        for i in range(len(self.vertices)):
            j += segmentMoment(self.vertices[i - 1] - self.pos, self.vertices[i] - self.pos)
        return abs(j)

    def sortVertices(self):
        self.vertices.sort(key=lambda vert: getAngle(vert, self.pos))

    def getEdges(self): 
        #TODO: THIS ASSUMES VERTICES ARE ALREADY SORTED C-WISE OR CC-WISE! 
        #Either need to ensure thats always true or make sure this sorts edges accordingly
        # V this'll result in a div by 0 error
        # getAngle = lambda center, point: math.atan((point[1] - center[1]) / (point[0] - center[0])) 
        # self.vertices.sort(key=getAngle)
        edges = [] 
        self.sortVertices()
        for i in range(len(self.vertices)):
            edges.append([self.vertices[i - 1], self.vertices[i]])
        return edges

    def applyForce(self, force, deltaTime):
        #print("v was", self.v, end="")
        for i in range(2): self.v[i] += force[i] * deltaTime / self.mass
        #print(" adding", (force[0] * deltaTime / self.mass, force[1] * deltaTime / self.mass), " and now v is", self.v)

    def applyImpulse(self, impulse):
        for i in range(2): self.v[i] += impulse[i] / self.mass

    def draw(self, background):
        background.blit(self.Surface, (round(self.pos[0] - self.r), round(self.pos[1] - self.r)))
        if(self.vertices == None):
            pygame.draw.circle(background, self.color, (int(round(self.pos[0])), int(round(self.pos[1]))), self.r)
        else:
            def getIntPointList(a): 
                return [(round(a[i][0]), round(a[i][1])) for i in range(len(a))]
            pygame.draw.polygon(background,self.color, getIntPointList(self.vertices))

    def move(self, deltaTime):
        for i in range(len(self.vertices)): 
        # ^ iterating this way is bad style but aliasing necessitates it.
            vert = self.vertices[i]
            currTheta = getAngle(vert, self.pos) + self.angularV * deltaTime
            vert = self.pos + np.linalg.norm(vert - self.pos) * np.array([math.cos(currTheta), math.sin(currTheta)])
            vert += self.v * deltaTime
            self.vertices[i] = vert # again, bad style. 
        self.pos += self.v * deltaTime

class SpaceshipComponent(Flyer): 
    #TODO: need to break this up into engines, capsules, rockets, struts?, etc
    def __init__(self, x, y, xDiam, yDiam, mass, fuel):
        super().__init__(x, y, mass + fuel)
        self.fuel = fuel
        
        #if you pretend it's an ellipse, the xDiam is the diameter along
        #ITS x axis, not the global x axis.
        #Also, it's probably not going to be an ellipse - usually a cone or rectangle
        #or something like that, i expect.
        self.dims = [xDiam, yDiam]

    def steer(self, force):
        #fuel burned has a linear relationship with force produced. It really does! Proportion depends on fuel though.F
        pass

class Astronaut(Flyer):
    def __init__(self, x, y, mass, name):
        super().__init__(x, y, mass)
        self.health = 100
        self.name = name

class Spaceship(object):
    def __init__(self, x, y):
        self.pos = [x, y]
        self.stage = 0 #stage of separation I guess

class TestPlayer(Flyer):
    def __init__(self, x, y, mass, vertices):
        super().__init__(x, y, mass, vertices)

def puckCollide(A, B, deltaTime): #should i make deltaTime a global?
    dist = np.linalg.norm(A.pos - B.pos)
    if dist <= A.r + B.r: 
        deltaAVcoeff = (-2 * B.mass / (A.mass + B.mass)) * np.dot(A.v - B.v, A.pos - B.pos) / np.dot(A.pos - B.pos, A.pos - B.pos)
        deltaAV = deltaAVcoeff * (A.pos - B.pos) 
        #^if you stare at the above two lines for a while and ignore all the 
        #mass terms, this is really just a projection of relative velocity vector
        #onto the line connecting the centers of A and B.
        FBonA = A.mass * deltaAV / deltaTime #newton's second law
        FAonB = -FBonA #newton's third law
        A.applyForce(FBonA, deltaTime)
        B.applyForce(FAonB, deltaTime)

def boundsIntersect(A, B):
    #TODO: use pygame bounding boxes for sake of speed
    return np.linalg.norm(A.pos - B.pos) < A.r + B.r #yes, strictly less than

def getYIntercept(edge):
    return edge[0][1] - getSlope(edge) * edge[0][0]

def getSlope(edge):
    if edge[1][0] == edge[0][0]: return None
    else: return (edge[1][1] - edge[0][1]) / (edge[1][0] - edge[0][0])

def getEdgeIntersect(a, b):
    #edge is represented as a 2-length list of [x, y] coordinates
    slopeA, slopeB = getSlope(a), getSlope(b)
    if slopeA == slopeB:
        return None
    elif None in (slopeA, slopeB): 
        if slopeA == None:
            verticalEdge, realEdge = a, b
            verticalSlope, realSlope = slopeA, slopeB
        else: 
            verticalEdge, realEdge = b, a
            verticalSlope, realSlope = slopeB, slopeA
        x = verticalEdge[0][0]
        assert(x == verticalEdge[1][0])
        y = realSlope * x + getYIntercept(realEdge)
    else:
        x = (getYIntercept(b) - getYIntercept(a)) / (slopeA - slopeB)
        y = slopeA * x + getYIntercept(a)
    
    def btw(x, a, b): 
        return min(a, b) <= x <= max(a, b)

    if (btw(x, a[0][0], a[1][0]) and
        btw(y, a[0][1], a[1][1]) and
        btw(x, b[0][0], b[1][0]) and
        btw(y, b[0][1], b[1][1])):
        return (x, y)

def rewindPosAndAng(A, deltaTime):
    A.pos += A.v * deltaTime
    A.angle += A.angularV * deltaTime

def getIntersects(A, B, deltaTime): 
    #TODO: think this is going to be troublesome with numpy's precision. Bug waiting to occur

    rewindPosAndAng(A, deltaTime)
    rewindPosAndAng(B, deltaTime) #DO NOT UNDO THIS BEFORE RETURNING. 
    #TODO: this isn't very clear, but i think this saves a lil time... refactor getNorm and getIntersects for clarity
    if boundsIntersect(A, B):
        intersects = []
        for edgeA in A.getEdges():
            for edgeB in B.getEdges():
                edgeIntersect = getEdgeIntersect(edgeA, edgeB)
                if edgeIntersect != None: intersects.append(edgeIntersect)
                if len(intersects) == 2:
                    return intersects
    return None

def getNorm(intersects, facing):
    tangent = intersects[1] - intersects[0]
    n = np.array([tangent[1], -tangent[0]])
    
    mid = (intersects[0] + intersects[1])/2
    n = va.proj(facing.pos - mid, n)
    n /= va.dot(n, n)

    return n

def genCollide(A, B, deltaTime):
    intersects = getIntersects(A, B, 0)
    if intersects == None: return
    hi = deltaTime
    lo = 0
    i = 0
    timeEdit = 0
    while(i < 4 or (intersects == None and len(intersects) != 2)): 
        #TODO: 4 is a magic number. Should make desired iters a function of relative speed or something
        #iterate as desired, but better have 2 intersect points!

        if intersects == None or len(intersects) != 2: 
            lo = (lo + hi)/2
            timeEdit = (lo + hi)/2
        else:
            hi = (lo + hi)/2
            timeEdit = -(lo + hi)/2
        intersects = getIntersects(A, B, timeEdit)
    n = getNorm(intersects)
    #TODO: apply the crazy formula to A
    n = -n
    #now apply to B



def testCollide(A, B, deltaTime):
    intersects = getIntersects(A, B, 0)
    return intersects

def getSysKE(A, B):
    return 0.5 * (A.mass * np.linalg.norm(A.v)**2) + 0.5 * (B.mass * np.linalg.norm(B.v)**2)

def getSysMomentum(A, B):
    return A.mass * A.v + B.mass * B.v

def almostEqual(a, b, alpha=0.001):
    return abs(a - b) <= alpha

def getAngle(point, origin):
    # returns angle subtended btw x-axis and vector from origin to point.
    opp = point[1] - origin[1]
    adj = point[0] - origin[0]
    return math.atan2(opp, adj)
    