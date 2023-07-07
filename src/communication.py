import sys
import struct
import time
from multiprocessing import Process, Event, Pipe, Value, Manager
sys.path.insert(0, 'C:/Users/ferna/Dropbox/UC/Magister/robot-flautista')
import src.lib.ethernet_ip.ethernetip as ethernetip
#from exercises.drivers_connect import Command, Setting, INPUT_FUNCTION_BITS, VirtualFlow, VirtualAxis
from numpy import sign

class CommunicationCenter(Process):
    """
    Clase que se encarga de la comunicación con los dispositivos mediante EthernetIP
    """
    def __init__(self, host, event, pipe, data, connect=True, verbose=False):
        Process.__init__(self)
        self.event = event
        self.pipe = pipe
        self.host = host
        self.EIP = ethernetip.EtherNetIP(self.host)
        self.connections = {}
        self.data = data
        self.verbose = verbose
        self.connect = connect
    
    def send_setAttrSingle(self, C1, data, device, dir1, dir2, dir3):
        try:
            r = C1.setAttrSingle(dir1, dir2, dir3, data)
            if r is None:
                raise Exception
        except:
            C1 = self.EIP.explicit_conn(device)
            C1.registerSession()
            r = C1.setAttrSingle(dir1, dir2, dir3, data)
        return C1
    
    def run(self):
        self.EIP.startIO() # inicio de la comunicación. Es importante pararla al final.
        while self.event.is_set(): # se usa un evento que al cerrar la aplicacion permite terminar este proceso
            for host, conn in self.connections.items(): # para cada dispositivo con el que se abrió un canal de comunicación...
                try:
                    # en la memoria compartida se actualiza la entrada de cada dispositivo y se usa lee lo que se quiere poner a la salida para actualizar el mensaje a cada dispositivo. 
                    # conn.inAssem es la entrada de cada dispositivo (de lectura)
                    # conn.outAssem es la salida a cada dispositivo (de escritura)
                    self.data[host + '_in'] = conn.inAssem
                    conn.outAssem = self.data[host + '_out']
                except:
                    print("Hubo un error en la lectura del input en el centro de comunicaciones", host)
                    print(self.data)
            if self.pipe.poll(): # si revisa si hay alguna instrucción esperando en la tuberia
                message = self.pipe.recv() # se recibe el mensaje que esta en espera
                if self.verbose:
                    print("Message received", message)
                if message[0] == "explicit_conn": # este es la primera instruccion para iniciar la comunicación con un dispositivo
                    C1 = self.EIP.explicit_conn(message[1]) # se crea la conexión con la dirección IP
                    C1.outAssem = [0 for i in range(message[2])]
                    C1.inAssem = [0 for i in range(message[3])]

                    pkt = C1.listID()
                    if pkt is not None:
                        print("Product name: ", pkt.product_name.decode())

                    inputsize = message[4]
                    outputsize = message[5]

                    # se crean las entradas en la memoria compartida
                    self.data[message[1] + '_in'] = [0 for i in range(inputsize*8)] 
                    self.data[message[1] + '_out'] = [0 for i in range(outputsize*8)]

                    # se registran los canales de entrada y salida con la direccion de los assembly
                    self.EIP.registerAssembly(message[6], inputsize, message[7], C1) 
                    self.EIP.registerAssembly(message[8], outputsize, message[9], C1)

                    self.connections[message[1]] = C1
                    print("Assembly registered...")

                elif message[0] == "registerSession":
                    # se registra la sesion
                    self.connections[message[1]].registerSession()

                elif message[0] == "sendFwdOpenReq":
                    # comienza la comunicación implicita con el dispositivo cuya direccion se informa en message[1]
                    self.connections[message[1]].sendFwdOpenReq(message[2], message[3], message[4], torpi=message[5], otrpi=message[6], priority=message[7])
                    self.connections[message[1]].produce()

                elif message[0] == "stopProduce":
                    # termina la comunicación implicita con el dispositivo cuya direccion se informa en message[1]
                    self.connections[message[1]].stopProduce()
                    self.connections[message[1]].sendFwdCloseReq(message[2], message[3], message[4])
                    del self.connections[message[1]]
                
                elif message[0] == "setAttrSingle":
                    self.connections[message[1]] = self.send_setAttrSingle(self.connections[message[1]], message[5], message[1], message[2], message[3], message[4])
                
                elif message[0] == "getAttrSingle":
                    # para leer un atributo con comunicación explicita
                    att = self.connections[message[1]].getAttrSingle(message[2], message[3], message[4])
                    self.pipe.send([message[1], att])
            time.sleep(0.008)
        self.EIP.stopIO() # se cierra la comunicación


if __name__ == "__main__":
    pass