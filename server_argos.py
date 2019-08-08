import socket
import sys
import datetime
import time
import _thread
import sqlite3

#   Variables globales
## Hard-coded IP and PORT
IP = '192.168.1.101'
PORT = 3480
##Conexion a base de datos
conn = sqlite3.connect('MyDatabase.sqlite')
c = conn.cursor()
##For testing purposes
tecla = 0
DEBUG = False



def conectar():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.bind((IP, PORT))
    s.listen(5)
    print(f'Escuchando en {IP} : {PORT}')
    try:
        clientsocket, address = s.accept()
        print(f'Connection from {address} established')
        trama = clientsocket.recv(128)
        if(DEBUG): print(f'{trama}  largo:{len(trama)}')   #For debugging
    except:
        print('\n\t SOCKET TIMEOUT!')
        return 0, 0, 0, 0, 0
        # sys.exit()
    comando = trama[0] + trama[1]
    mac = "%0.2X" % trama[2] + "%0.2X" % trama[3] + "%0.2X" % trama[4] + "%0.2X" % trama[5] + "%0.2X" % trama[6] + "%0.2X" % trama[7]
    argc = trama[8] + trama[9] + trama[10] + trama[11]
    if(DEBUG): print(f'Comando recibido: {comando}   MAC: {mac}   argc: {argc}')   # For debugging

    return clientsocket, address, comando, mac, argc

def leer(clientsocket, mac):
    fin = False
    datoQ = []
    request = bytes([1, 64, 00, 00, 00, 00, 00, 00])
    while not fin :
        clientsocket.send(request)
        trama = clientsocket.recv(128)
        if(DEBUG): print(f'{trama}  largo:{len(trama)}')   #For debugging
        for i in range(8):
            if trama[8*i+1] == 0 and trama[8*i+2] == 0 and trama[8*i+3] == 0 and trama[8*i+4] == 0 and trama[8*i+5] == 0 and trama[8*i+6] == 0 and trama[8*i+7] == 0 :
                fin = True
                now = datetime.datetime.now()
                sendnow = bytearray([2, 0, now.second, now.minute, now.hour, now.day, now.month ,now.year-2000])
                clientsocket.send(sendnow)
                desconectar(clientsocket)
                break
            tension = "%3.2f" % ((trama[8*i+0]<<8 | trama[8*i+1])/100)   #Formato de tension: xxx.xx V
            corriente = "%2.3f" % ((trama[8*i+2]<<8 | trama[8*i+3])/1000)   #Formato de corriente: xx.xxx A
            min = "%d" % trama[8*i+4]
            hour = "%d" % trama[8*i+5]
            day = trama[8*i+6]>>3
            month = ((trama[8*i+6]&7)<<1) |(trama[8*i+7]>>7)
            year = 2000 + (trama[8*i+7]&127)
            try:
                fecha = datetime.datetime(int(year), int(month), int(day), int(hour), int(min), 0)
                dato = []
                dato.append(tension)
                dato.append(corriente)
                dato.append(fecha)
                dato.append(mac)
                datoQ.append(dato)
                if(DEBUG): print(f'{year}-{month}-{day} {hour}:{min}:00  ->  Tension: {tension} V  Corriente: {corriente} A desde: {mac}')  #For debugging
            except:
                print('Error de fecha') #Si la fecha que leyó no es correcta (algun error random) saltea el paso. Sino me corta la operacion

    for item in datoQ:
        if(DEBUG): print(f'{item[0]} V {item[1]} A - Medido: {item[2]} desde: {item[3]}')   #For debugging
        sql = "INSERT INTO measures (mac, time, voltage, current) VALUES (?,?,?,?)" #sql query
        values = (str(item[3]), int(time.mktime(item[2].timetuple())), int(float(item[0])*100), int(float(item[1])*1000))   #sql values for the query
        c.execute(sql, values)
        conn.commit()

    print(f'Cargados {len(datoQ)} registros en la base de datos')
    return trama, len(datoQ)

def realtime(clientsocket):
    request = bytes([11, 164, 00, 00, 00, 00, 00, 00])
    clientsocket.send(request)
    trama = clientsocket.recv(128)
    if(DEBUG): print(f'{trama}  largo:{len(trama)}')   #For debugging
    tension = "%3.2f" % ((trama[0]<<8 | trama[1])/100)   #Formato de tension: xxx.xx V
    corriente = "%2.3f" % ((trama[2]<<8 | trama[3])/1000)   #Formato de corriente: xx.xxx A
    tension = int(float(tension)*100)
    corriente = int(float(corriente)*1000)
    print(f'Tension: {tension} V  Corriente: {corriente} A')
    return tension, corriente

def desconectar(clientsocket):
    clientsocket.shutdown(socket.SHUT_RDWR)
    clientsocket.close()
    if(DEBUG): print('Disconected!')

def getdevices():
    devices = []
    sql = "SELECT * FROM devices"
    for row in c.execute(sql):
        devices.append((row[0], row[1], row[2]))
    return devices


# Rutina para salir del monitor en tiempo real (only testing)
def teclapresionada():
    global tecla
    while True:
        tecla = input('presione para salir \n')
        if tecla:
            break



def test():
    global tecla
    while True:
        request = input('Modos: 1-Leer  2-RTM  3-Salir   ')
        if request == '1':
            clientsocket, address, comando, mac, argc = conectar()
            trama = leer(clientsocket, mac)
        elif request == '2':
            clientsocket, address, comando, mac, argc = conectar()
            tecla = 0
            _thread.start_new_thread(teclapresionada, ())
            while not tecla:
                tension, corriente = realtime(clientsocket)
                time.sleep(1)
            desconectar(clientsocket)
        elif request == '3':
            sys.exit()
        else:
            print('Invalido')

if __name__ == '__main__':
    test()
