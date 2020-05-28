import pygame
import math
import random
import time
import _thread
import threading
import os
import oznet
import sys

import tkinter as tk

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

width=int(screen_width/4)
height=int(screen_height/4)

root.destroy()

pygame.mixer.pre_init(channels=12)

pygame.init()

name="Ossitech"

fullscreen=True

noRadarRequired=False

if fullscreen:
    s=pygame.display.set_mode((width, height), pygame.FULLSCREEN|pygame.SCALED)
else:
    s=pygame.display.set_mode((width, height))

pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

mx=0
my=0

#Netzwerk
#region
GAME_PORT=12000
isHosting=True
ips=[]
ports={}
SERVER_IP=None
try:
    name=sys.argv[1]
    SERVER_IP=sys.argv[2]
    SERVER_PORT=int(sys.argv[3])
    GAME_PORT=int(sys.argv[4])
    isHosting=False
except:
    pass
oz=oznet.Oz("", GAME_PORT)
def broadcast(msg):
    for ip in ips:
        #print("Sende an "+ip+":"+ports[ip])
        oz.send(msg, ip, ports[ip])
def broadcastImportant(msg):
    for ip in ips:
        oz.send(msg, ip, ports[ip])
#Host
#region
def host(msg, ip, port):
    if not ip in ips:
        ips.append(ip)
        ports[ip]=port
    msg_splitted=msg.split()
    if msg_splitted[0]=="new_player_join":
        newName=msg_splitted[1]
        if newName in players:
            print(ip, str(port), newName+" gibts schon!")
            oz.sendImportant("name_already_in_use", ip, port)
        else:
            players[newName]=defaultPlayer(50, 50, newName)
            info="new_player "+newName+" "+str(players[newName].vesselIndex)+" "+str(players[newName].weaponL.weaponIndex)+" "+str(players[newName].weaponR.weaponIndex)+" "+str(players[newName].x)+" "+str(players[newName].y)+" "+str(players[newName].HP)
            broadcastImportant(info)
            for pn in players:
                if pn!=newName:
                    info="new_player "+pn+" "+str(players[pn].vesselIndex)+" "+str(players[pn].weaponL.weaponIndex)+" "+str(players[pn].weaponR.weaponIndex)+" "+str(players[pn].x)+" "+str(players[pn].y)+" "+str(players[pn].HP)
                    oz.send(info, ip, port)
            oz.send(map.getText(), ip, port)
    elif msg_splitted[0]=="key_press":
        pn=msg_splitted[1]
        key=msg_splitted[2]
        if msg_splitted[3]=="True":
            pressed=True
        else:
            pressed=False
        if key=="up":
            players[pn].up=pressed
        elif key=="down":
            players[pn].down=pressed
        elif key=="left":
            players[pn].left=pressed
        elif key=="right":
            players[pn].right=pressed
        elif key=="shift":
            players[pn].shift=pressed
        elif key=="r":
            players[pn].r=pressed
        elif key=="mousel":
            players[pn].weaponL.click=pressed
        elif key=="mouser":
            players[pn].weaponR.click=pressed
    elif msg_splitted[0]=="disconnect":
        pn=msg_splitted[1]
        players.pop(pn, None)
        ports.pop(ip, None)
        try:
            ips.remove(ip)
        except:
            pass
        broadcastImportant(msg)
    elif msg_splitted[0]=="wants_change_weapon_l":
        pn=msg_splitted[1]
        weaponIndex=int(msg_splitted[2])
        players[pn].weaponL=allWeapons[weaponIndex](pn)
        info="change_weapon_l "+pn+" "+msg_splitted[2]
        broadcastImportant(info)
    elif msg_splitted[0]=="wants_change_weapon_r":
        pn=msg_splitted[1]
        weaponIndex=int(msg_splitted[2])
        players[pn].weaponR=allWeapons[weaponIndex](pn)
        info="change_weapon_r "+pn+" "+msg_splitted[2]
        broadcastImportant(info)
    elif msg_splitted[0]=="wants_change_vessel":
        pn=msg_splitted[1]
        cp=players[pn]
        vesselIndex=int(msg_splitted[2])
        newVessel=allVessels[vesselIndex](0, 0, pn)
        newVessel.x=cp.x
        newVessel.y=cp.y
        newVessel.angle=cp.angle
        newVessel.weaponL=cp.weaponL
        newVessel.weaponR=cp.weaponR
        newVessel.HP=min(newVessel.maxHP, cp.HP)
        players[pn]=newVessel
        info="change_vessel "+pn+" "+msg_splitted[2]
        broadcastImportant(info)
    elif msg_splitted[0]=="cursor":
        pn=msg_splitted[1]
        x=float(msg_splitted[2])
        y=float(msg_splitted[3])
        players[pn].curx=x
        players[pn].cury=y
        players[pn].angle=Edge(players[pn].x, players[pn].y, x, y).angle
        broadcast(msg)
#endregion
#Client
#region
def client(msg, ip, port):
    msg_splitted=msg.split()
    if msg_splitted[0]=="name_already_in_use":
        pygame.quit()
        print("Name "+name+" wird schon verwendet!")
        oz.sendImportant("disconnect "+name, SERVER_IP, SERVER_PORT)
        time.sleep(5)
        exit()
    elif msg_splitted[0]=="new_player":#new_player NAME VESSELINDEX WEAPONINDEX_L WEAPONINDEX_R X Y HP
        pn=msg_splitted[1]
        vesselIndex=int(msg_splitted[2])
        weaponIndexL=int(msg_splitted[3])
        weaponIndexR=int(msg_splitted[4])
        x=float(msg_splitted[5])
        y=float(msg_splitted[6])
        HP=int(msg_splitted[7])
        if name!=pn:
            players[pn]=allVessels[vesselIndex](x, x, pn)
            players[pn].weaponL=allWeapons[weaponIndexL](pn)
            players[pn].weaponR=allWeapons[weaponIndexR](pn)
            players[pn].HP=HP
    elif msg_splitted[0]=="change_weapon_r":
        pn=msg_splitted[1]
        weaponIndex=int(msg_splitted[2])
        players[pn].weaponR=allWeapons[weaponIndex](pn)
    elif msg_splitted[0]=="change_weapon_l":
        pn=msg_splitted[1]
        weaponIndex=int(msg_splitted[2])
        players[pn].weaponL=allWeapons[weaponIndex](pn)
    elif msg_splitted[0]=="change_vessel":#change_vessel NAME VESSELINDEX
        pn=msg_splitted[1]
        cp=players[pn]
        vesselIndex=int(msg_splitted[2])
        newVessel=allVessels[vesselIndex](0, 0, pn)
        newVessel.x=cp.x
        newVessel.y=cp.y
        newVessel.angle=cp.angle
        newVessel.weaponL=cp.weaponL
        newVessel.weaponR=cp.weaponR
        newVessel.HP=min(newVessel.maxHP, cp.HP)
        players[pn]=newVessel
    elif msg_splitted[0]=="apply_damage":#apply_damage WEM VON_WEM SCHADEN QUELLE_X QUELLE_Y
        pn=msg_splitted[1]
        owner=msg_splitted[2]
        amount=float(msg_splitted[3])
        sx=float(msg_splitted[4])
        sy=float(msg_splitted[5])
        players[pn].damage(amount, sx, sy, owner)
    elif msg_splitted[0]=="server_closed":
        exit()
    elif msg_splitted[0]=="move":
        pn=msg_splitted[1]
        x=float(msg_splitted[2])
        y=float(msg_splitted[3])
        ba=float(msg_splitted[4])
        players[pn].x=x
        players[pn].y=y
        players[pn].baseAngle=ba
    elif msg_splitted[0]=="cursor":
        pn=msg_splitted[1]
        x=float(msg_splitted[2])
        y=float(msg_splitted[3])
        players[pn].curx=x
        players[pn].cury=y
        players[pn].angle=Edge(players[pn].x, players[pn].y, x, y).angle
        players[pn].cursorChanged=True
    elif msg_splitted[0]=="spawn_projectile":
        owner=msg_splitted[1]
        projectileIndex=int(msg_splitted[2])
        x=float(msg_splitted[3])
        y=float(msg_splitted[4])
        tx=float(msg_splitted[5])
        ty=float(msg_splitted[6])
        id=float(msg_splitted[7])
        projectiles.append(allProjectiles[projectileIndex](x, y, tx, ty, owner))
    elif msg_splitted[0]=="remove_projectile":
        id=float(msg_splitted[1])
        for p in projectiles:
            if p.id==id:
                p.lifetime=0
                break
    elif msg_splitted[0]=="disconnect":
        pn=msg_splitted[1]
        players.pop(pn, None)
    elif msg_splitted[0]=="spawn":
        pn=msg_splitted[1]
        x=float(msg_splitted[2])
        y=float(msg_splitted[3])
        players[pn].x=x
        players[pn].y=y
        players[pn].HP=players[pn].maxHP
        players[pn].invDelay=4
    elif msg_splitted[0]=="death":
        pn=msg_splitted[1]
        killer=msg_splitted[2]
        players[killer].score+=1
    elif msg_splitted[0]=="spawn_particle":
        index=int(msg_splitted[1])
        x=float(msg_splitted[2])
        y=float(msg_splitted[3])
        angle=float(msg_splitted[4])
        particles.append(allParticles[index](x, y, angle))
    elif msg_splitted[0]=="map":
        mapText=msg_splitted[1]
        global map
        global edges
        map=Map(text=mapText)
        edges=map.getEdges()
def join():
    oz.send("new_player_join "+name, SERVER_IP, SERVER_PORT)
def disconnect():
    if isHosting:
        broadcastImportant("server_closed")
    else:
        oz.send("disconnect "+name, SERVER_IP, SERVER_PORT)
    oz.stop()
#endregion
#endregion

#Hilfsfunktionen
#region
class Block:
    def __init__(self, x, y):
        self.x=x
        self.y=y
        self.hasR=False
        self.hasL=False
        self.hasT=False
        self.hasB=False

class Map:
    def __init__(self, path="", blocksize=100, text=""):
        self.path=path
        self.blocksize=blocksize
        self.plaintext=""
        try:
            with open(path, "r") as f:
                self.plaintext=f.read()
            lines=self.plaintext.split("\n")
            self.width=len(lines[0])
            self.height=len(lines)
        except:
            self.width=0
            self.height=0
        if text!="":
            self.plaintext=text
            lines=text.split("\n")
            self.width=len(lines[0])
            self.height=len(lines)
        self.blocks=[]
        self.mapImage=pygame.Surface((self.width, self.height))
        for i in range(len(self.plaintext)):
            if self.plaintext[i]=="#":
                self.blocks.append(Block(i%self.width, int(i/self.width)))
            elif self.plaintext[i]=="-":
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
        if len(self.blocks)==0:
            self.blocks=[0]
    def getBlock(self, x, y):
        if x<0 or x>=self.width or y<0 or y>=self.height:
            return 0
        x=int(x)
        y=int(y)
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
    def getText(self):
        return self.plaintext

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

def getNearestPoint(x, y, edge):
    ne1=getAngledEdge(x, y, edge.angle+math.pi/2, 3000)
    ne2=getAngledEdge(x, y, edge.angle-math.pi/2, 3000)
    a, ax, ay=edgeIntersection(edge, ne1)
    if a:
        return ax, ay
    else:
        a, ax, ay=edgeIntersection(edge, ne2)
        if a:
            return ax, ay
        else:
            tmp1=abst(x, y, edge.x, edge.y)
            tmp2=abst(x, y, edge.a, edge.b)
            if tmp1<=tmp2:
                return edge.x, edge.y
            else:
                return edge.a, edge.b

def abst(x, y, a, b):
    q1=a-x
    q2=b-y
    q1*=q1
    q2*=q2
    return math.sqrt(q1+q2)

def clamp(value, start, end):
    return max(start, min(end, value))

def getTriangleArea(a, b, c):
    det=((a[0]-c[0])*(b[1]-c[1]))-((b[0]-c[0])*(a[1]-c[1]))
    return det/2

def isPointInTriangle(p, a, b, c):
    totalArea=getTriangleArea(a, b, c)
    area1=getTriangleArea(p, b, c)
    area2=getTriangleArea(p, a, c)
    area3=getTriangleArea(p, a, b)
    if(totalArea==0):
        #return False
        totalArea=0.001
    alpha=area1/totalArea
    beta=area2/totalArea
    gamma=area3/totalArea
    if alpha>=0 and alpha<=1 and beta>=0 and beta<=1 and gamma>=0 and gamma<=1:
        return True
    return False

def isPointInView(eye, p, edges):
    for e in edges:
        a, ax, ay=edgeIntersection(Edge(eye[0], eye[1], p[0], p[1], calcAngle=False), e)
        if a:
            return False
    return True

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

def isOnScreen(x, y, border=0):
    a=x-camShiftX
    b=y-camShiftY
    if a+border>=0 and a-border<width and b+border>=0 and b-border<height:
        return True
    return False

def rotCenter(image, angle):
    angle=math.degrees(angle)
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

def drawCentered(s, image, x, y, angle):
    rect=image.get_rect()
    if angle!=0:
        s.blit(rotCenter(image, angle), (x-rect.width/2, y-rect.height/2))
    else:
        s.blit(image, (x-rect.width/2, y-rect.height/2))

num_tries=0
def isValidSpawnPoint(x, y):
    global num_tries
    if map.getBlock(int(x/map.blocksize), int(y/map.blocksize))==0 and (getDistanceToNearestPlayer(x, y)>200 or num_tries>10):
        num_tries=0
        return True
    num_tries+=1
    return False

def getDistanceToNearestPlayer(x, y):
    d=10000000
    for pn in players:
        tmp=abst(x, y, players[pn].x, players[pn].y)
        if tmp<d:
            d=tmp
    return d
#endregion

class Edge:
    def __init__(self, x, y, a, b, calcAngle=True, angle=0):
        self.x=x
        self.y=y
        self.a=a
        self.b=b
        self.vx=self.a-self.x
        self.vy=self.b-self.y
        if calcAngle:
            self.angle=getAngle([a, b], [x, y], [x+1, y])
        else:
            self.angle=angle
        self.length=abst(x, y, a, b)
    def draw(self, s):
        pygame.draw.line(s, (min(255, int(math.degrees(self.angle))), 0, 0), (int(self.x-camShiftX), int(self.y-camShiftY)), (int(self.a-camShiftX), int(self.b-camShiftY)), 1)
        #pygame.draw.line(s, (255, 0, 0), (int(self.x-camShiftX), int(self.y-camShiftY)), (int(self.a-camShiftX), int(self.b-camShiftY)), 1)
        pygame.draw.circle(s, (255, 255, 0), (int(self.x-camShiftX), int(self.y-camShiftY)), 5, 0)
        pygame.draw.circle(s, (255, 255, 0), (int(self.a-camShiftX), int(self.b-camShiftY)), 5, 0)
    def toLineTuple(self):
        return ((self.x, self.y), (self.a, self.b))
    def recalcLength(self):
        self.length=abst(self.x, self.y, self.a, self.b)
    def normalize(self):
        self.a=self.x+(self.a-self.x)/self.length
        self.b=self.y+(self.b-self.y)/self.length
        self.vx=self.a-self.x
        self.vy=self.b-self.y
        self.length=1
    def copy(self):
        return Edge(self.x, self.y, self.a, self.b)

#Projektile
#region
class plasmaBall:
    def __init__(self, x, y, targetX, targetY, owner, id=0):
        self.x=x
        self.y=y
        tmp=abst(x, y, targetX, targetY)
        if tmp==0:
            tmp+=0.01
        self.vx=(targetX-x)/tmp
        self.vy=(targetY-y)/tmp
        self.targetX=targetX
        self.targetY=targetY
        self.angle=Edge(x, y, targetX, targetY).angle
        self.speed=300
        self.damage=50
        self.lifetime=5
        self.owner=owner
        if id==0:
            self.id=time.time()
        else:
            self.id=id
        self.sprite=projectileSprites["plasmaBall"]
    def draw(self, s, dt):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
        pygame.draw.circle(lightSurface, (255, 255, 255), (self.x-camShiftX, self.y-camShiftY), 20, 0)
        self.x+=self.vx*self.speed*dt
        self.y+=self.vy*self.speed*dt
        if map.getBlock(self.x/map.blocksize, self.y/map.blocksize)!=0:
            self.lifetime=0
        for pn in players:
            if pn!=self.owner:
                cp=players[pn]
                tmp=abst(self.x, self.y, cp.x, cp.y)
                if tmp<5+cp.collisionRadius and cp.invDelay<=0 and cp.HP>0:
                    self.lifetime=0
                    if isHosting:
                        cp.damage(self.damage, self.x ,self.y, self.owner)
                        broadcastImportant("apply_damage "+pn+" "+self.owner+" "+str(self.damage)+" "+str(self.x)+" "+str(self.y))
        self.lifetime-=dt
class needle:
    def __init__(self, x, y, targetX, targetY, owner, id=0):
        if isOnScreen(x, y):
            random.choice(gunSounds["Needler"]).play()
        self.x=x
        self.y=y
        tmp=abst(x, y, targetX, targetY)
        if tmp==0:
            tmp+=0.01
        self.vx=(targetX-x)/tmp
        self.vy=(targetY-y)/tmp
        self.targetX=targetX
        self.targetY=targetY
        self.angle=Edge(x, y, targetX, targetY).angle
        self.speed=1000
        self.damage=20
        self.lifetime=5
        self.owner=owner
        self.collisions=0
        if id==0:
            self.id=time.time()
        else:
            self.id=id
        self.sprite=projectileSprites["needle"]
    def draw(self, s, dt):
        if isOnScreen(self.x, self.y):
            drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
            pygame.draw.circle(lightSurface, (255, 255, 255), (self.x-camShiftX, self.y-camShiftY), 20, 0)
        self.x+=self.vx*self.speed*dt
        self.y+=self.vy*self.speed*dt
        if map.getBlock(self.x/map.blocksize, self.y/map.blocksize)!=0:
            self.lifetime=0
        for pn in players:
            if pn!=self.owner:
                cp=players[pn]
                tmp=abst(self.x, self.y, cp.x, cp.y)
                if tmp<5+cp.collisionRadius and cp.invDelay<=0 and cp.HP>0:
                    self.lifetime=0
                    if isHosting:
                        cp.damage(self.damage, self.x ,self.y, self.owner)
                        broadcastImportant("apply_damage "+pn+" "+self.owner+" "+str(self.damage)+" "+str(self.x)+" "+str(self.y))
        if self.collisions<3:
            travel=Edge(self.x, self.y, self.x+self.vx*dt*self.speed, self.y+self.vy*dt*self.speed)
            for edge in edges:
                a, ax, ay=edgeIntersection(travel, edge)
                if a:
                    self.x=ax
                    self.y=ay
                    self.angle=edge.angle-(travel.angle-edge.angle)
                    newTravel=getAngledEdge(ax, ay, self.angle, 0.2)
                    self.x=newTravel.a
                    self.y=newTravel.b
                    newTravel=getAngledEdge(self.x, self.y, self.angle, 1)
                    self.vx=newTravel.a-newTravel.x
                    self.vy=newTravel.b-newTravel.y
                    self.collisions+=1
                    self.damage*=1.2
                    if isOnScreen(self.x, self.y):
                        random.choice(needleSounds).play()
                    break
        self.lifetime-=dt
class missile:
    def __init__(self, x, y, targetX, targetY, owner, id=0):
        if isOnScreen(x, y):
            random.choice(gunSounds["missileLauncher"]).play()
        self.x=x
        self.y=y
        tmp=abst(x, y, targetX, targetY)
        if tmp==0:
            tmp+=0.01
        self.vx=(targetX-x)/tmp
        self.vy=(targetY-y)/tmp
        self.targetX=targetX
        self.targetY=targetY
        self.angle=Edge(x, y, targetX, targetY).angle
        self.speed=350
        self.damage=30
        self.lifetime=5
        self.owner=owner
        self.turnSpeed=1
        if id==0:
            self.id=time.time()
        else:
            self.id=id
        self.sprite=projectileSprites["missile"]
        self.lastTargeted=""
    def draw(self, s, dt):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
        pygame.draw.circle(lightSurface, (255, 255, 255), (self.x-camShiftX, self.y-camShiftY), 20, 0)
        if map.getBlock(self.x/map.blocksize, self.y/map.blocksize)==0:
            d=10000000
            nearestEdge=None
            targetedPlayer=""
            for pn in players:
                if pn!=self.owner:
                    cp=players[pn]
                    direction=Edge(self.x, self.y, cp.x, cp.y)
                    tmpAngle=direction.angle-self.angle
                    if tmpAngle>math.pi:#>180
                        tmpAngle-=2*math.pi#-=360
                    if direction.length<d and abs(tmpAngle)<math.pi/4:
                        d=direction.length
                        nearestEdge=direction
                        targetedPlayer=pn
                    if direction.length<5+cp.collisionRadius and cp.invDelay<=0 and cp.HP>0:
                        self.lifetime=0
            if nearestEdge!=None:
                targetEdge=Edge(self.x, self.y, nearestEdge.a, nearestEdge.b)
                targetEdge.normalize()
                tp=players[targetedPlayer]
                #Marker zur anvisierung zeichnen
                pygame.draw.rect(s, (255, 0, 0), ((tp.x-tp.collisionRadius/2-camShiftX, tp.y-tp.collisionRadius/2-camShiftY), (tp.collisionRadius, tp.collisionRadius)), 1)
                if targetedPlayer==name and targetedPlayer!=self.lastTargeted:
                    targetSound.play()
                self.lastTargeted=targetedPlayer
                self.angle=targetEdge.angle
                if self.vx>targetEdge.vx:
                    self.vx-=self.turnSpeed*dt
                if self.vx<targetEdge.vx:
                    self.vx+=self.turnSpeed*dt
                if self.vy>targetEdge.vy:
                    self.vy-=self.turnSpeed*dt
                if self.vy<targetEdge.vy:
                    self.vy+=self.turnSpeed*dt
            self.x+=self.vx*self.speed*dt
            self.y+=self.vy*self.speed*dt
        self.lifetime-=dt
        if self.lifetime<=0:
            particles.append(explosion(self.x, self.y, self.angle))
            if isHosting:
                for pn in players:
                    if pn!=self.owner:
                        cp=players[pn]
                        tmp=abst(self.x, self.y, cp.x, cp.y)
                        if tmp<cp.collisionRadius*2:
                            cp.damage(self.damage, self.x ,self.y, self.owner)
                            broadcastImportant("apply_damage "+pn+" "+self.owner+" "+str(self.damage)+" "+str(self.x)+" "+str(self.y))
class sniperShot:
    def __init__(self, x, y, targetX, targetY, owner, id=0):
        if isOnScreen(x, y):
            random.choice(gunSounds["sniper"]).play()
        self.x=x
        self.y=y
        self.targetX=targetX
        self.targetY=targetY
        self.shot=Edge(x, y, targetX, targetY)
        self.angle=self.shot.angle
        self.shot=getAngledEdge(self.x, self.y, self.angle, 3000)
        self.speed=0
        self.damage=150
        self.maxLifetime=1
        self.lifetime=self.maxLifetime
        self.owner=owner
        if id==0:
            self.id=time.time()
        else:
            self.id=id
        #Länge begrenzen
        for edge in edges:
            a, ax, ay=edgeIntersection(self.shot, edge)
            if a:
                self.shot.a=ax
                self.shot.b=ay
                self.shot.recalcLength()
        #Punkte erzeugen
        self.points=[]
        self.rands=[]
        step=getAngledEdge(self.x, self.y, self.shot.angle, 5)
        px=self.x
        py=self.y
        while abst(px, py, self.x, self.y)<self.shot.length:
            self.points.append([px, py])
            self.rands.append([random.randint(-5, 5), random.randint(-5, 5)])
            px+=step.vx
            py+=step.vy
        #Damage
        if isHosting:
            for pn in players:
                if pn!=self.owner:
                    cp=players[pn]
                    tmp=getDistanceToEdge(cp.x, cp.y, self.shot)
                    if tmp<=cp.collisionRadius and cp.invDelay<=0 and cp.HP>0:
                        cp.damage(self.damage, self.x ,self.y, self.owner)
                        broadcastImportant("apply_damage "+pn+" "+self.owner+" "+str(self.damage)+" "+str(self.x)+" "+str(self.y))
    def draw(self, s, dt):
        #Strich malen
        faktor=self.lifetime/self.maxLifetime
        for i in range(len(self.points)):
            if i<len(self.points)-1:
                pygame.draw.line(s, (100+155*faktor, 120+135*faktor*faktor, 100+155*faktor*faktor), (self.points[i][0]-camShiftX, self.points[i][1]-camShiftY), (self.points[i+1][0]-camShiftX, self.points[i+1][1]-camShiftY), int(1+2*faktor))
            self.points[i][0]+=self.rands[i][0]*dt
            self.points[i][1]+=self.rands[i][1]*dt
        self.lifetime-=dt

allProjectiles=[]
allProjectiles.append(plasmaBall)
allProjectiles.append(needle)
allProjectiles.append(missile)
allProjectiles.append(sniperShot)
#endregion

#Weapons
#region
class plasmaGun:
    def __init__(self, owner):
        self.weaponIndex=0
        self.owner=owner
        self.x=0
        self.y=0
        self.xt=0
        self.yt=0
        self.angle=0
        self.sprite=gunSprites["plasmaGun"]
        self.maxDelay=0.25
        self.delay=0
        self.click=False
    def draw(self, s):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
    def update(self, dt, startx, starty, targetx, targety):
        self.x=startx
        self.y=starty
        self.xt=targetx
        self.yt=targety
        self.angle=Edge(startx, starty, targetx, targety).angle
        if isHosting:
            if self.delay<=0:
                if self.click and players[self.owner].repairDelay<=0:
                    self.delay=self.maxDelay
                    muzzle=getAngledEdge(self.x, self.y, self.angle, 10)
                    newProjectile=plasmaBall(muzzle.a, muzzle.b, self.xt, self.yt, self.owner)
                    projectiles.append(newProjectile)
                    broadcastImportant("spawn_projectile "+self.owner+" "+str(self.weaponIndex)+" "+str(muzzle.a)+" "+str(muzzle.b)+" "+str(self.xt)+" "+str(self.yt)+" "+str(newProjectile.id))
            else:
                self.delay-=dt
class needler:
    def __init__(self, owner):
        self.weaponIndex=1
        self.owner=owner
        self.x=0
        self.y=0
        self.xt=0
        self.yt=0
        self.angle=0
        self.sprite=gunSprites["needler"]
        self.maxDelay=1
        self.delay=0
        self.click=False
    def draw(self, s):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
    def update(self, dt, startx, starty, targetx, targety):
        self.x=startx
        self.y=starty
        self.xt=targetx
        self.yt=targety
        self.angle=Edge(startx, starty, targetx, targety).angle
        if isHosting:
            if self.delay<=0:
                if self.click and players[self.owner].repairDelay<=0:
                    self.delay=self.maxDelay
                    _thread.start_new_thread(self.shoot, (),)
            else:
                self.delay-=dt
    def shoot(self):
        for i in range(3):
            muzzle=getAngledEdge(self.x, self.y, self.angle, 10)
            newProjectile=needle(muzzle.a, muzzle.b, self.xt, self.yt, self.owner)
            projectiles.append(newProjectile)
            broadcastImportant("spawn_projectile "+self.owner+" "+str(self.weaponIndex)+" "+str(muzzle.a)+" "+str(muzzle.b)+" "+str(self.xt)+" "+str(self.yt)+" "+str(newProjectile.id))
            time.sleep(0.1)
class missileLauncher:
    def __init__(self, owner):
        self.weaponIndex=2
        self.owner=owner
        self.x=0
        self.y=0
        self.xt=0
        self.yt=0
        self.angle=0
        self.sprite=gunSprites["missileLauncher"]
        self.maxDelay=3
        self.delay=0
        self.click=False
    def draw(self, s):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
    def update(self, dt, startx, starty, targetx, targety):
        self.x=startx
        self.y=starty
        self.xt=targetx
        self.yt=targety
        self.angle=Edge(startx, starty, targetx, targety).angle
        if isHosting:
            if self.delay<=0:
                if self.click and players[self.owner].repairDelay<=0:
                    self.delay=self.maxDelay
                    _thread.start_new_thread(self.shoot, (),)
            else:
                self.delay-=dt
    def shoot(self):
        for i in range(5):
            muzzle=getAngledEdge(self.x, self.y, self.angle, 10)
            rx=random.randint(-5, 5)
            ry=random.randint(-5, 5)
            newProjectile=missile(muzzle.a+rx, muzzle.b+ry, self.xt, self.yt, self.owner)
            projectiles.append(newProjectile)
            #                   spawn_projectile OWNER         PROJ_INDEX STARTX        STARTY              CURSORX             CURSORY         PROJ_ID
            broadcastImportant("spawn_projectile "+self.owner+" "+str(self.weaponIndex)+" "+str(muzzle.a+rx)+" "+str(muzzle.b+ry)+" "+str(self.xt)+" "+str(self.yt)+" "+str(newProjectile.id))
            time.sleep(0.15)
class sniper:
    def __init__(self, owner):
        self.weaponIndex=3
        self.owner=owner
        self.x=0
        self.y=0
        self.xt=0
        self.yt=0
        self.angle=0
        self.sprite=gunSprites["sniper"]
        self.maxDelay=2
        self.delay=0
        self.click=False
    def draw(self, s):
        drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
    def update(self, dt, startx, starty, targetx, targety):
        self.x=startx
        self.y=starty
        self.xt=targetx
        self.yt=targety
        self.angle=Edge(startx, starty, targetx, targety).angle
        if isHosting:
            if self.delay<=0:
                if self.click and players[self.owner].repairDelay<=0:
                    self.delay=self.maxDelay
                    muzzle=getAngledEdge(self.x, self.y, self.angle, 10)
                    newProjectile=sniperShot(muzzle.a, muzzle.b, self.xt, self.yt, self.owner)
                    projectiles.append(newProjectile)
                    broadcastImportant("spawn_projectile "+self.owner+" "+str(self.weaponIndex)+" "+str(muzzle.a)+" "+str(muzzle.b)+" "+str(self.xt)+" "+str(self.yt)+" "+str(newProjectile.id))
            else:
                self.delay-=dt

allWeapons=[]
allWeapons.append(plasmaGun)
allWeapons.append(needler)
allWeapons.append(missileLauncher)
allWeapons.append(sniper)
#endregion

#Playertypes
#region
class defaultPlayer:
    def __init__(self, x, y, name):
        #Standartvariablen
        self.nameSprite=pygame.font.Font(fontFile, 10).render(name, False, (255, 255, 255))
        self.vesselIndex=0
        self.x=x
        self.y=y
        self.name=name
        self.maxHP=500
        self.HP=0
        self.speed=200
        self.angle=0
        self.baseAngle=0
        self.collisionRadius=16
        self.curx=0
        self.cury=0
        self.lastHitBy=name
        self.old_x=0
        self.old_y=0
        self.changed=False
        self.cursorChanged=False
        #Schöneres Lenken
        self.slow_vx=0
        self.slow_vy=0
        #Referenzen auf die Waffen
        self.weaponL=plasmaGun(name)
        self.weaponR=plasmaGun(name)
        #Tasten
        self.up=False
        self.down=False
        self.left=False
        self.right=False
        self.shift=False
        self.r=False
        #Dodge-Steuervariablen
        self.dodgeVector=[0, 0]
        self.dodgeDelay=0
        self.dodgeReleased=True
        self.baseSprite=playerSprites["defaultPlayer_base"]
        self.topSprite=playerSprites["defaultPlayer_top"]
        self.turretSprite=playerSprites["defaultPlayer_turret"]
        self.score=0
        self.invDelay=0
        self.spawnDelay=0
        self.repairDelay=0
        self.old_repairDelay=0
        self.low=False
        self.old_low=False
        self.driving=0
        self.old_driving=0
    def updateCursor(self, mouseX, mouseY):
        self.curx=mouseX+camShiftX
        self.cury=mouseY+camShiftY
        self.angle=Edge(self.x, self.y, self.curx, self.cury).angle
        self.cursorChanged=True
    def draw(self, s, dt):
        if self.HP>0:
            er=getAngledEdge(self.x, self.y, self.angle+math.pi/2, 10)
            el=getAngledEdge(self.x, self.y, self.angle-math.pi/2, 10)

            if isOnScreen(self.x, self.y, border=self.collisionRadius):
                drawCentered(s, self.baseSprite, self.x-camShiftX, self.y-camShiftY+5, self.baseAngle)
                drawCentered(s, self.topSprite, self.x-camShiftX, self.y-camShiftY, self.baseAngle)
                drawCentered(s, self.turretSprite, self.x-camShiftX, self.y-camShiftY, self.angle)
                self.weaponR.draw(s)
                self.weaponL.draw(s)
                #Repairkreis
                pygame.draw.arc(s, (200, 200, 200), ((self.x-camShiftX-30, self.y-camShiftY-30), (60, 60)), math.pi/2, math.pi/2-math.pi*2*(1-self.repairDelay), width=3)
                #Lebensbalken
                lx=self.x-29
                ly=self.y-29
                if map.getBlock(int(lx/map.blocksize), int(ly/map.blocksize))!=0:
                    ly=int(self.y/map.blocksize)*map.blocksize
                pygame.draw.rect(s, (255, 255, 255), ((lx-camShiftX, ly-camShiftY), (60, 8)), 0)
                if self.HP<self.maxHP*0.33:
                    if not self.low:
                        self.low=True
                    pygame.draw.rect(s, (200, 100, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                else:
                    if self.low:
                        self.low=False
                    pygame.draw.rect(s, (100, 200, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                for i in range(0, self.maxHP, 100):
                    pos=int(i/self.maxHP*60)
                    pygame.draw.line(s, (255, 255, 255), (lx+pos-camShiftX, ly-camShiftY+1), (lx+pos-camShiftX, ly-camShiftY+6), 1)
                #Spielername
                if name!=self.name:
                    ly=self.y+30
                    if map.getBlock(int(self.x/map.blocksize), int(ly/map.blocksize))!=0:
                        ly=int(self.y/map.blocksize)*map.blocksize+map.blocksize/2
                    drawCentered(s, self.nameSprite, self.x-camShiftX, ly-camShiftY, 0)
                #Lichtkreis
                if not noRadarRequired and self.name==name:
                    pygame.draw.circle(lightSurface, (255, 255, 255), (int(self.x-camShiftX), int(self.y-camShiftY)), self.collisionRadius*3, 0)
            #Waffen
            #region
            self.weaponL.update(dt, er.a, er.b, self.curx, self.cury)
            self.weaponR.update(dt, el.a, el.b, self.curx, self.cury)
            #endregion
            self.doRepairing(dt)
            self.doPlayerCollision(dt)
            self.doMapCollision(dt)
            self.doMovement(dt)
        self.doRespawning(dt)
        self.doLowWarning(dt)
        self.detectMovement(dt)
    def damage(self, amount, sx, sy, owner):
        if amount>=0:
            self.lastHitBy=owner
        self.HP-=amount
        self.HP=clamp(self.HP, 0, self.maxHP)
        if self.HP==0:
            splashAngle=Edge(sx, sy, self.x, self.y).angle
            particles.append(explosion(self.x, self.y, 0))
            particles.append(directionalExplosion(self.x, self.y, splashAngle))
            for i in range(20):
                particles.append(deathWaste(self.x, self.y, splashAngle+0.01*random.randint(-40, 40)))
            if isHosting:
                self.spawnDelay=3
                broadcastImportant("death "+self.name+" "+self.lastHitBy)
    def doRepairing(self, dt):
        #Reparieranimation
        #region
        if self.r:
            if self.repairDelay<1:
                self.repairDelay+=dt
        else:
            if self.repairDelay>0:
                self.repairDelay-=dt
        #unten gehts weiter
        #Repariersounds
        if self.name==name:
            if self.repairDelay>=1 and self.old_repairDelay<1:
                repairLoop.play(loops=5, fade_ms=100)
            if self.repairDelay<1 and self.old_repairDelay>=1:
                repairLoop.fadeout(100)
        #endregion
        if isHosting:
            #Reparatur umsetzen
            if self.repairDelay>=1:
                self.damage(-150*dt, self.x, self.y, self.name)
                #apply_damage WEM VON_WEM SCHADEN QUELLE_X QUELLE_Y
                broadcastImportant("apply_damage "+self.name+" "+self.name+" "+str(-150*dt)+" "+str(self.x)+" "+str(self.y))
    def doPlayerCollision(self, dt):
        if isHosting:
            #Kollision mit Spielern
            #region
            for cn in players:
                otherPlayer=players[cn]
                tmp=abst(self.x, self.y, otherPlayer.x, otherPlayer.y)
                if tmp<self.collisionRadius + otherPlayer.collisionRadius and otherPlayer.HP>0:
                    self.x+=(self.x-otherPlayer.x)*3*dt
                    self.y+=(self.y-otherPlayer.y)*3*dt
            #endregion
    def doMapCollision(self, dt):
        #Kollision mit Map
        if isHosting:
            nearest=edges.copy()
            nearest.sort(key=lambda e: getDistanceToEdge(self.x, self.y, e))
            nearest=nearest[:2]
            for edge in nearest:
                ax, ay=getNearestPoint(self.x, self.y, edge)
                tmp=abst(self.x, self.y, ax, ay)
                if tmp<self.collisionRadius:
                    self.x+=(self.x-ax)/tmp*(self.collisionRadius-tmp)
                    self.y+=(self.y-ay)/tmp*(self.collisionRadius-tmp)
    def doMovement(self, dt):
        if isHosting:
            #Bewegung
            #region
            #Nur wenn man sich nicht gerade repariert.
            if self.repairDelay<=0:
                vx=0
                vy=0
                if self.up:
                    vy-=1
                if self.down:
                    vy+=1
                if self.left:
                    vx-=1
                if self.right:
                    vx+=1
                if vx!=0 and vy!=0:
                    tmp=abst(0, 0, vx, vy)
                    vx/=tmp
                    vy/=tmp
                if self.shift and self.dodgeDelay==0 and self.dodgeReleased and (vx!=0 or vy!=0):
                    dodgeAngle=Edge(0, 0, vx, vy).angle
                    particles.append(dodgeParticle(self.x, self.y, dodgeAngle))
                    broadcast("spawn_particle 3 "+str(self.x)+" "+str(self.y)+" "+str(dodgeAngle))
                    self.dodgeVector=[vx, vy]
                    self.dodgeDelay=1
                if self.dodgeDelay>0.8:
                    #Dodgen
                    self.x+=self.dodgeVector[0]*self.speed*2.5*dt
                    self.y+=self.dodgeVector[1]*self.speed*2.5*dt
                    if self.dodgeVector[0]!=0 or self.dodgeVector[1]!=0:
                        self.slow_vx+=(self.dodgeVector[0]-self.slow_vx)*10*dt
                        self.slow_vy+=(self.dodgeVector[1]-self.slow_vy)*10*dt
                else:
                    #Normal bewegen
                    self.x+=vx*self.speed*dt
                    self.y+=vy*self.speed*dt
                    if vx!=0 or vy!=0:
                        self.slow_vx+=(vx-self.slow_vx)*10*dt
                        self.slow_vy+=(vy-self.slow_vy)*10*dt
                if self.dodgeDelay>0:
                    self.dodgeDelay=max(0, self.dodgeDelay-dt)
                if self.dodgeReleased==False and self.shift==False:
                    self.dodgeReleased=True
                self.baseAngle=Edge(self.x, self.y, self.x+self.slow_vx, self.y+self.slow_vy).angle
            #endregion
    def doRespawning(self, dt):
        #Respawnen
        #region
        if isHosting:
            if self.spawnDelay>0:
                self.spawnDelay-=dt
            else:
                if self.HP==0:
                    self.HP=self.maxHP
                    x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                    y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    while not isValidSpawnPoint(x, y):
                        x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                        y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    self.x=x
                    self.y=y
                    self.invDelay=4
                    broadcastImportant("spawn "+self.name+" "+str(x)+" "+str(y))
        if self.invDelay>0:
            self.invDelay-=dt
            drawCentered(s, playerSprites["shield"], self.x-camShiftX, self.y-camShiftY, 0)
        #endregion
    def detectMovement(self, dt):
        #Playerbewegung erkennen
        #region
        if self.x==self.old_x and self.y==self.old_y and not self.cursorChanged:
            self.changed=False
        else:
            self.changed=True
        if self.cursorChanged:
            self.cursorChanged=False
        #Fahrsounds
        if self.x!=self.old_x or self.y!=self.old_y:
            self.driving=0.1
        else:
            if self.driving>0:
                self.driving-=dt
        if self.name==name:
            if self.driving>0 and self.old_driving<=0:
                defaultPlayerMoveLoop.play(loops=-1, fade_ms=200)
            if self.driving<=0 and self.old_driving>0:
                defaultPlayerMoveLoop.fadeout(200)
        self.old_driving=self.driving
        self.old_x=self.x
        self.old_y=self.y
        self.old_repairDelay=self.repairDelay
        #endregion
    def doLowWarning(self, dt):
        if self.name==name:
            if self.low and not self.old_low:
                warnLowLoop.play(loops=10, fade_ms=100)
            if not self.low and self.old_low:
                warnLowLoop.fadeout(100)
        self.old_low=self.low
class mech:
    def __init__(self, x, y, name):
        #Standartvariablen
        self.nameSprite=pygame.font.Font(fontFile, 10).render(name, False, (255, 255, 255))
        self.vesselIndex=1
        self.x=x
        self.y=y
        self.name=name
        self.maxHP=700
        self.HP=0
        self.speed=100
        self.angle=0
        self.baseAngle=0
        self.collisionRadius=16
        self.curx=0
        self.cury=0
        self.lastHitBy=name
        self.old_x=0
        self.old_y=0
        self.changed=False
        self.cursorChanged=False
        #Schöneres Lenken
        self.slow_vx=0
        self.slow_vy=0
        #Referenzen auf die Waffen
        self.weaponL=plasmaGun(name)
        self.weaponR=plasmaGun(name)
        #Tasten
        #region
        self.up=False
        self.down=False
        self.left=False
        self.right=False
        self.shift=False
        self.r=False
        #endregion
        #Dodge-Steuervariablen
        #region
        self.dodgeVector=[0, 0]
        self.dodgeDelay=0
        self.dodgeReleased=True
        self.baseSprite=playerSprites["mech_base"]
        self.topSprite=playerSprites["mech_top"]
        self.turretSprite=playerSprites["mech_turret"]
        self.score=0
        self.invDelay=0
        self.spawnDelay=0
        self.repairDelay=0
        self.old_repairDelay=0
        self.low=False
        self.old_low=False
        #endregion
        #Laufanimation
        #region
        self.walking=0
        self.old_walking=0
        self.animationCounter=0
        self.frames=22
        #endregion
    def updateCursor(self, mouseX, mouseY):
        self.curx=mouseX+camShiftX
        self.cury=mouseY+camShiftY
        self.angle=Edge(self.x, self.y, self.curx, self.cury).angle
        self.cursorChanged=True
    def draw(self, s, dt):
        if self.HP>0:
            er=getAngledEdge(self.x, self.y, self.angle+math.pi/2, 15)
            el=getAngledEdge(self.x, self.y, self.angle-math.pi/2, 15)

            if isOnScreen(self.x, self.y, border=self.collisionRadius):
                if self.walking>0:
                    drawCentered(s, mechWalkSprites[int(self.animationCounter*22)], self.x-camShiftX, self.y-camShiftY+5, self.baseAngle)
                else:
                    drawCentered(s, self.baseSprite, self.x-camShiftX, self.y-camShiftY+5, self.baseAngle)
                self.animationCounter+=dt
                if self.animationCounter>=1:
                    self.animationCounter=0
                drawCentered(s, self.topSprite, self.x-camShiftX, self.y-camShiftY, self.baseAngle)
                self.weaponR.draw(s)
                self.weaponL.draw(s)
                drawCentered(s, self.turretSprite, self.x-camShiftX, self.y-camShiftY, self.angle)
                #Repairkreis
                pygame.draw.arc(s, (200, 200, 200), ((self.x-camShiftX-30, self.y-camShiftY-30), (60, 60)), math.pi/2, math.pi/2-math.pi*2*(1-self.repairDelay), width=3)
                #Lebensbalken
                lx=self.x-29
                ly=self.y-29
                if map.getBlock(int(lx/map.blocksize), int(ly/map.blocksize))!=0:
                    ly=int(self.y/map.blocksize)*map.blocksize
                pygame.draw.rect(s, (255, 255, 255), ((lx-camShiftX, ly-camShiftY), (60, 8)), 0)
                if self.HP<self.maxHP*0.33:
                    if not self.low:
                        self.low=True
                    pygame.draw.rect(s, (200, 100, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                else:
                    if self.low:
                        self.low=False
                    pygame.draw.rect(s, (100, 200, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                for i in range(0, self.maxHP, 100):
                    pos=int(i/self.maxHP*60)
                    pygame.draw.line(s, (255, 255, 255), (lx+pos-camShiftX, ly-camShiftY+1), (lx+pos-camShiftX, ly-camShiftY+6), 1)
                #Spielername
                if name!=self.name:
                    ly=self.y+30
                    if map.getBlock(int(self.x/map.blocksize), int(ly/map.blocksize))!=0:
                        ly=int(self.y/map.blocksize)*map.blocksize+map.blocksize/2
                    drawCentered(s, self.nameSprite, self.x-camShiftX, ly-camShiftY, 0)
                #Lichtkreis
                if not noRadarRequired and self.name==name:
                    pygame.draw.circle(lightSurface, (255, 255, 255), (int(self.x-camShiftX), int(self.y-camShiftY)), self.collisionRadius*3, 0)
            self.doRepairing(dt)
            self.doPlayerCollision(dt)
            self.doMapCollision(dt)
            self.doMovement(dt)
            #Waffen
            #region
            self.weaponL.update(dt, er.a, er.b, self.curx, self.cury)
            self.weaponR.update(dt, el.a, el.b, self.curx, self.cury)
            #endregion
        self.doRespawning(dt)
        self.doLowWarning(dt)
        self.detectMovement(dt)
    def damage(self, amount, sx, sy, owner):
        if amount>=0:
            self.lastHitBy=owner
        self.HP-=amount
        self.HP=clamp(self.HP, 0, self.maxHP)
        if self.HP==0:
            splashAngle=Edge(sx, sy, self.x, self.y).angle
            particles.append(explosion(self.x, self.y, 0))
            particles.append(directionalExplosion(self.x, self.y, splashAngle))
            for i in range(20):
                particles.append(deathWaste(self.x, self.y, splashAngle+0.01*random.randint(-40, 40)))
            if isHosting:
                self.spawnDelay=3
                broadcastImportant("death "+self.name+" "+self.lastHitBy)
    def doRepairing(self, dt):
        #Reparieranimation
        #region
        if self.r:
            if self.repairDelay<1:
                self.repairDelay+=dt
        else:
            if self.repairDelay>0:
                self.repairDelay-=dt
        if self.repairDelay>=1 and self.old_repairDelay<1:
            repairLoop.play(loops=5, fade_ms=100)
        if self.repairDelay<1 and self.old_repairDelay>=1:
            repairLoop.fadeout(100)
        #unten gehts weiter
        #endregion
        if isHosting:
            #Reparatur umsetzen
            if self.repairDelay>=1:
                self.damage(-150*dt, self.x, self.y, self.name)
                #apply_damage WEM VON_WEM SCHADEN QUELLE_X QUELLE_Y
                broadcastImportant("apply_damage "+self.name+" "+self.name+" "+str(-150*dt)+" "+str(self.x)+" "+str(self.y))
    def doPlayerCollision(self, dt):
        if isHosting:
            #Kollision mit Spielern
            #region
            for cn in players:
                otherPlayer=players[cn]
                tmp=abst(self.x, self.y, otherPlayer.x, otherPlayer.y)
                if tmp<self.collisionRadius + otherPlayer.collisionRadius and otherPlayer.HP>0:
                    self.x+=(self.x-otherPlayer.x)*3*dt
                    self.y+=(self.y-otherPlayer.y)*3*dt
            #endregion
    def doMapCollision(self, dt):
        #Kollision mit Map
        if isHosting:
            nearest=edges.copy()
            nearest.sort(key=lambda e: getDistanceToEdge(self.x, self.y, e))
            nearest=nearest[:2]
            for edge in nearest:
                ax, ay=getNearestPoint(self.x, self.y, edge)
                tmp=abst(self.x, self.y, ax, ay)
                if tmp<self.collisionRadius:
                    self.x+=(self.x-ax)/tmp*(self.collisionRadius-tmp)
                    self.y+=(self.y-ay)/tmp*(self.collisionRadius-tmp)
    def doMovement(self, dt):
        if isHosting:
            #Bewegung
            #region
            #Nur wenn man sich nicht gerade repariert.
            if self.repairDelay<=0:
                vx=0
                vy=0
                if self.up:
                    vy-=1
                if self.down:
                    vy+=1
                if self.left:
                    vx-=1
                if self.right:
                    vx+=1
                if vx!=0 and vy!=0:
                    tmp=abst(0, 0, vx, vy)
                    vx/=tmp
                    vy/=tmp
                if self.shift and self.dodgeDelay==0 and self.dodgeReleased and (vx!=0 or vy!=0):
                    dodgeAngle=Edge(0, 0, vx, vy).angle
                    particles.append(dodgeParticle(self.x, self.y, dodgeAngle))
                    broadcast("spawn_particle 3 "+str(self.x)+" "+str(self.y)+" "+str(dodgeAngle))
                    self.dodgeVector=[vx, vy]
                    self.dodgeDelay=2
                if self.dodgeDelay>1.0:
                    #Dodgen
                    self.x+=self.dodgeVector[0]*self.speed*2.5*dt
                    self.y+=self.dodgeVector[1]*self.speed*2.5*dt
                    if self.dodgeVector[0]!=0 or self.dodgeVector[1]!=0:
                        self.slow_vx+=(self.dodgeVector[0]-self.slow_vx)*10*dt
                        self.slow_vy+=(self.dodgeVector[1]-self.slow_vy)*10*dt
                else:
                    #Normal bewegen
                    self.x+=vx*self.speed*dt
                    self.y+=vy*self.speed*dt
                    if vx!=0 or vy!=0:
                        self.slow_vx+=(vx-self.slow_vx)*10*dt
                        self.slow_vy+=(vy-self.slow_vy)*10*dt
                if self.dodgeDelay>0:
                    self.dodgeDelay=max(0, self.dodgeDelay-dt)
                if self.dodgeReleased==False and self.shift==False:
                    self.dodgeReleased=True
                self.baseAngle=Edge(self.x, self.y, self.x+self.slow_vx, self.y+self.slow_vy).angle
            #endregion
    def doRespawning(self, dt):
        #Respawnen
        #region
        if isHosting:
            if self.spawnDelay>0:
                self.spawnDelay-=dt
            else:
                if self.HP==0:
                    self.HP=self.maxHP
                    x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                    y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    while not isValidSpawnPoint(x, y):
                        x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                        y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    self.x=x
                    self.y=y
                    self.invDelay=4
                    broadcastImportant("spawn "+self.name+" "+str(x)+" "+str(y))
        if self.invDelay>0:
            self.invDelay-=dt
            drawCentered(s, playerSprites["shield"], self.x-camShiftX, self.y-camShiftY, 0)
        #endregion
    def detectMovement(self, dt):
        #Bewgungserkennung
        #region
        if self.x==self.old_x and self.y==self.old_y and not self.cursorChanged:
            self.changed=False
        else:
            self.changed=True
        if self.cursorChanged:
            self.cursorChanged=False
        #endregion
        #Playerbewegung erkennen
        #Walking
        #region
        if self.x!=self.old_x or self.y!=self.old_y:
            self.walking=0.1
        else:
            if self.walking>0:
                self.walking-=dt
        if self.name==name:
            if self.walking>0 and self.old_walking<=0:
                mechWalkLoop.play(loops=-1, fade_ms=100)
            if self.walking<=0 and self.old_walking>0:
                mechWalkLoop.fadeout(100)
        self.old_x=self.x
        self.old_y=self.y
        self.old_walking=self.walking
        self.old_repairDelay=self.repairDelay
        #endregion
    def doLowWarning(self, dt):
        if self.name==name:
            if self.low and not self.old_low:
                warnLowLoop.play(loops=10, fade_ms=100)
            if not self.low and self.old_low:
                warnLowLoop.fadeout(100)
        self.old_low=self.low
class assel:
    def __init__(self, x, y, name):
        #Standartvariablen
        self.nameSprite=pygame.font.Font(fontFile, 10).render(name, False, (255, 255, 255))
        self.vesselIndex=1
        self.x=x
        self.y=y
        self.name=name
        self.maxHP=300
        self.HP=0
        self.speed=250
        self.angle=0
        self.baseAngle=0
        self.collisionRadius=16
        self.curx=0
        self.cury=0
        self.lastHitBy=name
        self.old_x=0
        self.old_y=0
        self.changed=False
        self.cursorChanged=False
        #Schöneres Lenken
        self.slow_vx=0
        self.slow_vy=0
        #Referenzen auf die Waffen
        self.weaponL=plasmaGun(name)
        self.weaponR=plasmaGun(name)
        #Tasten
        #region
        self.up=False
        self.down=False
        self.left=False
        self.right=False
        self.shift=False
        self.r=False
        #endregion
        #Dodge-Steuervariablen
        #region
        self.dodgeVector=[0, 0]
        self.dodgeDelay=0
        self.dodgeReleased=True
        self.baseSprite=playerSprites["assel_base"]
        self.topSprite=None
        self.turretSprite=playerSprites["assel_turret"]
        self.score=0
        self.invDelay=0
        self.spawnDelay=0
        self.repairDelay=0
        self.old_repairDelay=0
        self.low=False
        self.old_low=False
        #endregion
        #Laufanimation
        #region
        self.walking=0
        self.old_walking=0
        self.animationCounter=0
        self.frames=22
        #endregion
    def updateCursor(self, mouseX, mouseY):
        self.curx=mouseX+camShiftX
        self.cury=mouseY+camShiftY
        self.angle=Edge(self.x, self.y, self.curx, self.cury).angle
        self.cursorChanged=True
    def draw(self, s, dt):
        if self.HP>0:
            aer=getAngledEdge(self.x, self.y, self.angle+math.pi/2, 12)
            ael=getAngledEdge(self.x, self.y, self.angle-math.pi/2, 12)
            er=getAngledEdge(aer.a, aer.b, self.angle, 10)
            el=getAngledEdge(ael.a, ael.b, self.angle, 10)

            if isOnScreen(self.x, self.y, border=self.collisionRadius):
                if self.walking>0:
                    drawCentered(s, asselWalkSprites[int(self.animationCounter*70)%8], self.x-camShiftX, self.y-camShiftY, self.baseAngle)
                    drawCentered(s, self.turretSprite, self.x-camShiftX, self.y-camShiftY, self.angle)
                else:
                    drawCentered(s, self.baseSprite, self.x-camShiftX, self.y-camShiftY, self.baseAngle)
                    drawCentered(s, asselBreatheSprites[int(self.animationCounter*6)], self.x-camShiftX, self.y-camShiftY, self.angle)
                self.animationCounter+=dt
                if self.animationCounter>=1:
                    self.animationCounter=0
                self.weaponR.draw(s)
                self.weaponL.draw(s)
                #Repairkreis
                pygame.draw.arc(s, (200, 200, 200), ((self.x-camShiftX-30, self.y-camShiftY-30), (60, 60)), math.pi/2, math.pi/2-math.pi*2*(1-self.repairDelay), width=3)
                #Lebensbalken
                lx=self.x-29
                ly=self.y-29
                if map.getBlock(int(lx/map.blocksize), int(ly/map.blocksize))!=0:
                    ly=int(self.y/map.blocksize)*map.blocksize
                pygame.draw.rect(s, (255, 255, 255), ((lx-camShiftX, ly-camShiftY), (60, 8)), 0)
                if self.HP<self.maxHP*0.33:
                    if not self.low:
                        self.low=True
                    pygame.draw.rect(s, (200, 100, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                else:
                    if self.low:
                        self.low=False
                    pygame.draw.rect(s, (100, 200, 100), ((lx-camShiftX+1, ly-camShiftY+1), (int(58*self.HP/self.maxHP), 6)), 0)
                for i in range(0, self.maxHP, 100):
                    pos=int(i/self.maxHP*60)
                    pygame.draw.line(s, (255, 255, 255), (lx+pos-camShiftX, ly-camShiftY+1), (lx+pos-camShiftX, ly-camShiftY+6), 1)
                #Spielername
                if name!=self.name:
                    ly=self.y+30
                    if map.getBlock(int(self.x/map.blocksize), int(ly/map.blocksize))!=0:
                        ly=int(self.y/map.blocksize)*map.blocksize+map.blocksize/2
                    drawCentered(s, self.nameSprite, self.x-camShiftX, ly-camShiftY, 0)
                #Lichtkreis
                if not noRadarRequired and self.name==name:
                    pygame.draw.circle(lightSurface, (255, 255, 255), (int(self.x-camShiftX), int(self.y-camShiftY)), self.collisionRadius*3, 0)
            self.doRepairing(dt)
            self.doPlayerCollision(dt)
            self.doMapCollision(dt)
            self.doMovement(dt)
            #Waffen
            #region
            self.weaponL.update(dt, er.a, er.b, self.curx, self.cury)
            self.weaponR.update(dt, el.a, el.b, self.curx, self.cury)
            #endregion
        self.doRespawning(dt)
        self.doLowWarning(dt)
        self.detectMovement(dt)
    def damage(self, amount, sx, sy, owner):
        if amount>=0:
            self.lastHitBy=owner
        self.HP-=amount
        self.HP=clamp(self.HP, 0, self.maxHP)
        if self.HP==0:
            splashAngle=Edge(sx, sy, self.x, self.y).angle
            particles.append(explosion(self.x, self.y, 0))
            particles.append(directionalExplosion(self.x, self.y, splashAngle))
            for i in range(20):
                particles.append(deathWaste(self.x, self.y, splashAngle+0.01*random.randint(-40, 40)))
            if isHosting:
                self.spawnDelay=3
                broadcastImportant("death "+self.name+" "+self.lastHitBy)
    def doRepairing(self, dt):
        #Reparieranimation
        #region
        if self.r:
            if self.repairDelay<1:
                self.repairDelay+=dt
        else:
            if self.repairDelay>0:
                self.repairDelay-=dt
        if self.repairDelay>=1 and self.old_repairDelay<1:
            repairLoop.play(loops=5, fade_ms=100)
        if self.repairDelay<1 and self.old_repairDelay>=1:
            repairLoop.fadeout(100)
        #unten gehts weiter
        #endregion
        if isHosting:
            #Reparatur umsetzen
            if self.repairDelay>=1:
                self.damage(-150*dt, self.x, self.y, self.name)
                #apply_damage WEM VON_WEM SCHADEN QUELLE_X QUELLE_Y
                broadcastImportant("apply_damage "+self.name+" "+self.name+" "+str(-150*dt)+" "+str(self.x)+" "+str(self.y))
    def doPlayerCollision(self, dt):
        if isHosting:
            #Kollision mit Spielern
            #region
            for cn in players:
                otherPlayer=players[cn]
                tmp=abst(self.x, self.y, otherPlayer.x, otherPlayer.y)
                if tmp<self.collisionRadius + otherPlayer.collisionRadius and otherPlayer.HP>0:
                    self.x+=(self.x-otherPlayer.x)*3*dt
                    self.y+=(self.y-otherPlayer.y)*3*dt
            #endregion
    def doMapCollision(self, dt):
        #Kollision mit Map
        if isHosting:
            nearest=edges.copy()
            nearest.sort(key=lambda e: getDistanceToEdge(self.x, self.y, e))
            nearest=nearest[:2]
            for edge in nearest:
                ax, ay=getNearestPoint(self.x, self.y, edge)
                tmp=abst(self.x, self.y, ax, ay)
                if tmp<self.collisionRadius:
                    self.x+=(self.x-ax)/tmp*(self.collisionRadius-tmp)
                    self.y+=(self.y-ay)/tmp*(self.collisionRadius-tmp)
    def doMovement(self, dt):
        if isHosting:
            #Bewegung
            #region
            #Nur wenn man sich nicht gerade repariert.
            if self.repairDelay<=0:
                vx=0
                vy=0
                if self.up:
                    vy-=1
                if self.down:
                    vy+=1
                if self.left:
                    vx-=1
                if self.right:
                    vx+=1
                if vx!=0 and vy!=0:
                    tmp=abst(0, 0, vx, vy)
                    vx/=tmp
                    vy/=tmp
                if self.shift and self.dodgeDelay==0 and self.dodgeReleased and (vx!=0 or vy!=0):
                    dodgeAngle=Edge(0, 0, vx, vy).angle
                    particles.append(dodgeParticle(self.x, self.y, dodgeAngle))
                    broadcast("spawn_particle 3 "+str(self.x)+" "+str(self.y)+" "+str(dodgeAngle))
                    self.dodgeVector=[vx, vy]
                    self.dodgeDelay=0.5
                if self.dodgeDelay>0.4:
                    #Dodgen
                    self.x+=self.dodgeVector[0]*self.speed*3.5*dt
                    self.y+=self.dodgeVector[1]*self.speed*3.5*dt
                    if self.dodgeVector[0]!=0 or self.dodgeVector[1]!=0:
                        self.slow_vx+=(self.dodgeVector[0]-self.slow_vx)*10*dt
                        self.slow_vy+=(self.dodgeVector[1]-self.slow_vy)*10*dt
                else:
                    #Normal bewegen
                    self.x+=vx*self.speed*dt
                    self.y+=vy*self.speed*dt
                    if vx!=0 or vy!=0:
                        self.slow_vx+=(vx-self.slow_vx)*10*dt
                        self.slow_vy+=(vy-self.slow_vy)*10*dt
                if self.dodgeDelay>0:
                    self.dodgeDelay=max(0, self.dodgeDelay-dt)
                if self.dodgeReleased==False and self.shift==False:
                    self.dodgeReleased=True
                self.baseAngle=Edge(self.x, self.y, self.x+self.slow_vx, self.y+self.slow_vy).angle
            #endregion
    def doRespawning(self, dt):
        #Respawnen
        #region
        if isHosting:
            if self.spawnDelay>0:
                self.spawnDelay-=dt
            else:
                if self.HP==0:
                    self.HP=self.maxHP
                    x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                    y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    while not isValidSpawnPoint(x, y):
                        x=random.randint(1, map.width-1)*map.blocksize+map.blocksize/2
                        y=random.randint(1, map.height-1)*map.blocksize+map.blocksize/2
                    self.x=x
                    self.y=y
                    self.invDelay=4
                    broadcastImportant("spawn "+self.name+" "+str(x)+" "+str(y))
        if self.invDelay>0:
            self.invDelay-=dt
            drawCentered(s, playerSprites["shield"], self.x-camShiftX, self.y-camShiftY, 0)
        #endregion
    def detectMovement(self, dt):
        #Bewgungserkennung
        #region
        if self.x==self.old_x and self.y==self.old_y and not self.cursorChanged:
            self.changed=False
        else:
            self.changed=True
        if self.cursorChanged:
            self.cursorChanged=False
        #endregion
        #Playerbewegung erkennen
        #Walking
        #region
        if self.x!=self.old_x or self.y!=self.old_y:
            self.walking=0.1
        else:
            if self.walking>0:
                self.walking-=dt
        if self.name==name:
            if self.walking>0 and self.old_walking<=0:
                #mechWalkLoop.play(loops=-1, fade_ms=100)
                pass
            if self.walking<=0 and self.old_walking>0:
                #mechWalkLoop.fadeout(100)
                pass
        self.old_x=self.x
        self.old_y=self.y
        self.old_walking=self.walking
        self.old_repairDelay=self.repairDelay
        #endregion
    def doLowWarning(self, dt):
        if self.name==name:
            if self.low and not self.old_low:
                warnLowLoop.play(loops=10, fade_ms=100)
            if not self.low and self.old_low:
                warnLowLoop.fadeout(100)
        self.old_low=self.low
allVessels=[]
allVessels.append(defaultPlayer)
allVessels.append(mech)
allVessels.append(assel)
#endregion

#Partikel
#region
class directionalExplosion:
    def __init__(self, x, y, angle):
        random.choice(explosionSounds).play()
        self.x=x
        self.y=y
        self.angle=angle
        self.lifetime=16/24
        edge=getAngledEdge(x, y, angle, 1)
        self.vx=edge.a-edge.x
        self.vy=edge.b-edge.y
    def draw(self, s, dt):
        if isOnScreen(self.x, self.y):
            drawCentered(s, particleSprites["directionalExplosion"][int(16-self.lifetime*24)], self.x-camShiftX, self.y-camShiftY, self.angle-math.pi)
        self.lifetime-=dt
class explosion:
    def __init__(self, x, y, angle):
        self.x=x
        self.y=y
        self.angle=angle
        self.lifetime=16/24
        edge=getAngledEdge(x, y, angle, 1)
        self.vx=edge.a-edge.x
        self.vy=edge.b-edge.y
    def draw(self, s, dt):
        if isOnScreen(self.x, self.y):
            drawCentered(s, particleSprites["explosion"][int(16-self.lifetime*24)], self.x-camShiftX, self.y-camShiftY, self.angle)
            pygame.draw.circle(lightSurface, (255, 255, 255), (self.x-camShiftX, self.y-camShiftY), 50*math.sin(self.lifetime/(16/24)*math.pi))
        self.lifetime-=dt
class deathWaste:
    def __init__(self, x, y, angle):
        self.x=x
        self.y=y
        self.angle=angle
        self.lifetime=random.randint(1, 5)
        self.sprite=random.choice(particleSprites["deathWaste"])
        edge=getAngledEdge(x, y, angle, 1)
        self.vx=edge.a-edge.x
        self.vy=edge.b-edge.y
        self.speed=float(random.randint(100, 300))
        self.angularSpeed=math.radians(random.randint(0, 1000))
    def draw(self, s, dt):
        if isOnScreen(self.x, self.y):
            drawCentered(s, self.sprite, self.x-camShiftX, self.y-camShiftY, self.angle)
        travel=Edge(self.x, self.y, self.x+self.vx*dt*self.speed, self.y+self.vy*dt*self.speed)
        for edge in edges:
            a, ax, ay=edgeIntersection(travel, edge)
            if a:
                self.x=ax
                self.y=ay
                self.angle=edge.angle-(travel.angle-edge.angle)
                self.angularSpeed=math.radians(random.randint(0, 1000))
                newTravel=getAngledEdge(ax, ay, self.angle, 0.2)
                self.x=newTravel.a
                self.y=newTravel.b
                newTravel=getAngledEdge(self.x, self.y, self.angle, 1)
                self.vx=newTravel.a-newTravel.x
                self.vy=newTravel.b-newTravel.y
                break
        self.x+=self.vx*dt*self.speed
        self.y+=self.vy*dt*self.speed
        self.angle+=self.angularSpeed*dt
        if self.angularSpeed>0:
            self.angularSpeed-=10*dt
        if self.speed>0:
            self.speed-=dt*50
        self.lifetime-=dt
class dodgeParticle:
    def __init__(self, x, y, angle):
        random.choice(dodgeSounds).play()
        self.x=x
        self.y=y
        self.angle=angle
        self.lifetime=58/24
        edge=getAngledEdge(x, y, angle, 1)
        self.vx=edge.a-edge.x
        self.vy=edge.b-edge.y
    def draw(self, s, dt):
        if isOnScreen(self.x, self.y):
            drawCentered(s, particleSprites["dodge"][int(58-self.lifetime*24)], self.x-camShiftX, self.y-camShiftY, self.angle)
            pygame.draw.circle(lightSurface, (255, 255, 255), (int(self.x-camShiftX), int(self.y-camShiftY)), 50, 0)
        self.lifetime-=dt

allParticles=[directionalExplosion, explosion, deathWaste, dodgeParticle]
#endregion

sTop=Edge(0, 0, width, 0)
sBottom=Edge(0, height, width, height)
sLeft=Edge(0, 0, 0, height)
sRight=Edge(width, 0, width, height)

edges=[]

try:
    os.chdir("D:/Programme_und_Coding/Python/LANGame")
except Exception as e:
    print("------")
    print(e)
    print("Konnte Ordner nicht finden!")

#Resourcen
#region

curPath=os.getcwd()
curPath="."

#Sprites
#default Player
playerSprites={"defaultPlayer_base":pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'defaultPlayer_base.png')).convert_alpha()}
playerSprites["defaultPlayer_top"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'defaultPlayer_top.png')).convert_alpha()
playerSprites["defaultPlayer_turret"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'defaultPlayer_turret.png')).convert_alpha()

playerSprites["shield"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'shield.png')).convert_alpha()

#Mech
playerSprites["mech_base"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'mech_base.png')).convert_alpha()
playerSprites["mech_top"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'mech_top.png')).convert_alpha()
playerSprites["mech_turret"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'mech_turret.png')).convert_alpha()

mechWalkSprites=[]
for i in os.listdir(os.path.join(curPath, "Sprites", "playerSprites", "mech_walking")):
    mechWalkSprites.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'mech_walking', i)).convert_alpha())

#Assel
playerSprites["assel_base"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'assel_base.png')).convert_alpha()
playerSprites["assel_turret"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'assel_turret.png')).convert_alpha()

asselWalkSprites=[]
for i in os.listdir(os.path.join(curPath, "Sprites", "playerSprites", "assel_walking")):
    asselWalkSprites.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'assel_walking', i)).convert_alpha())

asselBreatheSprites=[]
for i in os.listdir(os.path.join(curPath, "Sprites", "playerSprites", "assel_breathing")):
    asselBreatheSprites.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'playerSprites', 'assel_breathing', i)).convert_alpha())


gunSprites={}
gunSprites["plasmaGun"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'plasmaGun.png')).convert_alpha()
gunSprites["needler"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'needler.png')).convert_alpha()
gunSprites["shotgun"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'shotgun.png')).convert_alpha()
gunSprites["sniper"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'sniper.png')).convert_alpha()
gunSprites["grenadeLauncher"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'grenadelauncher.png')).convert_alpha()
gunSprites["missileLauncher"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'gunSprites', 'missilelauncher.png')).convert_alpha()

projectileSprites={}
projectileSprites["plasmaBall"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'projectileSprites', 'plasmaBall.png')).convert_alpha()
projectileSprites["needle"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'projectileSprites', 'needle.png')).convert_alpha()
projectileSprites["grenade"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'projectileSprites', 'grenade.png')).convert_alpha()
projectileSprites["missile"]=pygame.image.load(os.path.join(curPath, 'Sprites', 'projectileSprites', 'missile.png')).convert_alpha()

particleSprites={}
particleSprites["directionalExplosion"]=[]
for i in os.listdir(os.path.join(curPath, 'Sprites', 'particleSprites', 'directionalExplosion')):
    particleSprites["directionalExplosion"].append(pygame.image.load(os.path.join('Sprites', 'particleSprites', 'directionalExplosion', i)).convert_alpha())

particleSprites["explosion"]=[]
for i in os.listdir(os.path.join(curPath, 'Sprites', 'particleSprites', 'explosion')):
    particleSprites["explosion"].append(pygame.image.load(os.path.join('Sprites', 'particleSprites', 'explosion', i)).convert_alpha())

particleSprites["deathWaste"]=[]
for i in os.listdir(os.path.join(curPath, 'Sprites', 'particleSprites', 'deathWaste')):
    particleSprites["deathWaste"].append(pygame.image.load(os.path.join('Sprites', 'particleSprites', 'deathWaste', i)).convert_alpha())

particleSprites["dodge"]=[]
for i in os.listdir(os.path.join(curPath, 'Sprites', 'particleSprites', 'dodge')):
    particleSprites["dodge"].append(pygame.image.load(os.path.join('Sprites', 'particleSprites', 'dodge', i)).convert_alpha())

cursorImage=pygame.image.load(os.path.join(curPath, 'Sprites', 'cursor.png')).convert_alpha()

icons=[]
icons.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'Icons', 'tank_icon.png')).convert_alpha())#0
icons.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'Icons', 'mech_icon.png')).convert_alpha())#1
icons.append(pygame.image.load(os.path.join(curPath, 'Sprites', 'Icons', 'assel_icon.png')).convert_alpha())#2

weaponIcons=[]
weaponIcons.append(gunSprites["plasmaGun"])#0
weaponIcons.append(gunSprites["needler"])#1
weaponIcons.append(gunSprites["missileLauncher"])#2
weaponIcons.append(gunSprites["sniper"])#3

#Sounds
explosionSounds=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Explosion")):
    pass
    explosionSounds.append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Explosion", i)))

needleSounds=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Weapon", "Needler", "Collision")):
    needleSounds.append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Weapon", "Needler", "Collision", i)))

dodgeSounds=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Move", "Dodge")):
    dodgeSounds.append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Move", "Dodge", i)))

gunSounds={}
gunSounds["Needler"]=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Weapon", "Needler", "Shoot")):
    gunSounds["Needler"].append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Weapon", "Needler", "Shoot", i)))

gunSounds["missileLauncher"]=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Weapon", "Missilelauncher", "Shoot")):
    gunSounds["missileLauncher"].append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Weapon", "Missilelauncher", "Shoot", i)))

gunSounds["sniper"]=[]
for i in os.listdir(os.path.join(curPath, "Sounds", "Weapon", "Sniper", "Shoot")):
    gunSounds["sniper"].append(pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Weapon", "Sniper", "Shoot", i)))

mechWalkLoop=pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Move", "mechMoveLoop.wav"))
defaultPlayerMoveLoop=pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Move", "defaultPlayerMoveLoop.ogg"))

repairLoop=pygame.mixer.Sound(os.path.join(curPath, "Sounds", "repairLoop.ogg"))

warnLowLoop=pygame.mixer.Sound(os.path.join(curPath, "Sounds", "warnLowLoop.wav"))

targetSound=pygame.mixer.Sound(os.path.join(curPath, "Sounds", "Weapon", "Missilelauncher", "targeted.ogg"))

#Font
fontFile=pygame.font.get_default_font()


#endregion

#Globale Variablen
#region
map=Map("map.txt", 40)
edges=map.getEdges()

players={}
players[name]=defaultPlayer(150, 150, name)
players[name].HP=10
players["Fripy"]=assel(50, 50, "Fripy")
players["Fripy"].HP=players["Fripy"].maxHP

projectiles=[]

particles=[]

camShiftX=0
camShiftY=0

t=time.time()
old_t=t
#endregion

#Licht
#region

def getViewBeams(allEdges, sx, sy):
    beams=list()
    edges=allEdges.copy()
    #edges.sort(key=lambda e: getDistanceToEdge(sx, sy, e))
    #edges=edges[:20]
    d=0.0001
    e=0
    n1=getAngledEdge(sx, sy, players[name].angle+math.radians(35), 3000)
    n2=getAngledEdge(sx, sy, players[name].angle+math.radians(325), 3000)
    while e<len(edges):
        a, ax, ay=edgeIntersection(n1, edges[e])
        b, bx, by=edgeIntersection(n2, edges[e])
        cx, cy=getNearestPoint(sx, sy, edges[e])
        w=abs(Edge(sx, sy, cx, cy).angle-players[name].angle)
        if not a and not b and w>math.radians(35) and w<math.radians(325) or not isOnScreen(cx, cy):
            edges.pop(e)
        else:
            e+=1
    for edge in edges:
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.x, edge.y).angle, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.x, edge.y).angle+d, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.x, edge.y).angle-d, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.a, edge.b).angle, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.a, edge.b).angle+d, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
        n=getAngledEdge(sx, sy, Edge(sx, sy, edge.a, edge.b).angle-d, 3000)
        for i in edges:
            a, x, y=edgeIntersection(n, i)
            if a:
                tmp=abst(n.x, n.y, x, y)
                if tmp<n.length:
                    n.a=x
                    n.b=y
                    n.length=tmp
        beams.append(n)
    #Sichtbereich
    n=n1
    for i in edges:
        a, x, y=edgeIntersection(n, i)
        if a:
            tmp=abst(n.x, n.y, x, y)
            if tmp<n.length:
                n.a=x
                n.b=y
                n.length=tmp
    beams.append(n)
    n=n2
    for i in edges:
        a, x, y=edgeIntersection(n, i)
        if a:
            tmp=abst(n.x, n.y, x, y)
            if tmp<n.length:
                n.a=x
                n.b=y
                n.length=tmp
    beams.append(n)
    e=0
    while e<len(beams):
        if abs(players[name].angle-beams[e].angle)>math.radians(36) and abs(players[name].angle-beams[e].angle)<math.radians(324):
            beams.pop(e)
        else:
            e+=1
    beams.sort(key=lambda x: beamSortCrit(sx, sy, x))
    return beams

def drawViewPolygon(s, beams):
    for e in range(len(beams)-1):
        nextBeam=beams[(e+1)]
        pygame.draw.polygon(s, (255, 255, 255), ((int(beams[e].x-camShiftX), int(beams[e].y-camShiftY)), (int(beams[e].a-camShiftX), int(beams[e].b-camShiftY)), (int(nextBeam.a-camShiftX), int(nextBeam.b-camShiftY))))

def beamSortCrit(sx, sy, beam):
    start=getAngledEdge(sx, sy, players[name].angle+math.degrees(35), 1)
    normed=getAngledEdge(sx, sy, beam.angle, 1)
    return abst(start.a, start.b, normed.a, normed.b)

lightSurface=pygame.Surface((width, height))
lightSurface.set_colorkey((255, 255, 255))


#endregion

#Threads starten
if isHosting:
    oz.start(host)
else:
    oz.start(client)
    join()

class PlayerMenu:
    def __init__(self):
        self.changed=False
        self.weaponIndexL=0
        self.weaponIndexR=0
        self.vesselIndex=0
        self.pointingAt=0
    def changePlayer(self):
        if isHosting:
            cp=players[name]
            newVessel=allVessels[self.vesselIndex](cp.x, cp.y, name)
            newVessel.HP=min(cp.HP, newVessel.maxHP)
            newVessel.score=cp.score
            newVessel.weaponL=allWeapons[self.weaponIndexL](name)
            newVessel.weaponR=allWeapons[self.weaponIndexR](name)
            players[name]=newVessel
            broadcastImportant("change_vessel "+name+" "+str(self.vesselIndex))
            broadcastImportant("change_weapon_r "+name+" "+str(self.weaponIndexR))
            broadcastImportant("change_weapon_l "+name+" "+str(self.weaponIndexL))
        else:
            oz.sendImportant("wants_change_vessel "+name+" "+str(self.vesselIndex), SERVER_IP, SERVER_PORT)
            oz.sendImportant("wants_change_weapon_r "+name+" "+str(self.weaponIndexR), SERVER_IP, SERVER_PORT)
            oz.sendImportant("wants_change_weapon_l "+name+" "+str(self.weaponIndexL), SERVER_IP, SERVER_PORT)
        warnLowLoop.stop()
    def draw(self):
        pygame.draw.rect(s, (0, 0, 0), ((width/5, height/5), (width*3/5, height*3/5)), 0)
        pygame.draw.rect(s, (255, 255, 255), ((width/5, height/5), (width*3/5, height*3/5)), 2)
        #Mitte
        drawCentered(s, icons[self.vesselIndex], width/2, height/2, 0)
        if self.pointingAt==1:
            pygame.draw.rect(s, (255, 255, 255), ((width/2-25, height/2-25), (50, 50)), 2)
        #Links
        drawCentered(s, weaponIcons[self.weaponIndexL], width/4, height/2, 0)
        if self.pointingAt==0:
            pygame.draw.rect(s, (255, 255, 255), ((width/4-20, height/2-20), (40, 40)), 2)
        #Rechts
        drawCentered(s, weaponIcons[self.weaponIndexR], width*3/4, height/2, 0)
        if self.pointingAt==2:
            pygame.draw.rect(s, (255, 255, 255), ((width*3/4-20, height/2-20), (40, 40)), 2)
    def doLeft(self):
        self.pointingAt=(self.pointingAt-1)%3
    def doRight(self):
        self.pointingAt=(self.pointingAt+1)%3
    def doUp(self):
        if self.pointingAt==0:
            self.weaponIndexL=(self.weaponIndexL+1)%len(allWeapons)
        elif self.pointingAt==1:
            self.vesselIndex=(self.vesselIndex+1)%len(allVessels)
        elif self.pointingAt==2:
            self.weaponIndexR=(self.weaponIndexR+1)%len(allWeapons)
    def doDown(self):
        if self.pointingAt==0:
            self.weaponIndexL=(self.weaponIndexL-1)%len(allWeapons)
        elif self.pointingAt==1:
            self.vesselIndex=(self.vesselIndex-1)%len(allVessels)
        elif self.pointingAt==2:
            self.weaponIndexR=(self.weaponIndexR-1)%len(allWeapons)
playerMenu=PlayerMenu()
TAB=False
while True:
    #FPS handling
    #region
    #clock.tick(60)
    old_t=t
    t=time.time()
    elapsedTime=t-old_t
    if elapsedTime>0:
        fps=1/elapsedTime
    else:
        fps=0
    if not fullscreen:
        pygame.display.set_caption("FPS: "+str(int(fps)))
    #endregion
    s.fill((100, 120, 100))
    if not noRadarRequired:
        lightSurface.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            disconnect()
            pygame.quit()
            exit()
        if event.type==pygame.MOUSEMOTION:
            mx=event.pos[0]
            my=event.pos[1]
            #update playerangle
            if isHosting:
                players[name].updateCursor(mx, my)
            else:
                oz.send("cursor "+name+" "+str(mx+camShiftX)+" "+str(my+camShiftY), SERVER_IP, SERVER_PORT)
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                disconnect()
                pygame.quit()
                print(fps)
                exit()
            if event.key==pygame.K_TAB:
                TAB=True
                playerMenu.pointingAt=1
            if event.key==pygame.K_UP:
                if TAB:
                    playerMenu.doUp()
            if event.key==pygame.K_DOWN:
                if TAB:
                    playerMenu.doDown()
            if event.key==pygame.K_LEFT:
                if TAB:
                    playerMenu.doLeft()
            if event.key==pygame.K_RIGHT:
                if TAB:
                    playerMenu.doRight()
            if event.key==pygame.K_r:
                players[name].r=True
            if isHosting:
                if event.key==pygame.K_w:
                    players[name].up=True
                if event.key==pygame.K_s:
                    players[name].down=True
                if event.key==pygame.K_a:
                    players[name].left=True
                if event.key==pygame.K_d:
                    players[name].right=True
                if event.key==pygame.K_LSHIFT:
                    players[name].shift=True
            else:
                if event.key==pygame.K_w:
                    oz.send("key_press "+name+" up True", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_s:
                    oz.send("key_press "+name+" down True", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_a:
                    oz.send("key_press "+name+" left True", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_d:
                    oz.send("key_press "+name+" right True", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_r:
                    oz.send("key_press "+name+" r True", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_LSHIFT:
                    oz.send("key_press "+name+" shift True", SERVER_IP, SERVER_PORT)
        if event.type==pygame.KEYUP:                
            if event.key==pygame.K_TAB:
                TAB=False
                playerMenu.changePlayer()
            if event.key==pygame.K_r:
                players[name].r=False
            if isHosting:
                if event.key==pygame.K_w:
                    players[name].up=False
                if event.key==pygame.K_s:
                    players[name].down=False
                if event.key==pygame.K_a:
                    players[name].left=False
                if event.key==pygame.K_d:
                    players[name].right=False
                if event.key==pygame.K_LSHIFT:
                    players[name].shift=False
            else:
                if event.key==pygame.K_w:
                    oz.send("key_press "+name+" up False", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_s:
                    oz.send("key_press "+name+" down False", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_a:
                    oz.send("key_press "+name+" left False", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_d:
                    oz.send("key_press "+name+" right False", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_r:
                    oz.send("key_press "+name+" r False", SERVER_IP, SERVER_PORT)
                if event.key==pygame.K_LSHIFT:
                    oz.send("key_press "+name+" shift False", SERVER_IP, SERVER_PORT)
        if event.type==pygame.MOUSEBUTTONDOWN:
            if isHosting:
                if event.button==1:
                    players[name].weaponL.click=True
                if event.button==3:
                    players[name].weaponR.click=True
            else:
                if event.button==1:
                    oz.send("key_press "+name+" mousel True", SERVER_IP, SERVER_PORT)
                if event.button==3:
                    oz.send("key_press "+name+" mouser True", SERVER_IP, SERVER_PORT)
        if event.type==pygame.MOUSEBUTTONUP:
            if isHosting:
                if event.button==1:
                    players[name].weaponL.click=False
                if event.button==3:
                    players[name].weaponR.click=False
            else:
                if event.button==1:
                    oz.send("key_press "+name+" mousel False", SERVER_IP, SERVER_PORT)
                if event.button==3:
                    oz.send("key_press "+name+" mouser False", SERVER_IP, SERVER_PORT)
    #Kamera
    #region
    tmp=abst(players[name].x-width/2, players[name].y-height/2, camShiftX, camShiftY)
    if tmp>1:
        camShiftX+=(players[name].x-width/2-camShiftX)*elapsedTime*7
        camShiftY+=(players[name].y-height/2-camShiftY)*elapsedTime*7
        #update playerangle
        if isHosting:
            players[name].updateCursor(mx, my)
        else:
            oz.send("cursor "+name+" "+str(mx+camShiftX)+" "+str(my+camShiftY), SERVER_IP, SERVER_PORT)
    #endregion
    #Partikel
    #region
    e=0
    while e<len(particles):
        particles[e].draw(s, elapsedTime)
        if particles[e].lifetime<=0:
            particles.pop(e)
        else:
            e+=1
    #endregion
    #Spieler
    #region
    try:
        #Änderung der Größe von players (zum Beispiel durch joinen/leften) während er Iteration kann zu einem Error führen
        for playername in players:
            player=players[playername]
            player.draw(s, elapsedTime)
            if player.changed:
                if isHosting:
                    broadcast("move "+playername+" "+str(player.x)+" "+str(player.y)+" "+str(player.baseAngle))
    except Exception as e:
        print(e)
    #endregion
    #Projektile
    #region
    e=0
    while e<len(projectiles):
        projectiles[e].draw(s, elapsedTime)
        if projectiles[e].lifetime<=0:
            projectiles.pop(e)
        else:
            e+=1
    #endregion
    #Licht
    #region
    if not noRadarRequired and players[name].HP>0:
        beams=getViewBeams(edges, players[name].x, players[name].y)
        drawViewPolygon(lightSurface, beams)
        s.blit(lightSurface, (0, 0))
    #endregion
    #Map zeichnen
    #region
    for x in range(map.width):
        for y in range(map.height):
            currentBlock=map.getBlock(x, y)
            if isOnScreen(x*map.blocksize, y*map.blocksize, border=map.blocksize):
                if currentBlock!=0:
                    pygame.draw.rect(s, (50, 50, 50), ((map.blocksize*x-camShiftX, map.blocksize*y-camShiftY), (map.blocksize, map.blocksize)))
                    if not currentBlock.hasB:
                        pygame.draw.rect(s, (20, 20, 20), ((map.blocksize*x-camShiftX, map.blocksize*y-camShiftY+map.blocksize*0.8), (map.blocksize, map.blocksize*0.2)))
            #Minimap
            if currentBlock==0:
                pygame.draw.line(map.mapImage, (100, 120, 100), (x, y), (x, y), 1)
            else:
                pygame.draw.line(map.mapImage, (50, 50, 50), (x, y), (x, y), 1)
    pygame.draw.line(map.mapImage, (0, 200, 0), (int(players[name].x/map.blocksize), int(players[name].y/map.blocksize)), (int(players[name].x/map.blocksize), int(players[name].y/map.blocksize)), 1)
    s.blit(map.mapImage, (0, 0))
    #endregion
    #UI
    #region
    if TAB:
        playerMenu.draw()
    drawCentered(s, cursorImage, mx, my, 0)
    #endregion
    pygame.display.update()
