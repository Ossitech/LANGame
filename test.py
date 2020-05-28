import oznet


def c1(msg, ip, port):
    print("C1 From: "+ip+":"+str(port)+"\n"+msg)

def c2(msg, ip, port):
    print("C2 From: "+ip+":"+str(port)+"\n"+msg)

a=oznet.Oz("", 12000)
b=oznet.Oz("", 12001)
a.start(c1)
b.start(c2)

while True:
    msg=input()
    a.sendImportant(msg, "127.0.0.1", 12001)
    b.sendImportant(msg, "127.0.0.1", 12000)