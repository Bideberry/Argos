import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import sqlite3
import csv
import time
import datetime
import calwidget
import server_argos



#   Variables globales
##For testing purposes
conn = sqlite3.connect('MyDatabase.sqlite')
c = conn.cursor()
clientsocket = 0
##Datos de mediciones
gt = []
gv = []
gi = []
gw = []
##MAC base para consulta
macactual = None
##Flags
running = False
connected = False



# Para prueba standalone de la clase graficos
class Widgets(tk.Frame):
    def __init__(self, master):
        botones = tk.Frame(master, height=100)
        botones.pack(side=tk.TOP, fill=tk.BOTH)

        self.dataview = tk.Frame(master)
        self.dataview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.newGraficos = Graficos(master)

        self.ent_fecha_desde = tk.Entry(botones)
        self.ent_fecha_desde.insert(0, str(datetime.datetime.now()-datetime.timedelta(days=1))[:-7])
        self.ent_fecha_desde.pack(side=tk.LEFT)
        boton_fecha_desde = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(botones, self.ent_fecha_desde))
        boton_fecha_desde.pack(side=tk.LEFT)

        self.ent_fecha_hasta = tk.Entry(botones)
        self.ent_fecha_hasta.pack(side=tk.LEFT)
        self.ent_fecha_hasta.insert(0, str(datetime.datetime.now())[:-7])
        boton_fecha_hasta = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(botones, self.ent_fecha_hasta))
        boton_fecha_hasta.pack(side=tk.LEFT)

        traer = tk.Button(botones, text='Traer Datos', command=lambda:consultadb(self.newGraficos, self.ent_fecha_desde, self.ent_fecha_hasta, macactual, self.kwhlabel))
        traer.pack(side=tk.LEFT)

        sync = tk.Button(botones, text='Sincronizar', command=lambda:sincronizar(master))
        sync.pack(side=tk.LEFT)

        rtmbutton = tk.Button(botones, text='  RTM  ', command=lambda:openrtm(master))
        rtmbutton.pack(side=tk.RIGHT)

        #Selector de sensor: inicio
        tkvar = tk.StringVar(botones)
        tkvar.set('Seleccione un sensor...')
        devices = []
        sql = "SELECT * FROM devices"
        for row in c.execute(sql):
            devices.append((row[0], row[1], row[2]))
        devnm = []
        for t in devices: devnm.append(t[2])
        menuSensor = tk.OptionMenu(botones, tkvar, *devnm)
        menuSensor.pack(side=tk.RIGHT)

        def change_dropdown(*args):
            global macactual
            nombreactual = tkvar.get()
            for item in devices:
                if item[2]==nombreactual: macactual = item[0]

        tkvar.trace('w', change_dropdown)
        #Selector de sensor: fin

        self.kwhlabel = tk.Label(botones, text='0 kW')
        self.kwhlabel.pack(side=tk.RIGHT)


class Graficos(tk.Frame):
    def __init__(self, master, **kw):
        self.master = master
        self.fig = Figure(figsize=(10,6), dpi=80)    #figura donde van los graficos
        self.fig.set_tight_layout(True)  #para que no se superpongan los titulos con los ejes (alternativa a tight_layout)
        self.canvas = FigureCanvasTkAgg(self.fig, self.master)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._newLayout()


    def _newLayout(self):
        self.vx = self._build_axes(self.fig, 311, 'Tension [V]')
        self.ix = self._build_axes(self.fig, 312, 'Corriente [A]')
        self.wx = self._build_axes(self.fig, 313, 'Potencia [W]')
        self.vx.set_ylim(bottom=0, ymax=max(gv, default=250)*1.1)  #grafico de tension arranca en cero
        self.ix.set_ylim(ymin=0, ymax=max(gi, default=1)*1.1)
        self.wx.set_ylim(ymin=0, ymax=max(gw, default=200)*1.1)

    def _build_axes(self, fig, pos, titulo):
        ax = fig.add_subplot(pos)
        ax.title.set_text(titulo)
        ax.grid(color='grey', linestyle='--', linewidth=0.2, alpha=0.5)
        ax.yaxis.set_major_locator(ticker.LinearLocator(8))
        return ax

    def _clearValues(self):
        gt.clear()
        gv.clear()
        gi.clear()
        gw.clear()

    def _getValues(self):
        self._clearValues()
        for row in c.execute(sql):
            gt.append(datetime.datetime.fromtimestamp(row[1]))
            gv.append(row[2]/100)
            gi.append(row[3]/1000)
            gw.append(row[2]*row[3]/100000)

    def update_plot(self):
        self.fig.clf()
        self._getValues()
        self._newLayout()
        self.vx.plot(gt, gv, 'C2')   #\
        self.ix.plot(gt, gi, 'C3')   # plot de graficos
        self.wx.plot(gt, gw, 'C4')   #/
        self.vx.get_shared_x_axes().join(self.vx, self.ix, self.wx) #eje x compartido
        self.canvas.draw()

    def getkwh(self):
        global gw
        kw = sum(gw)/1000
        kw = format(kw, '.2f')
        return kw


class RTM(tk.Frame):
    def __init__(self, master):
        global macactual
        self.master = master

        botones = tk.Frame(master, height=100)
        botones.pack(side=tk.TOP, fill=tk.BOTH)

        config = tk.LabelFrame(botones, text='Configuracion')
        config.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        umed = tk.LabelFrame(botones, text='Ultima medicion', height=100, width=300)
        umed.pack(side=tk.RIGHT, expand=False)

        self.dataview = tk.Frame(master)
        self.dataview.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.newGraficos = Graficos(self.dataview)

        #Selector de sensor: inicio
        label_sensor = tk.Label(config, text='Sensor:')
        label_sensor.pack(side=tk.LEFT)

        tkvar = tk.StringVar(config)
        tkvar.set('Seleccione un sensor...')
        devices = []
        sql = "SELECT * FROM devices"
        for row in c.execute(sql):
            devices.append((row[0], row[1], row[2]))
        devnm = []
        for t in devices: devnm.append(t[2])
        menuSensor = tk.OptionMenu(config, tkvar, *devnm)
        menuSensor.pack(side=tk.LEFT)

        def change_dropdown(*args):
            global macactual
            nombreactual = tkvar.get()
            for item in devices:
                if item[2]==nombreactual: macactual = item[0]

        tkvar.trace('w', change_dropdown)
        #Selector de sensor: fin

        ssbutton = tk.Button(config, text=' start/stop ', command=toggle)
        ssbutton.pack(side=tk.RIGHT, padx=20)

        clearbutton = tk.Button(config, text='  Borrar  ', command=self.borrar)
        clearbutton.pack(side=tk.RIGHT, padx=10)

        self.umedlabel = tk.Label(umed, justify=tk.LEFT, text=f'Tension: --  \t\t\n\nCorriente: --  \t\t\n\nPotencia: -- ')
        self.umedlabel.place(x='0', y='0')

        self.newGraficos._clearValues()
        self.newGraficos._newLayout()

        master.protocol("WM_DELETE_WINDOW", self.on_closing)


    def updatevalue(self, v, i, w):
        self.umedlabel.configure(text=f'Tension: {v} V \t\t\n\nCorriente: {i} A \t\t\n\nPotencia: {w} W')
        self.umedlabel.update()

    def borrar(self):
        self.newGraficos._clearValues()
        self.newGraficos.fig.clf()
        self.newGraficos._newLayout()

    def on_closing(self):
        try:
            global running, connected
            running = False
            connected = False
            server_argos.desconectar(clientsocket)
        except:
            # print('No socket open to close')
            pass
        self.master.destroy()


class BajaTension(tk.Frame):
    import calwidget
    def __init__(self, master):
        header = tk.Frame(master, height=200)
        header.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        botones = tk.Frame(header)
        botones.pack(side=tk.LEFT)
        calendario = tk.Frame(header)
        calendario.pack(side=tk.LEFT)
        self.mediciones = tk.Label(header)
        self.mediciones.pack(side=tk.RIGHT, padx=40)
        self.dataview = tk.Frame(master)
        self.dataview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(10,2), dpi=80)    #figura donde van los graficos
        self.fig.set_tight_layout(True)  #para que no se superpongan los titulos con los ejes (alternativa a tight_layout)
        self.canvas = FigureCanvasTkAgg(self.fig, self.dataview)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, self.dataview)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        self._newLayout()

        #Selector de sensor: inicio
        tkvar = tk.StringVar(botones)
        tkvar.set('Sensor...')
        devices = []
        sql = "SELECT * FROM devices"
        for row in c.execute(sql):
            devices.append((row[0], row[1], row[2]))
        devnm = []
        for t in devices: devnm.append(t[2])
        menuSensor = tk.OptionMenu(botones, tkvar, *devnm)
        menuSensor.grid(row='0', column='1', pady=15)

        def change_dropdown(*args):
            global macactual
            nombreactual = tkvar.get()
            for item in devices:
                if item[2]==nombreactual: macactual = item[0]

        tkvar.trace('w', change_dropdown)
        #Selector de sensor: fin

        label_desde = tk.Label(botones, text='Desde: ')
        label_desde.grid(row='1', column='0', pady=15)
        self.ent_fecha_desde = tk.Entry(botones)
        self.ent_fecha_desde.insert(0, str(datetime.datetime.now()-datetime.timedelta(days=1))[:-7])
        self.ent_fecha_desde.grid(row='1', column='1', pady=15)
        boton_fecha_desde = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(calendario, self.ent_fecha_desde))
        boton_fecha_desde.grid(row='1', column='2', pady=15)

        label_hasta = tk.Label(botones, text='Hasta: ')
        label_hasta.grid(row='2', column='0', pady=15)
        self.ent_fecha_hasta = tk.Entry(botones)
        self.ent_fecha_hasta.grid(row='2', column='1', pady=15)
        self.ent_fecha_hasta.insert(0, str(datetime.datetime.now())[:-7])
        boton_fecha_hasta = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(calendario, self.ent_fecha_hasta))
        boton_fecha_hasta.grid(row='2', column='2', pady=15)

        traer = tk.Button(botones, text='Buscar...', command=lambda:consultabt(self, self.ent_fecha_desde, self.ent_fecha_hasta, macactual, self.mediciones))
        traer.grid(row='0', column='2', pady=15)

    def _newLayout(self):
        self.vx = self._build_axes(self.fig, 111, 'Tension [V]')
        self.vx.set_ylim(bottom=0, ymax=max(gv, default=250)*1.1)  #grafico de tension arranca en cero

    def _build_axes(self, fig, pos, titulo):
        ax = fig.add_subplot(pos)
        ax.title.set_text(titulo)
        ax.grid(color='grey', linestyle='-', linewidth=0.2, alpha=0.5)
        ax.yaxis.set_major_locator(ticker.LinearLocator(8))
        return ax

    def _clearValues(self):
        gt.clear()
        gv.clear()

    def _getValues(self):
        self._clearValues()
        btl = []
        for row in c.execute(sql):
            btl.append(row)
        btl = sorted(btl, key=lambda med: med[1])
        for item in btl:
            gt.append(datetime.datetime.fromtimestamp(item[1]))
            gv.append(item[2]/100)

    def update_plot(self):
        self.fig.clf()
        self._getValues()
        self._newLayout()
        self.vx.plot(gt, gv, 'C2', marker='o', linestyle='')   #Solo grafico de tension
        self.canvas.draw()


class PicosConsumo(tk.Frame):
    def __init__(self, master):
        header = tk.Frame(master, height=200)
        header.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        botones = tk.Frame(header)
        botones.pack(side=tk.LEFT)
        calendario = tk.Frame(header)
        calendario.pack(side=tk.LEFT)
        self.mediciones = tk.Label(header)
        self.mediciones.pack(side=tk.RIGHT, padx=40)
        self.dataview = tk.Frame(master)
        self.dataview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(10,2), dpi=80)    #figura donde van los graficos
        self.fig.set_tight_layout(True)  #para que no se superpongan los titulos con los ejes (alternativa a tight_layout)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._newLayout()

        #Selector de sensor: inicio
        tkvar = tk.StringVar(botones)
        tkvar.set('Sensor...')
        devices = []
        sql = "SELECT * FROM devices"
        for row in c.execute(sql):
            devices.append((row[0], row[1], row[2]))
        devnm = []
        for t in devices: devnm.append(t[2])
        menuSensor = tk.OptionMenu(botones, tkvar, *devnm)
        menuSensor.grid(row='0', column='1', pady=15)

        def change_dropdown(*args):
            global macactual
            nombreactual = tkvar.get()
            for item in devices:
                if item[2]==nombreactual: macactual = item[0]

        tkvar.trace('w', change_dropdown)
        #Selector de sensor: fin

        label_desde = tk.Label(botones, text='Desde: ')
        label_desde.grid(row='1', column='0', pady=15)
        self.ent_fecha_desde = tk.Entry(botones)
        self.ent_fecha_desde.insert(0, str(datetime.datetime.now()-datetime.timedelta(days=1))[:-7])
        self.ent_fecha_desde.grid(row='1', column='1', pady=15)
        boton_fecha_desde = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(calendario, self.ent_fecha_desde))
        boton_fecha_desde.grid(row='1', column='2', pady=15)

        label_hasta = tk.Label(botones, text='Hasta: ')
        label_hasta.grid(row='2', column='0', pady=15)
        self.ent_fecha_hasta = tk.Entry(botones)
        self.ent_fecha_hasta.grid(row='2', column='1', pady=15)
        self.ent_fecha_hasta.insert(0, str(datetime.datetime.now())[:-7])
        boton_fecha_hasta = tk.Button(botones, text='...', command=lambda:calwidget.Calendar.pickdate(calendario, self.ent_fecha_hasta))
        boton_fecha_hasta.grid(row='2', column='2', pady=15)

        traer = tk.Button(botones, text='Buscar...', command=lambda:consultapc(self, self.ent_fecha_desde, self.ent_fecha_hasta, macactual, self.mediciones))
        traer.grid(row='0', column='2', pady=15)

    def _newLayout(self):
        self.wx = self._build_axes(self.fig, 111, 'Potencia [W]')
        self.wx.set_ylim(bottom=0, ymax=max(gw, default=250)*1.1)  #grafico de tension arranca en cero

    def _build_axes(self, fig, pos, titulo):
        ax = fig.add_subplot(pos)
        ax.title.set_text(titulo)
        ax.grid(color='grey', linestyle='-', linewidth=0.2, alpha=0.5)
        ax.yaxis.set_major_locator(ticker.LinearLocator(8))
        return ax

    def _clearValues(self):
        gt.clear()
        gw.clear()

    def _getValues(self):
        self._clearValues()
        picosl = []
        for row in c.execute(sql):
            picosl.append(row)
        picosl = sorted(picosl, key=lambda med: med[1])
        for item in picosl:
            gt.append(datetime.datetime.fromtimestamp(item[1]))
            gw.append(item[2]*item[3]/100000)

    def update_plot(self):
        self.fig.clf()
        self._getValues()
        self._newLayout()
        self.wx.plot(gt, gw, 'C4', marker='o', linestyle='')   #Solo grafico de tension
        self.canvas.draw()




# Funciones generales
def sincronizar(master):
    try:
        clientsocket, address, comando, mac, argc = server_argos.conectar()
    except:
        messagebox.showerror('Error de conexion', 'Verifique su conexion')
    if clientsocket:
        trama, cantidad = server_argos.leer(clientsocket, mac)
        messagebox.showinfo('Sincronización completa', f'Cargados {cantidad} registros en la base de datos')
    else:
        messagebox.showerror('Error', 'Error en la sincronización')

def consultadb(graph, entrydesde, entryhasta, mac, label):
    global sql
    x = entrydesde.get()
    y = entryhasta.get()
    try:
        mac = "'" + mac + "'" # Formato de mac para string sql
    except TypeError:
        messagebox.showwarning('Argos v2', 'Seleccione un dispositivo válido')
    # Chequeo que sea una fecha valida
    if x and y:
        desde = time.mktime(datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timetuple())
        hasta = time.mktime(datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S").timetuple())
        sql = "SELECT * FROM measures WHERE mac= " + mac + " AND time>=" + str(int(desde)) + " AND time<=" + str(int(hasta)) + " ORDER BY time ASC"
        if(DEBUG): print(sql)    # for debugging
        graph.update_plot()
        kw = graph.getkwh()
        label.configure(text=f'Consumo del peridodo: {kw} kW')
        label.update()
    else:
        print('Error de fecha') # luego será ventana de error

def consultabt(master, entrydesde, entryhasta, mac, mlabel):
    global sql
    x = entrydesde.get()
    y = entryhasta.get()
    try:
        mac = "'" + mac + "'" # Formato de mac para string sql
    except TypeError:
        messagebox.showwarning('Argos v2', 'Seleccione un dispositivo válido')
    # Chequeo que sea una fecha valida
    if x and y:
        desde = time.mktime(datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timetuple())
        hasta = time.mktime(datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S").timetuple())
        sql = "SELECT * FROM measures WHERE mac= " + mac + " AND time>=" + str(int(desde)) + " AND time<=" + str(int(hasta)) + " AND voltage > 100 ORDER BY voltage ASC LIMIT 10"
        if(DEBUG): print(sql)    # for debugging
        master.update_plot()
        mediciones = []
        for row in c.execute(sql):
            mediciones.append(f'Fecha: {datetime.datetime.fromtimestamp(row[1])} -- Tension: {row[2]/100 :.2f}')
        mlabel.config(justify='left', text=f' {mediciones[0]}\n {mediciones[0]}\n {mediciones[1]}\n {mediciones[2]}\n {mediciones[3]}\n {mediciones[4]}\n {mediciones[5]}\n {mediciones[6]}\n {mediciones[7]}\n {mediciones[8]}\n {mediciones[9]}')
        mlabel.update()
    else:
        print('Error de fecha') # luego será ventana de error

def consultapc(master, entrydesde, entryhasta, mac, mlabel):
    global sql
    x = entrydesde.get()
    y = entryhasta.get()
    try:
        mac = "'" + mac + "'" # Formato de mac para string sql
    except TypeError:
        messagebox.showwarning('Argos v2', 'Seleccione un dispositivo válido')
    # Chequeo que sea una fecha valida
    if x and y:
        desde = time.mktime(datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timetuple())
        hasta = time.mktime(datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S").timetuple())
        sql = "SELECT mac, time, voltage, current, voltage*current AS 'power' FROM measures WHERE mac= " + mac + " AND time>=" + str(int(desde)) + " AND time<=" + str(int(hasta)) + " ORDER BY power DESC LIMIT 10"
        if(DEBUG): print(sql)    # for debugging
        master.update_plot()
        mediciones = []
        for row in c.execute(sql):
            mediciones.append(f'Fecha: {datetime.datetime.fromtimestamp(row[1])} -- Potencia: {row[2]*row[3]/100000 :.2f}')
        mlabel.config(justify='left', text=f' {mediciones[0]}\n {mediciones[0]}\n {mediciones[1]}\n {mediciones[2]}\n {mediciones[3]}\n {mediciones[4]}\n {mediciones[5]}\n {mediciones[6]}\n {mediciones[7]}\n {mediciones[8]}\n {mediciones[9]}')
        mlabel.update()
    else:
        print('Error de fecha') # luego será ventana de error

def exportcsv(entrydesde, entryhasta, mac):
    global sql
    x = entrydesde.get()
    y = entryhasta.get()
    try:
        mac = "'" + mac + "'" # Formato de mac para string sql
    except TypeError:
        messagebox.showwarning('Argos v2', 'Seleccione un dispositivo válido')
    # Chequeo que sea una fecha valida
    if x and y:
        desde = time.mktime(datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timetuple())
        hasta = time.mktime(datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S").timetuple())
        sql = "SELECT * FROM measures WHERE mac= " + mac + " AND time>=" + str(int(desde)) + " AND time<=" + str(int(hasta)) + " ORDER BY time ASC"
        c.execute(sql)
        rows = c.fetchall()
    if rows:
        filename = f'Argos_bk.csv'
        with open(filename, 'w', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=';', lineterminator='\n', quoting=csv.QUOTE_NONE)  #delimiter=';' porque es windows europeo
            filewriter.writerow(['Argos', 'Industria Argentina'])
            filewriter.writerow(['Nombre del sensor:', mac])
            filewriter.writerow(['Desde:', x])
            filewriter.writerow(['Hasta:', y])
            filewriter.writerow([])
            filewriter.writerow(['Fecha y hora', 'Tension [V]', 'Corriente [A]', 'Potencia [W]'])
            for row in rows:
                filewriter.writerow([datetime.datetime.fromtimestamp(row[1]), row[2]/100, row[3]/1000, row[2]*row[3]/100000])
                if(DEBUG): print(f'{datetime.datetime.fromtimestamp(row[1])} {row[2]/100} {row[3]/1000} {row[2]*row[3]/100000}')
        messagebox.showinfo('Exportar', 'La operación has sido realizada con éxito. \nEl archivo ha sido generado en la carpeta del programa')


def toggle():
    global running, clientsocket
    if running:
        connected = False
        running = False
    else:
        running = True

def monitor(ventana):
    global connected, clientsocket
    if not connected:
        ventana.master.config(cursor='wait')
        ventana.master.update()
        try:
            clientsocket, address, comando, mac, argc = server_argos.conectar()
            connected = True
        except:
            messagebox.showerror('Erorr', 'No se pudo conectar. Verifique la conexión de red')
    ventana.master.config(cursor='')
    tension, corriente = server_argos.realtime(clientsocket)
    gt.append(datetime.datetime.now())
    gv.append(tension/100)
    gi.append(corriente/1000)
    gw.append(tension * corriente / 100000)

def startanimation(ventana):
    graph = ventana.newGraficos
    def animate(i):
        if running :
            graph.fig.clf()
            monitor(ventana)
            graph._newLayout()
            graph.vx.plot(gt, gv, 'C2')   #\
            graph.ix.plot(gt, gi, 'C3')   # plot de graficos
            graph.wx.plot(gt, gw, 'C4')   #/
            graph.vx.get_shared_x_axes().join(graph.vx, graph.ix, graph.wx) #eje x compartido
            ventana.updatevalue(gv[-1], gi[-1], gw[-1])


    ani = animation.FuncAnimation(graph.fig, animate, interval=1000)
    return ani  # Si no devuelvo esto no funciona (garbage collected al salir del method startanimation)


def opennormal(master):
    global rootanimation
    newwin = tk.Toplevel(master)
    newWidgets = Widgets(newwin)

def openrtm(master):
    global rootanimation
    newWin = tk.Toplevel(master)
    newRTM = RTM(newWin)
    rootanimation = startanimation(newRTM)

def openbajat(master):
    newwin = tk.Toplevel(master)
    newBT = BajaTension(newwin)

def openpicos(master):
    newwin = tk.Toplevel(master)
    newPicos = PicosConsumo(newwin)


def comingsoon():
    messagebox.showinfo('Argos v2', 'Proximamente...')


rootanimation = None

def test():

    root = tk.Tk()

    boton1 = tk.Button(root, text='  Normal  ', command=lambda:opennormal(root))
    boton1.pack(side=tk.LEFT, padx=20)

    boton2 = tk.Button(root, text='Baja tension', command=lambda:openbajat(root))
    boton2.pack(side=tk.LEFT, padx=20)

    boton3 = tk.Button(root, text='Picos de consumo', command=lambda:openpicos(root))
    boton3.pack(side=tk.LEFT, padx=20)

    root.mainloop()


if __name__ == '__main__':
    test()
