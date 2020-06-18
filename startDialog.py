from tkinter import *
import random

root=None
name=""
hosts=True
ip=""
port=0

def handle_name(r_name):
    global name

    if r_name=="":
        name="Unknown_"+str(random.randint(0, 10000))

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
        print("gibts nicht")
    else:
        root.destroy()

def joinFunc(r_name, r_ip, r_port):
    global hosts
    global ip
    global port
    global root

    handle_name(R_name)

    hosts = False
    ip = r_ip

    try:
        port = int(r_port)
    except:
        print("gibts nicht")
    else:
        root.destroy()


def start():
    global root
    global name

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

    #root.geometry("800x600")
    root.mainloop()

    return name, hosts, ip, port