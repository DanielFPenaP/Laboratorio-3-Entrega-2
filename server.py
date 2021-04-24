from io import TextIOWrapper
import socket
import threading
import hashlib
from datetime import datetime
from time import time
import os


def sendInfoThread(address, fileName, hash, clientId, logger: TextIOWrapper, server: socket):
    print("Enviando archivo "+fileName+" al cliente "+str(clientId))
    start_time = time()
    paquetes = 0
    file = open(fileName, "rb")
    content = file.read(4096)
    while content:
        server.sendto(content, address)
        paquetes += 1
        content = file.read(4096)

    server.sendto(bytes("Ya termine", "utf-8"), address)
    print("Enviando ya termine cliente "+str(clientId))
    elapsed_time = time() - start_time
    logger.write("El tiempo de transferencia del archivo "+fileName+" al cliente " +
                 str(clientId)+" es: "+str(elapsed_time)+" segundos\n")
    logger.write("Numero de paquetes enviados al cliente " +
                 str(clientId) + " = "+str(paquetes)+" paquetes\n")
    sizefile = os.stat(fileName).st_size
    logger.write("Valor total de bytes enviados al cliente " +
                 str(clientId) + " = "+str(sizefile)+" bytes\n")
    file.close()
    server.sendto(hash, address)


def startLogger():
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    print("Date and time =", dt_string)
    return open(str(dt_string)+"-log.txt", "a")


def getHashFromFile(fileName):
    hash = hashlib.md5()
    file = open(fileName, "rb")
    content = file.read(2048)
    while content:
        content = file.read(2048)
        hash.update(content)
    return hash.digest()


def getFileName(value):
    if value == "1":
        fileName = "infra/100 MB.mp4"
    elif value == "2":
        fileName = "infra/250 MB.mp4"
    else:
        fileName = "prueba.txt"
    return fileName


def startServer(logger: TextIOWrapper):
    logger.write("Comenzando servidor\n")
    host = "192.168.107.128"
    port = 10000
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    print("Socket binded to port", port)
    return server


def printMenu(logger: TextIOWrapper):
    print('Seleccione el archivo a utilizar')
    print('1. Archivo de 100MB')
    print('2. Archivo de 250MB')
    opcionA = input()
    logger.write("Nombre del archivo enviado: ")
    consoleMsg = ('Usted seleccionó la opcion ' +
                  opcionA) if opcionA == '1' or opcionA == '2' else 'Opcion de prueba'
    print(consoleMsg)
    return opcionA

def getClients(logger: TextIOWrapper, server: socket, clientsNumber: int):
    lista = []
    clientId = 0
    print("Recibiendo clientes")
    while clientsNumber > clientId:
        data, addr = server.recvfrom(40)
        print("cliente "+str(clientId)+": "+data.decode("utf-8"))
        if data == bytes("Hola", "utf-8"):
            clientId += 1
            print('Connected to :', addr[0], ':', addr[1])
            logger.write("Cliente "+str(clientId)+":\n")
            logger.write("Se ha conectado el cliente " +
                         str(addr[0])+" al puerto "+str(addr[1])+"\n")
            lista.append([addr,clientId])
            server.sendto(bytes(str(clientId), "utf-8"), addr)
            
    return lista


def Main():
    logger = startLogger()
    server = startServer(logger)
    selectedOption = printMenu(logger)
    fileName = getFileName(selectedOption)
    logger.write(fileName+"\n")
    hash = getHashFromFile(fileName)
    print('A cuántos usuarios desea transmitir el archivo')
    clientsNumber = int(input())
    print('Usted selecionó '+str(clientsNumber)+' usuarios')
    # server.listen(25)
    print("Socket is listening")
    clients = getClients(logger, server, clientsNumber)

    thread_list = []
    for j in range(len(clients)):
        print("Creando Thread "+str(j))
        thread = threading.Thread(target=sendInfoThread, args=(
            clients[j][0], fileName, hash, clients[j][1], logger, server))
        thread.start()
        thread_list.append(thread)
        
    for thread in thread_list:
        print("Haciendo join")
        thread.join()
    print("Se terminó de enviar la información a todos los clientes")


if __name__ == '__main__':
    Main()
