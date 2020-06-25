from tkinter import *
import random, socket, time
from oznet import *

root=None
name=""
hosts=True
ip=""
port=0

frame=None
nameEntry=None

all_instances=[]
servers=[]

def getMyIp():
    return socket.gethostbyname(socket.getfqdn())

def handlePing(msg, ip, port):
    global servers
    if msg=="pong":
        if not ip in servers:
            print("Da war was! auf "+ip+":"+str(port))
            addButton(ip)
            servers.append(ip)

def addButton(ip):
    global frame
    global nameEntry
    tmpButton = Button(frame, text="Join Server on " + ip, command=lambda: joinFunc(nameEntry.get(), ip, 12000))
    tmpButton.pack()

def addJoinButtons():
    global all_instances

    my_ip=getMyIp()
    tmp=my_ip.split(".")
    tmp=tmp[:-1]
    mask=".".join(tmp)
    mask+="."
    n=0
    for i in range(1, 256):
        tmp_ip=mask+str(i)
        #print(tmp_ip)
        try:
            all_instances.append(Oz("", 12000+n))
            all_instances[-1].start(handlePing)
            all_instances[-1].sendImportant("ping", tmp_ip, 12000)
        except:
            #print("Error")
            pass
        n+=1



def handle_name(r_name):
    global name

    if r_name=="":
        name="Unknown_"+str(random.randint(0, 10000))
    else:
        name=r_name.replace(" ", "_")

def hostFunc(r_name, r_port):
    global hosts
    global port
    global root

    hosts = True
    
    handle_name(r_name)

    try:
        port = int(r_port)
    except:
        print("Port 12000")
    root.destroy()

def joinFunc(r_name, r_ip, r_port):
    global hosts
    global ip
    global port
    global root

    handle_name(r_name)

    hosts = False
    ip = r_ip

    try:
        port = int(r_port)
    except:
        print("Port 12000")
    root.destroy()


def start():
    global root
    global name
    global frame
    global nameEntry

    root = Tk()

    root.title("LAN Game - start options")

    ipLabel = Label(root, text="IP:")
    ipEntry = Entry(root)

    ipLabel.grid(row=0, column=0)
    ipEntry.grid(row=0, column=1)

    portLabel = Label(root, text="Port (default: 12000):")
    portEntry = Entry(root)

    portLabel.grid(row=1, column=0)
    portEntry.grid(row=1, column=1)

    nameLabel = Label(root, text="Playername:")
    nameEntry = Entry(root)

    nameLabel.grid(row=2, column=0)
    nameEntry.grid(row=2, column=1)

    hostButton = Button(root, text="Host Game", command=lambda: hostFunc(nameEntry.get(), portEntry.get()))
    joinButton = Button(root, text="Join Game", command=lambda: joinFunc(nameEntry.get(), ipEntry.get(), portEntry.get()))

    hostButton.grid(row=3, column=0)
    joinButton.grid(row=3, column=1)

    frame = Frame(root, relief=SUNKEN)
    frame.grid(row=4, column=0)

    addJoinButtons()

    #addButton("192.168.0.0")

    #root.geometry("800x600")
    root.mainloop()

    for i in all_instances:
        i.stop()

    return name, hosts, ip, port