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
    elapsed_time = time() - start_time
    logger.write("El tiempo de transferencia del archivo "+fileName+" al cliente" +
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
    return open(str(dt_string)+"-Server-log.txt", "a")


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
    consoleMsg = ('Usted selecciono la opcion ' +
                  opcionA) if opcionA == '1' or opcionA == '2' else 'Opcion de prueba'
    print(consoleMsg)


def getClients(logger: TextIOWrapper, server: socket, clientsNumber: int):
    lista = []
    clientId = 0
    print("Recibiendo clientes")
    while clientsNumber > clientId:
        data, addr = server.recvfrom(1024)
        if data == bytes("Hola", "utf-8"):
            clientId += 1
            print('Connected to :', addr[0], ':', addr[1])
            logger.write("Cliente "+str(clientId)+":\n")
            logger.write("Se ha conectado el cliente " +
                         str(addr[0])+" al puerto "+str(addr[1])+"\n")
            server.sendto(bytes(str(clientId), "utf-8"), addr)
        elif data[0:20] == bytes("Ya recibi mi numero", "utf-8"):
            id = data[20:len(data)].decode('utf-8')
            lista.append([addr, id])
            print("El cliente recibio su numero: " + id)
    return lista


def Main():
    logger = startLogger()
    server = startServer(logger)
    selectedOption = printMenu(logger)
    fielName = getFileName(selectedOption)
    logger.write(fielName+"\n")
    hash = getHashFromFile(fielName)
    print('A cuantos usuarios desea transmitir el archivo')
    clientsNumber = int(input())
    print('Usted seleciono '+str(clientsNumber)+' usuarios')
    # server.listen(25)
    print("Socket is listening")
    clients = getClients(logger, server, clientsNumber)

    thread_list = []
    for j in range(len(clients)):
        thread = threading.Thread(target=sendInfoThread, args=(
            clients[j][0], fielName, hash, clients[j][1], logger))
        thread.start()
        thread_list.append(thread)

    finishedClients = 0
    while finishedClients < len(clients):
        data, addr = server.recvfrom(1024)
        if data[0:10] == bytes("Ya recibi", "utf-8"):
            finishedClients += 1
            clientId = data[10:len(data)].decode('utf-8')
            print("Confirmacion exitosa para cliente " + clientId)
            logger.write(
                "Tranferencia exitosa hacia el cliente " + clientId+"\n")
        elif data[0:10] == bytes("No recibi", "utf-8"):
            finishedClients += 1
            clientId = data[10:len(data)].decode('utf-8')
            print("Confimacion NO exitosa para cliente " + clientId)
            logger.write(
                "Tranferencia NO exitosa hacia el cliente " + clientId+"\n")

    print("Se termino de enviar la informacion a todos los clientes")


if __name__ == '__main__':
    Main()
