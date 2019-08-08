from tkinter import *
import time
import datetime
import menu
import configsensor
import graficos


from tkinter import ttk

#   Variable globales (:$)
##Dimensiones
HEIGHT=500
WIDTH=1000
##Conexion a la base de datos
conn = graficos.sqlite3.connect('MyDatabase.sqlite')
c = conn.cursor()
##Nombre y mac del dispositivo seleccionado
nombrectual = None
macactual = None
##Animacion del medidor en tiempo real (debe ser instanciada antes del mainloop)
rootanimation = None
##Inicializo labels desde y hasta con fecha ayer y hoy
z1 = str(datetime.datetime.now()-datetime.timedelta(days=1))[:-7]
z2 = str(datetime.datetime.now())[:-7]


# Funciones generales
def openConfigSensor(master):
    CSwindow = Toplevel(master)
    newCS = configsensor.ConfigSensor(CSwindow)






#   Programa
def argosmain():
    root=Tk()

    root.title('Argos v2')
    root.iconbitmap('argos_icon.ico')

    logo = PhotoImage(file='argos_logo.gif')

    #   Formato de la ventana principal
    canvas1=Canvas(root, height=HEIGHT, width=WIDTH*0.2)
    canvas1.pack(side=LEFT, fill=Y)
    canvas2=Canvas(root, height=HEIGHT, width=WIDTH*0.8)
    canvas2.pack(side=LEFT, expand=TRUE, fill=BOTH)

    #   Sectores base
    sincronizacion = LabelFrame(canvas1, text='Sincronizacion', height=HEIGHT*0.15, width= WIDTH*0.2)
    sincronizacion.pack(expand=FALSE, fill=X)
    consulta = LabelFrame(canvas1, text='Consulta', height=HEIGHT*0.35, width= WIDTH*0.2)
    consulta.pack(expand=FALSE, fill=X)
    valores = LabelFrame(canvas1, text='Argos v2', height=HEIGHT*0.5, width= WIDTH*0.2)
    valores.pack(expand=TRUE, fill=Y)
    bdatos = LabelFrame(canvas2, text='Base de datos')
    bdatos.pack(expand=TRUE, fill=BOTH)

    #   Graficos desde base de datos
    rootGraficos = graficos.Graficos(bdatos)

    #   Sincronizacion con el sensor
    boton_config = Button(sincronizacion, text='Configurar...', cursor='hand2', command=lambda:openConfigSensor(root))
    boton_config.place(x='20', y='15')
    boton_sinc = Button(sincronizacion, text='Sincronizar', cursor='hand2', command=lambda:graficos.sincronizar(root))
    boton_sinc.place(x='120', y='15')

    #   Consulta de datos
    label_consulta = Label(consulta, text='Desde: \n\nHasta: \n\nSensor:', justify='left')
    label_consulta.place(x='0', y='0')

    ent_fecha_desde = Entry(consulta)
    ent_fecha_desde.insert(0, z1)
    ent_fecha_desde.place(x='180', y='0', anchor='ne')
    boton_fecha_desde = Button(consulta, text='...', command=lambda:graficos.calwidget.Calendar.pickdate(consulta, ent_fecha_desde))
    boton_fecha_desde.place(x='210', y='0', anchor='ne')

    ent_fecha_hasta = Entry(consulta)
    ent_fecha_hasta.insert(0, z2)
    ent_fecha_hasta.place(x='180', y='30', anchor='ne')
    boton_fecha_hasta = Button(consulta, text='...', command=lambda:graficos.calwidget.Calendar.pickdate(consulta, ent_fecha_hasta))
    boton_fecha_hasta.place(x='210', y='30', anchor='ne')

    tkvar = StringVar(consulta)
    tkvar.set('Seleccione un sensor...')

    devices = graficos.server_argos.getdevices()

    devnm = []
    for t in devices: devnm.append(t[2])

    menuSensor = OptionMenu(consulta, tkvar, *devnm)
    menuSensor.place(x='50', y='55')

    def change_dropdown(*args):
        global macactual
        nombreactual = tkvar.get()
        for item in devices:
            if item[2]==nombreactual: macactual = item[0]

    tkvar.trace('w', change_dropdown)

    boton_consulta = Button(consulta, text='Ejecutar consulta', cursor='hand2', command=lambda: graficos.consultadb(rootGraficos, ent_fecha_desde, ent_fecha_hasta, macactual, label_kw))
    boton_consulta.place(x='10', y='100')

    boton_exportar = Button(consulta, text='Exportar...', cursor='hand2', command=lambda: graficos.exportcsv(ent_fecha_desde, ent_fecha_hasta, macactual))
    boton_exportar.place(x='120', y='100')

    label_kw = Label(consulta, text= 'Consumo del periodo: 0 kW')
    label_kw.place(x='10', y='130')

    #   Valores
    label_valoreslogo = Label(valores, image=logo)
    label_valoreslogo.pack(side=BOTTOM)

    #   Construccion del menu
    newMenu = menu.MenuArgos(root)

    #   Inicio del lazo de GUI
    root.mainloop()


if __name__ == '__main__':
    argosmain()
