import socket
import _thread
import time

class Oz:
    def __init__(self, ip, port):
        self.ip=ip
        self.port=port
        self.running=False
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lastImportandMessage=""
    def start(self, callback):
        self.callback=callback
        self.sock.bind((self.ip, self.port))
        if not self.running:
            self.running=True
            _thread.start_new_thread(self.service, (),)
    def service(self):
        while self.running:
            try:
                data, addr=self.sock.recvfrom(4096)
                msg=data.decode()
                msg_splitted=msg.split()
                if len(msg_splitted)>=2:
                    if msg!=self.lastImportandMessage:
                        if msg_splitted[-2]=="stamp":
                            self.lastImportandMessage=msg
                            #Timestamp abschneiden
                            msg=" ".join(msg_splitted[:-2])
                        self.callback(msg, addr[0], addr[1])
                else:
                    self.callback(msg, addr[0], addr[1])
            except Exception as e:
                print(e)
    def stop(self):
        self.running=False
    def send(self, message, ip, port):
        data=message.encode()
        if data!=None:
            self.sock.sendto(data, (ip, port))
    def sendImportant(self, message, ip, port):
        stamp=str(time.time())
        message+=" stamp "+stamp
        self.send(message, ip, port)
        self.send(message, ip, port)
        self.send(message, ip, port)