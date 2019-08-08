from tkinter import *
from tkinter import messagebox
import socket

## Hard-coded IP and PORT
IP = '192.168.1.1'
PORT = 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class ConfigSensor:
    #   Constructor de clase
    def __init__(self, master):
        self.master = master
        self.__place_widgets()  # Crea y ubica los widgets

    #   Funciones
    def __place_widgets(self):
        self.master.title('Configuracion')
        canvas = Canvas(self.master, height=150, width=200)
        label_ssid = Label(self.master, text='Nombre de la red:')
        label_ssid.pack(side=TOP)
        label_pwd = Label(self.master, text='Contraseña:')
        label_pwd.pack(side=TOP)
        csssid = StringVar()
        cspwd = StringVar()
        ent_ssid = Entry(self.master, textvariable=csssid, width=30)
        ent_ssid.pack(side=TOP, padx=10, after=label_ssid)
        ent_pwd = Entry(self.master, textvariable=cspwd, width=30, show='*')
        ent_pwd.pack(side=TOP, padx=10, after=label_pwd)
        boton_configsensor = Button(self.master, text='Configurar', cursor='hand2', command=lambda:self.configwifi(csssid.get(),cspwd.get()))
        boton_configsensor.pack(side=TOP, pady=20)

    def configwifi(self, csssid, cspwd):
        if csssid and cspwd:
            try:
                command = f'apply,{csssid},2,{cspwd},'
                s.connect((IP, PORT))
                s.send(bytes(command, 'utf-8'))
            except:
                messagebox.showerror('Error', 'Falló la configuración.\nVerifique conexión')
        else:
            messagebox.showwarning('Advertencia', 'Nombre de red o contraseña no pueden estar vacíos')


def test():
    root = Tk()

    CSwindow = ConfigSensor(root)

    root.mainloop()


if __name__ == '__main__':
    test()
