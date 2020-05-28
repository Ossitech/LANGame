import pygame
import math
import random

pygame.init()

fullscreen=True

if fullscreen:
    s=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height=s.get_size()
else:
    width=800
    height=600
    s=pygame.display.set_mode((width, height))

pygame.mouse.set_visible(True)
clock=pygame.time.Clock()

mx=0

class Block:
    def __init__(self, x, y):
        self.x=x
        self.y=y
        self.hasR=False
        self.hasL=False
        self.hasT=False
        self.hasB=False

class Map:
    def __init__(self, path, blocksize=100):
        self.path=path
        self.blocksize=blocksize
        plaintext=""
        with open(path, "r") as f:
            plaintext=f.read()
        lines=plaintext.split("\n")
        self.width=len(lines[0])
        self.height=len(lines)
        self.blocks=[]
        for i in range(len(plaintext)):
            if plaintext[i]=="#":
                self.blocks.append(Block(i%self.width, int(i/self.width)))
            elif plaintext[i]=="-":
                self.blocks.append(0)
        for x in range(self.width):
            for y in range(self.height):
                cb=self.getBlock(x, y)
                if cb!=0:
                    if self.getBlock(x, y-1)!=0:
                        cb.hasT=True
                    if self.getBlock(x, y+1)!=0:
                        cb.hasB=True
                    if self.getBlock(x-1, y)!=0:
                        cb.hasL=True
                    if self.getBlock(x+1, y)!=0:
                        cb.hasR=True
    def getBlock(self, x, y):
        if x<0 or x>=self.width or y<0 or y>=self.height:
            return 0
        return self.blocks[int(self.width*y+x)]
    def getEdges(self):
        edges=[]
        #Alle freien Kanten der Blöcke den Edges zufügen
        for x in range(self.width):
            for y in range(self.height):
                cb=self.getBlock(x, y)
                if cb!=0:
                    if cb.hasT==False:
                        edges.append(Edge(x*self.blocksize, y*self.blocksize, x*self.blocksize + self.blocksize, y*self.blocksize))
                    if cb.hasB==False:
                        edges.append(Edge(x*self.blocksize, y*self.blocksize + self.blocksize, x*self.blocksize + self.blocksize, y*self.blocksize + self.blocksize))
                    if cb.hasL==False:
                        edges.append(Edge(x*self.blocksize, y*self.blocksize, x*self.blocksize, y*self.blocksize + self.blocksize))
                    if cb.hasR==False:
                        edges.append(Edge(x*self.blocksize + self.blocksize, y*self.blocksize, x*self.blocksize + self.blocksize, y*self.blocksize + self.blocksize))
        #Edges in einer Linie zusammenfassen
        updated=True
        while updated:
            updated=False
            for e1 in range(len(edges)):
                for e2 in range(len(edges)):
                    if e1!=e2 and edges[e1]!=0 and edges[e2]!=0:
                        edge1=edges[e1]
                        edge2=edges[e2]
                        if edge1.a==edge2.x and edge1.b==edge2.y and edge1.angle==edge2.angle:
                            edges.append(Edge(edge1.x, edge1.y, edge2.a, edge2.b))
                            edges[e1]=0
                            edges[e2]=0
                            updated=True
        #Nullen aus der Liste löschen
        e=0
        while e<len(edges):
            if edges[e]==0:
                edges.pop(e)
            else:
                e+=1
        return edges

def getDistanceToEdge(x, y, edge):
    ne1=getAngledEdge(x, y, edge.angle+math.pi/2, 3000)
    ne2=getAngledEdge(x, y, edge.angle-math.pi/2, 3000)
    a, ax, ay=edgeIntersection(edge, ne1)
    if a:
        return abst(x, y, ax, ay)
    else:
        a, ax, ay=edgeIntersection(edge, ne2)
        if a:
            return abst(x, y, ax, ay)
        else:
            return min(abst(x, y, edge.x, edge.y), abst(x, y, edge.a, edge.b))

def abst(x, y, a, b):
    q1=a-x
    q2=b-y
    q1*=q1
    q2*=q2
    return math.sqrt(q1+q2)

def getAngle(a, b, c):
    ang = math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])
    return ang + math.pi*2 if ang < 0 else ang

def getAngledEdge(x, y, angle, length):
    return Edge(x, y, x+math.cos(angle)*length, y-math.sin(angle)*length, False, angle)

def edgeIntersection(line1, line2):
    xdiff = (line1.x - line1.a, line2.x - line2.a)
    ydiff = (line1.y - line1.b, line2.y - line2.b)

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return False, 0, 0

    d = (det([line1.x, line1.y], [line1.a, line1.b]), det([line2.x, line2.y], [line2.a, line2.b]))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    if abst(line1.x, line1.y, x, y)<=line1.length and abst(line1.a, line1.b, x, y)<=line1.length and abst(line2.x, line2.y, x, y)<=line2.length and abst(line2.a, line2.b, x, y)<=line2.length:
        return True, x, y
    return False, 0, 0

def getViewBeams(allEdges, sx, sy):
    beams=list()
    edges=allEdges.copy()
    edges=edges
    edges.sort(key=lambda e: getDistanceToEdge(sx, sy, e))
    edges=edges[:20]
    d=0.0001
    for edge in [sTop, sBottom]+edges:
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.x, edge.y).angle, 3000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(mx, my, Edge(sx, sy, edge.x, edge.y).angle+d, 3000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(mx, my, Edge(sx, sy, edge.x, edge.y).angle-d, 3000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.a, edge.b).angle, 10000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(mx, my, Edge(sx, sy, edge.a, edge.b).angle+d, 10000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(mx, my, Edge(sx, sy, edge.a, edge.b).angle-d, 10000)
        for i in [sTop, sBottom]+edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
    beams.sort(key=lambda x: x.angle)
    return beams

def drawViewPolygon(s, beams):
    for e in range(len(beams)):
        nextBeam=beams[(e+1)%len(beams)]
        pygame.draw.polygon(s, (255, 255, 255), beams[e].toLineTuple()+((nextBeam.a, nextBeam.b)))
        pygame.draw.polygon(s, (255, 255, 255), ((beams[e].x, beams[e].y), (beams[e].a, beams[e].b), (nextBeam.a, nextBeam.b)))

class Edge:
    def __init__(self, x, y, a, b, calcAngle=True, angle=0):
        self.x=x
        self.y=y
        self.a=a
        self.b=b
        if calcAngle:
            self.angle=getAngle([a, b], [x, y], [x+1, y])
        else:
            self.angle=angle
        self.length=abst(x, y, a, b)
    def draw(self, s):
        pygame.draw.line(s, (255, 0, 0), (self.x, self.y), (self.a, self.b), 1)
        pygame.draw.circle(s, (255, 255, 0), (self.x, self.y), 5, 0)
        pygame.draw.circle(s, (255, 255, 0), (self.a, self.b), 5, 0)
    def toLineTuple(self):
        return ((self.x, self.y), (self.a, self.b))
    def recalcLength(self):
        self.length=abst(x, y, a, b)

sTop=Edge(0, 0, width, 0)
sBottom=Edge(0, height, width, height)
sLeft=Edge(0, 0, 0, height)
sRight=Edge(width, 0, width, height)

edges=[
       Edge(400, 400, 500, 400),
       Edge(400, 400, 400, 500),
       Edge(500, 400, 500, 500),
       Edge(400, 500, 500, 500),

       Edge(600, 400, 800, 400),
       Edge(600, 400, 600, 500),
       Edge(800, 400, 800, 500),
       Edge(600, 500, 800, 500),

       Edge(100, 100, 200, 100),
       Edge(100, 100, 100, 200),
       Edge(200, 100, 100, 200),
       Edge(100, 200, 200, 300),

       Edge(200, 200, 300, 200),
       Edge(200, 200, 200, 300),
       Edge(300, 200, 300, 200),
       Edge(200, 300, 300, 300),

       Edge(700, 700, 800, 700),
       Edge(700, 700, 700, 800),
       Edge(800, 700, 800, 800),
       Edge(700, 800, 800, 800),
       ]

map=Map("D:/Programme_und_Coding/Python/LANGame/map.txt")
edges=map.getEdges()

while True:
    clock.tick(60)
    s.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            exit()
        if event.type==pygame.MOUSEMOTION:
            mx=event.pos[0]
            my=event.pos[1]
    for edge in edges:
        edge.draw(s)
    beams=getViewBeams(edges, mx, my)
    drawViewPolygon(s, beams)
    pygame.display.update()
