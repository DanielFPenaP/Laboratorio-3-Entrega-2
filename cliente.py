import threading
import hashlib
import socket
from datetime import datetime
from time import time
import os
timeout = socket.timeout
server_address = ('192.168.107.128', 10000)

def sendDataToServer(data, socket: socket):
    socket.sendto(data, server_address)


def helloProtocol(socket: socket, log, clientNumber):
    print("Mandando hola cliente: "+str(clientNumber))
    sendDataToServer(bytes("Hola", "utf-8"), socket)
    print("Recibiendo id cliente: "+str(clientNumber))
    data, address = socket.recvfrom(40)
    clientId = data.decode("utf-8")  
    # print("Mandando confirmación")
    # socket.sendto(bytes("Ya recibi mi numero"+str(clientId),"utf-8"), address)
    fileName = "Cliente" + str(clientId) + "-Prueba-" + str(clientNumber) + ".mp4"
    log.write("El nombre de archivo recibido es: "+fileName+"\n")
    log.write("Mi numero de cliente es: " + clientId + "\n")
    return [fileName, clientId]


def getHashFromFile(fileName):
    hash = hashlib.md5()
    file = open(fileName, "rb")
    content = file.read(2048)
    while content:
        content = file.read(2048)
        hash.update(content)
    return hash.digest()


def checkHash(socket: socket, fileName):
    input_data = socket.recvfrom(4096)
    if input_data:
        if isinstance(input_data, bytes):
            end = input_data == bytes("Ya termine", "utf-8")
        else:
            end = input_data == "Ya termine"
        if not end:
            hash = input_data
            calculateHash = getHashFromFile(fileName)
            comprobacion = hash[0] == calculateHash
            print("Hash recibido: " + str(hash[0]))
            print("Hash calculado: " + str(calculateHash))
            print("Son iguales = " + str(comprobacion))
            return comprobacion


def saveFileFromServer(fileName, socket, clientId, log):
    file = open(fileName, "wb")
    print("Esperando...")
    start_time = time()
    paquetes = 0
    goodEnd = False
    fallo = False
    print("Empezando transferencia cliente ",clientId)
    while True:
        paquetes += 1
        
        try:
            bytes_read,address = socket.recvfrom(4096)
        except timeout:
                print("timeout falla en descarga cliente ", clientId)
                break
                continue
        if fallo:
            break
        print("Recibí paquete, cliente", clientId)
        end = bytes_read[len(bytes_read) - 10:len(bytes_read)
                         ] == bytes("Ya termine", "utf-8")
       
        if not end:
            print("Escribiendo cliente "+str(clientId))
            file.write(bytes_read)
        
        else:
            print("Terminó cliente "+str(clientId))
            file.write(bytes_read[0:len(bytes_read) - 10])
            goodEnd = True
            break
    print("Evaluando resultado")
    if(goodEnd):
        elapsed_time = time() - start_time
        log.write("El tiempo de transferencia del archivo "+fileName+" al cliente " +
                  clientId + " es: " + str(elapsed_time) + " segundos\n")
        log.write("Numero de paquetes enviados al cliente " +
                  clientId + " = " + str(paquetes) + " paquetes\n")
        file.close()
        if checkHash(socket, fileName):
            print("El archivo se ha recibido correctamente.")
            sendDataToServer(bytes("Ya recibi", "utf-8"), socket)
            log.write("Transmision exitosa del cliente " + clientId + "\n")
        else:
            print("El archivo NO se ha recibido correctamente.")
            sendDataToServer(bytes("No recibi", "utf-8"), socket)
            log.write("Transmision No exitosa del cliente " + clientId + "\n")
    else:
        print("Error en la transmisión")
        sendDataToServer(bytes("No recibi", "utf-8"), socket)
        log.write("Error en transmision del cliente " + clientId + "\n")


def startLogger(clientId):
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    print("Date and time = ", dt_string)
    return open(dt_string+"_client_"+str(clientId)+"-log.txt", "a")


def threadedCliente(id, clientNumber):
    print('Inicio cliente', id)
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cliente.settimeout(5)
    logger = startLogger(id)
    logger.write("Comenzando Cliente\n")
    fileName, clientId = helloProtocol(cliente, logger, clientNumber)
    print("Termina protocolo hola")
    saveFileFromServer(fileName, cliente, clientId, logger)
    sizefile = os.stat(fileName).st_size
    logger.write("Valor total de bytes enviados al cliente " +
                 clientId + " = "+str(sizefile)+" bytes\n")
    logger.close()

    
def Main():
    print('Ingrese el número de clientes a crear')
    clientNumber = int(input())
    # print (clientNumber)
    thread_list = []
    for j in range(clientNumber):
        thread = threading.Thread(target=threadedCliente, args=(j+1, clientNumber,))
        thread.start()
        thread_list.append(thread)

    for thread in thread_list:
        thread.join()
    print("Se termino de recibir la información de todos los clientes")


if __name__ == '__main__':
    Main()
