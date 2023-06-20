from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog, QLineEdit, QPushButton, QVBoxLayout
    )
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import sys
from time import time, sleep
from numpy import linspace
from random import random, randint
from functools import partial

from src.plots.plot_window_view import Ui_MainWindow as PlotWindow
from src.plots.pasive_plot import Ui_MainWindow as ReferencePlot

from src.route import calculate_route
from src.cinematica import change_to_joint_space
from numpy import gradient

signals = ['Radius', 'Incidence Angle', 'Jet Offset', 'Position', 'Mouth Pressure', 'Mass Flow Rate', 'Volume Flow Rate', 'Air Temperature', 'Sound Frequency', 'X Position', 'Z Position', 'Alpha Position']

class LivePlotWindow(QMainWindow, PlotWindow, QtCore.QThread):
    def __init__(self, app, measure, data, interval=10, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.interval = interval
        self.parent = parent
        self.app = app
        self.measures = [measure]
        self.traces = []
        if measure != 3:
            for i in range(len(signals)):
                if measure != i and i != 3:
                    self.traces.append(self.menuAdd_Trace.addAction(signals[i]))
                    self.traces[-1].triggered.connect(partial(self.add_trace, i))
        self.data = data
        # self.times = data['times'] 
        # self.radius = data['radius'] 
        # self.theta = data['theta'] 
        # self.offset = data['offset'] 
        # self.x_val = data['x'] 
        # self.z = data['z'] 
        # self.alpha = data['alpha'] 
        # self.mouth_pressure = data['mouth_pressure'] 
        # self.mass_flow = data['mass_flow'] 
        # self.flow_ref = data['flow_ref'] 
        # self.volume_flow = data['volume_flow'] 
        # self.temperature = data['temperature'] 
        # self.frequency = data['frequency'] 
        # self.x_ref = data['x_ref'] 
        # self.z_ref = data['z_ref'] 
        # self.alpha_ref = data['alpha_ref']


        #self.ptr = -self.windowWidth                      # set first x position
        self.curves = []
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w', (randint(0,255),randint(0,255),randint(0,255)), (randint(0,255),randint(0,255),randint(0,255)), (randint(0,255),randint(0,255),randint(0,255)), (randint(0,255),randint(0,255),randint(0,255))]

        for i in range(len(signals)):
            self.curves.append(self.graphicsView.plot(pen=pg.mkPen(colors[i], width=1)))
        self.ref_curve = self.graphicsView.plot(pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
        if measure == 3:
            self.graphicsView.setXRange(-1, 110, padding=0)
            self.graphicsView.setYRange(-1, 110, padding=0)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.interval)

        self.t0 = time()
        self.t = 0
    
    def add_trace(self, index):
        print(index)

    def update(self):
        for index in range(len(self.measures)):
            if self.measures[index] == 0: # Radius
                self.curves[index].setData(self.data['times'], self.data['radius'])
            elif self.measures[index] == 1: # Theta
                self.curves[index].setData(self.data['times'], self.data['theta'])
            elif self.measures[index] == 2: # Offset
                self.curves[index].setData(self.data['times'], self.data['offset'])
            elif self.measures[index] == 3: # Position
                self.curves[index].setData(self.data['x'], self.data['z'])
            elif self.measures[index] == 4: # Mouth Pressure
                self.curves[index].setData(self.data['times'], self.data['mouth_pressure'])
            elif self.measures[index] == 5: # Mass Flow
                self.curves[index].setData(self.data['times'], self.data['mass_flow'])
                self.ref_curve.setData(self.data['times'], self.data['flow_ref'])
            elif self.measures[index] == 6: # Volume Flow
                self.curves[index].setData(self.data['times'], self.data['volume_flow'])
            elif self.measures[index] == 7: # Temperature
                self.curves[index].setData(self.data['times'], self.data['temperature'])
            elif self.measures[index] == 8: # Frequency
                self.curves[index].setData(self.data['times'], self.data['frequency'])
            elif self.measures[index] == 9: # X
                self.curves[index].setData(self.data['times'], self.data['x'])
                self.ref_curve.setData(self.data['times'], self.data['x_ref'])
            elif self.measures[index] == 10: # Z
                self.curves[index].setData(self.data['times'], self.data['z'])
                self.ref_curve.setData(self.data['times'], self.data['z_ref'])
            elif self.measures[index] == 11: # Alpha
                self.curves[index].setData(self.data['times'], self.data['alpha'])
                self.ref_curve.setData(self.data['times'], self.data['alpha_ref'])
            
        self.app.processEvents()


class PassivePlotWindow(QMainWindow, ReferencePlot):
    def __init__(self, app, route1, route2, route3, parent=None, space=0):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.app = app
        self.route1 = route1
        self.route2 = route2
        self.route3 = route3
        self.space = space
        self.Fs = self.route1['Fs']
        
        try:
            if self.space == 0:
                t, f_r, p, vib, fil = calculate_route(self.route1)
                t, f_theta, p, vib, fil = calculate_route(self.route2)
                t, f_offset, p, vib, fil = calculate_route(self.route3)
                f_x, f_z, f_alpha = change_to_joint_space(f_r, f_theta, f_offset)
            elif self.space == 1:
                t, f_x, p, vib, fil = calculate_route(self.route1)
                t, f_z, p, vib, fil = calculate_route(self.route2)
                t, f_alpha, p, vib, fil = calculate_route(self.route3)
            self.time = t
            self.x_ref = f_x
            self.x_vel_ref = gradient(self.x_ref)*self.Fs
            self.z_ref = f_z
            self.z_vel_ref = gradient(self.z_ref)*self.Fs
            self.alpha_ref = f_alpha
            self.alpha_vel_ref = gradient(self.alpha_ref)*self.Fs

            colors = ['b', 'g', 'r', 'c', 'm', 'y']
            self.x_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[0], width=1))
            self.x_vel_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[1], width=1))
            self.z_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[2], width=1))
            self.z_vel_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[3], width=1))
            self.alpha_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[4], width=1))
            self.alpha_vel_curve = pg.PlotCurveItem(pen=pg.mkPen(colors[5], width=1))

            self.x_curve.setData(self.time, self.x_ref)
            self.x_vel_curve.setData(self.time, self.x_vel_ref)
            self.z_curve.setData(self.time, self.z_ref)
            self.z_vel_curve.setData(self.time, self.z_vel_ref)
            self.alpha_curve.setData(self.time, self.alpha_ref)
            self.alpha_vel_curve.setData(self.time, self.alpha_vel_ref)

            self.graphicsView.addItem(self.x_curve)
            self.graphicsView.addItem(self.x_vel_curve)

            self.xCheck.stateChanged.connect(self.x_checked)
            self.xVelCheck.stateChanged.connect(self.x_vel_checked)
            self.zCheck.stateChanged.connect(self.z_checked)
            self.zVelCheck.stateChanged.connect(self.z_vel_checked)
            self.alphaCheck.stateChanged.connect(self.alpha_checked)
            self.alphaVelCheck.stateChanged.connect(self.alpha_vel_checked)

            self.refreshButton.clicked.connect(self.refresh)
            self.problem = False
        except:
            self.problem = True
        

    def refresh(self):
        try:
            Fs = self.route1['Fs']
            if self.space == 0:
                t, f_r, p, vib, fil = calculate_route(self.route1)
                t, f_theta, p, vib, fil = calculate_route(self.route2)
                t, f_offset, p, vib, fil = calculate_route(self.route3)
                f_x, f_z, f_alpha = change_to_joint_space(f_r, f_theta, f_offset)
            elif self.space == 1:
                t, f_x, p, vib, fil = calculate_route(self.route1)
                t, f_z, p, vib, fil = calculate_route(self.route2)
                t, f_alpha, p, vib, fil = calculate_route(self.route3)
            time = t
            x_ref = f_x
            x_vel_ref = gradient(x_ref)*Fs
            z_ref = f_z
            z_vel_ref = gradient(z_ref)*Fs
            alpha_ref = f_alpha
            alpha_vel_ref = gradient(alpha_ref)*Fs

            self.x_curve.setData(time, x_ref)
            self.x_vel_curve.setData(time, x_vel_ref)
            self.z_curve.setData(time, z_ref)
            self.z_vel_curve.setData(time, z_vel_ref)
            self.alpha_curve.setData(time, alpha_ref)
            self.alpha_vel_curve.setData(time, alpha_vel_ref)
        except:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Couldn't calculate route.")
            msg.setInformativeText("There is a problem in the trajectory, a part of it is impossible to achieve. It is probably due to the relation between the lip-to-edge distance and the offset. Please check your requirements.")
            msg.setWindowTitle("Path error!")
            #msg.setDetailedText("The details are as follows:")
            retval = msg.exec_()
            self.close()

    def x_checked(self, value):
        if value:
            self.graphicsView.addItem(self.x_curve)
        else:
            self.graphicsView.removeItem(self.x_curve)

    def x_vel_checked(self, value):
        if value:
            self.graphicsView.addItem(self.x_vel_curve)
        else:
            self.graphicsView.removeItem(self.x_vel_curve)

    def z_checked(self, value):
        if value:
            self.graphicsView.addItem(self.z_curve)
        else:
            self.graphicsView.removeItem(self.z_curve)

    def z_vel_checked(self, value):
        if value:
            self.graphicsView.addItem(self.z_vel_curve)
        else:
            self.graphicsView.removeItem(self.z_vel_curve)

    def alpha_checked(self, value):
        if value:
            self.graphicsView.addItem(self.alpha_curve)
        else:
            self.graphicsView.removeItem(self.alpha_curve)

    def alpha_vel_checked(self, value):
        if value:
            self.graphicsView.addItem(self.alpha_vel_curve)
        else:
            self.graphicsView.removeItem(self.alpha_vel_curve)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window(app)
    win.show()

    sys.exit(app.exec())

# Import libraries
# from numpy import *
# from pyqtgraph.Qt import QtGui, QtCore
# import pyqtgraph as pg
# from random import random

# ### START QtApp #####
# app = QtGui.QApplication([])            # you MUST do this once (initialize things)
# ####################

# win = pg.GraphicsWindow(title="Signal from serial port") # creates a window
# p = win.addPlot(title="Realtime plot")  # creates empty space for the plot in the window
# curve = p.plot()                        # create an empty "plot" (a curve to plot)

# windowWidth = 500                       # width of the window displaying the curve
# Xm = linspace(0,0,windowWidth)          # create array that will contain the relevant time series     
# ptr = -windowWidth                      # set first x position

# # Realtime data plot. Each time this function is called, the data display is updated
# def update():
#     global curve, ptr, Xm    
#     Xm[:-1] = Xm[1:]                      # shift data in the temporal mean 1 sample left
#     value = 10 * random()                 # read line (single value) from the serial port
#     Xm[-1] = float(value)                 # vector containing the instantaneous values      
#     ptr += 1                              # update x position for displaying the curve
#     curve.setData(Xm)                     # set the curve with this data
#     curve.setPos(ptr,0)                   # set x position in the graph to 0
#     QtGui.QApplication.processEvents()    # you MUST process the plot now

# ### MAIN PROGRAM #####    
# # this is a brutal infinite loop calling your realtime data plot
# while True: update()

# ### END QtApp ####
# pg.QtGui.QApplication.exec_() # you MUST put this at the end
# ##################


# self.timer = QtCore.QTimer()
# self.timer.timeout.connect(self.update)
# self.timer.start(self.interval)