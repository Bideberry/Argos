from tkinter import *
from tkinter import messagebox
import subprocess
import graficos
import acercade

class MenuArgos:
        #   Constructor de clase
        def __init__(self, master):
            self.master = master
            self.__place_widgets()  # Crea y ubica los widgets

        #   Funciones
        def __place_widgets(self):
            menubar = Menu(self.master)
            menuH = Menu(menubar, tearoff=0)
            menuH.add_command(label='Picos de consumo', command=self.picosconsumo)
            menuH.add_command(label='Baja tension', command=self.bajatension)
            menuH.add_command(label='Monitor en tiempo real', command=self.openRTM)
            menuH.add_command(label='Consola de administrador')
            menubar.add_cascade(label='Herramientas', menu=menuH)

            menuA = Menu(menubar, tearoff=0)
            menuA.add_command(label='Manual de usuario', command=lambda:self.openFile('Manual de Usuario Argos.pdf'))
            menuA.add_command(label='Manual técnico', command=lambda:self.openFile('Manual técnico Argos.pdf'))
            menuA.add_command(label='Acerca de...', command=self.openAbout)
            menubar.add_cascade(label='Ayuda', menu=menuA)

            self.master.config(menu=menubar)

        def openFile(self, archivo):
             subprocess.Popen('Manuales/'+archivo, shell=TRUE)

        def openAbout(self):
            newWin = Toplevel(self.master)
            newWin.iconbitmap('argos_icon.ico')
            logo = PhotoImage(file='argos_logo.gif')
            newAbout = acercade.About(newWin, logo)

        def openRTM(self):
            global rootanimation
            newWin = Toplevel(self.master)
            newWin.iconbitmap('argos_icon.ico')
            newWin.title('Monitor en tiempo real -- Argos v2')
            newRTM = graficos.RTM(newWin)
            rootanimation = graficos.startanimation(newRTM)

        def picosconsumo(self):
            graficos.openpicos(self.master)

        def bajatension(self):
            graficos.openbajat(self.master)


        # Para funciones pendientes...
        def comingsoon(self):
            messagebox.showinfo('Argos v2', 'Proximamente...')

def test():
    root = Tk()

    newMenu = MenuArgos(root)

    root.mainloop()


if __name__ == '__main__':
    test()
