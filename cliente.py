import threading
import hashlib
import socket
from datetime import datetime
from time import time
import os
host = "192.168.1.62"
port = 10000
def connectToServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    server_address = (host, port)
    print('Connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)
    return sock


def helloProtocol(socket, log):
    clientId, address = socket.recvfrom(4096)
    socket.sendto(bytes("Ya recibi mi numero", "utf-8"),address)
    clientId = clientId.decode("utf-8")
    fileName = "Cliente"+ str(clientId) +"-.mp4"
    log.write("El nombre de archivo recibido es: "+fileName+"\n")
    log.write("Mi numero de cliente es: " + clientId + "\n")
    return [fileName, clientId]


def getHashFromFile(fileName):
    hash = hashlib.md5()
    file = open(fileName, "rb")
    content = file.read(4096)
    while content:
        content = file.read(4096)
        hash.update(content)
    return hash.digest()


def checkHash(fileName):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.bind((host, port)) 
    conecction, addr = server.accept()
    input_data = socket.recv(4096)
    if input_data:
        if isinstance(input_data, bytes):
            end = input_data == bytes("Ya termine", "utf-8")
        else:
            end = input_data == "Ya termine"
        if not end:
            hash = input_data
            calculateHash = getHashFromFile(fileName)
            comprobacion = hash == calculateHash
            print("Hash recibido: "+ str(hash))
            print("Hash calculado: "+ str(calculateHash))
            print("Son iguales = " + str(comprobacion)) 


def saveFileFromServer(fileName, socket , clientId, log):
    file = open(fileName, "wb")
    print("Esperando...")
    start_time = time()
    paquetes = 0
    goodEnd = False
    while True:
        paquetes += 1
        bytes_read, address = socket.recvfrom(4096)
        if not bytes_read:
            break
        end = bytes_read[len(bytes_read) - 10:len(bytes_read)] == bytes("Ya termine", "utf-8")
        if not end:
            file.write(bytes_read)
        else:
            file.write(bytes_read[0:len(bytes_read) - 10])
            goodEnd = True
            break

    if(goodEnd):     
        elapsed_time = time() - start_time
        log.write("El tiempo de transferencia del archivo "+fileName+" al cliente "+
                clientId + " es: " + str(elapsed_time) + " segundos\n")    
        log.write("Numero de paquetes enviados al cliente "+ clientId +" = " + str(paquetes) + " paquetes\n") 
        file.close()
        print("El archivo se ha recibido correctamente.")
        socket.sendto(bytes("Ya recibi", "utf-8"),address)
        log.write("Transmision exitosa del cliente "+ clientId +"\n")
    else:
        print("Error en la transmision")
        log.write("Error en transmision del cliente "+ clientId +"\n")


def threadedC(id):
    print('Inicio cliente')
    socket = connectToServer()
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    print("date and time =", dt_string)	
    log = open(dt_string+"_client_"+str(id)+"-log.txt","a")
    log.write("Comenzando Cliente\n")
    fileName, clientId = helloProtocol(socket, log)
    saveFileFromServer(fileName, socket, clientId, log)
    sizefile = os.stat(fileName).st_size
    log.write("Valor total de bytes enviados al cliente "+  clientId +" = "+str(sizefile)+" bytes\n")
    log.close()
    checkHash(socket, fileName)
    print('Cerrando socket')
    socket.close()


def Main():
    print('Ingrese el numero de clientes a crear')
    clientNumber = int(input())
    # print (clientNumber)
    thread_list = []
    for j in range(clientNumber):
        thread = threading.Thread(target = threadedC, args = (j+1,))
        thread.start()
        thread_list.append(thread)

    for thread in thread_list:
        thread.join()
    print("Se termino de recibir la informacion de todos los clientes")

if __name__ == '__main__': 
    Main() 
