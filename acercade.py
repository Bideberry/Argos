from tkinter import *



class About:
    # Constructor de clase
    def __init__(self, master, logo):
        self.master = master
        self.logo = logo
        self.__place_widgets()  # Crea y ubica los widgets

    def __place_widgets(self):
        label1 = Label(self.master, image = self.logo)
        label1.image = self.logo
        label1.pack(side=TOP)
        label2 = Label(self.master, font=('Calibri', 11), justify='left', text='  Argos - Industria Argentina\n\n Somos una empresa dedicada a la\n producción de sistemas de monitoreo\n de consumo eléctrico, fundada en\n marzo de 2016 por sus miembros:\n\n  Ing. César Carballido\n  Ing. Mauro Vaca\n  Sr. Agustín Bideberry\n')
        label2.pack(side=TOP)

def test():
    root = Tk()

    logo = PhotoImage(file='argos_logo.gif')

    newAbout = About(root, logo)

    root.mainloop()


if __name__ == '__main__':
    test()
