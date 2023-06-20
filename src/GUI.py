import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox, QFileDialog, QSplashScreen, QDesktopWidget
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import sys
from time import time, sleep
from numpy import linspace
from random import random, randint
from functools import partial
import json
import os
from datetime import date, datetime
from multiprocessing import Process, Event, Value, Pipe, Manager
import subprocess

from src.views.mainwindow import Ui_MainWindow as PlotWindow
from src.views.start_up_screen import Ui_Form as StartWindow
from src.route import *
from src.cinematica import *
from src.manual_move_win import *

from src.plots.plot_window import LivePlotWindow, PassivePlotWindow

from src.forms.forms import PointForm, VibratoForm, windows_vibrato, FilterForm, filter_windows, filter_choices, FuncTableForm, NoteForm, DurationForm, CorrectionForm, ScaleTimeForm, SettingsForm, TrillForm


class StartUpWindow(QSplashScreen, StartWindow):
    stop_playing = QtCore.pyqtSignal()
    def __init__(self, app, pipe, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.app = app
        self.pipe = pipe
    
    def set_progress(self, value):
        self.progressBar.setValue(int(value))

    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()

        widget = self.geometry()
        x = int(ag.width()/2 - widget.width()/2)
        y = int(ag.height()/2 - widget.height()/2)
        self.move(x, y)

    def wait_loading(self):
        progress = 10
        self.set_progress(10)
        while True:
            if self.pipe.poll(0.2):
                m = self.pipe.recv()
                if m[0] == "instances created":
                    progress += 10
                    self.instancesCheck.setChecked(True)
                elif m[0] == "x_driver_started":
                    progress += 10
                    self.XCheck.setChecked(True)
                elif m[0] == "z_driver_started":
                    progress += 10
                    self.ZCheck.setChecked(True)
                elif m[0] == "alpha_driver_started":
                    progress += 10
                    self.AlphaCheck.setChecked(True)
                elif m[0] == "memory_started":
                    progress += 10
                    self.memoryCheck.setChecked(True)
                elif m[0] == "microphone_started":
                    progress += 10
                    self.microphoneCheck.setChecked(True)
                elif m[0] == "flow_driver_started":
                    progress += 10
                    self.flowCheck.setChecked(True)
                elif m[0] == "pressure_sensor_started":
                    progress += 10
                    self.pressureCheck.setChecked(True)
                elif m[0] == "finger_driver_started":
                    progress += 10
                    self.fingersCheck.setChecked(True)
            self.set_progress(progress)
            if progress >= 100:
                self.close()
                break

class Window(QMainWindow, PlotWindow):
    stop_playing = QtCore.pyqtSignal()
    def __init__(self, app, running, musician_pipe, data, parent=None, connected=False):
        super().__init__(parent)
        self.setupUi(self)
        self.app = app
        self.route = []
        self.route2 = []
        self.route3 = []
        self.route4 = []
        self.route5 = []

        self.running = running
        self.musician_pipe = musician_pipe
        self.data = data
        self.connected = connected
        self.playing = threading.Event()

        self.graphicsView.setBackground('w')
        self.graphicsView_2.setBackground('w')
        self.graphicsView_3.setBackground('w')
        self.graphicsView_4.setBackground('w')
        self.graphicsView_5.setBackground('w')

        self.rule = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('m', width=2), label='t')
        self.rule2 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('m', width=2), label='t')
        self.rule3 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('m', width=2), label='t')
        self.rule4 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('m', width=2), label='t')
        self.rule5 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('m', width=2), label='t')
        self.graphicsView.addItem(self.rule)
        self.graphicsView_2.addItem(self.rule2)
        self.graphicsView_3.addItem(self.rule3)
        self.graphicsView_4.addItem(self.rule4)
        self.graphicsView_5.addItem(self.rule5)

        self.func1 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2))
        self.func1.setClickable(10)
        self.func1.sigClicked.connect(self.onCurveClicked)
        self.graphicsView.addItem(self.func1)
        self.graphicsView.setLabel('left', 'l', units='mm')

        self.r_real = pg.PlotCurveItem(pen=pg.mkPen('g', width=2))
        self.graphicsView.addItem(self.r_real)

        self.scatter1 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(30, 255, 35, 255))
        self.scatter1.sigClicked.connect(self.onPointsClicked)
        self.graphicsView.addItem(self.scatter1)

        self.vibscatter1 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(255, 35, 35, 255))
        self.vibscatter1.sigClicked.connect(self.onVibratoClicked)
        self.graphicsView.addItem(self.vibscatter1)

        self.filscatter1 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(35, 35, 255, 255))
        self.filscatter1.sigClicked.connect(self.onFilterClicked)
        self.graphicsView.addItem(self.filscatter1)

        ## 2
        self.func2 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2))
        self.func2.setClickable(10)
        self.func2.sigClicked.connect(self.onCurveClicked2)
        self.graphicsView_2.addItem(self.func2)
        self.graphicsView_2.setLabel('left', u"\u03b8", units='°')

        self.theta_real = pg.PlotCurveItem(pen=pg.mkPen('g', width=2))
        self.graphicsView_2.addItem(self.theta_real)
        
        self.scatter2 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(30, 255, 35, 255))
        self.scatter2.sigClicked.connect(self.onPointsClicked2)
        self.graphicsView_2.addItem(self.scatter2)

        self.vibscatter2 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(255, 35, 35, 255))
        self.vibscatter2.sigClicked.connect(self.onVibratoClicked2)
        self.graphicsView_2.addItem(self.vibscatter2)

        self.filscatter2 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(35, 35, 255, 255))
        self.filscatter2.sigClicked.connect(self.onFilterClicked2)
        self.graphicsView_2.addItem(self.filscatter2)

        ## 3
        self.func3 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2))
        self.func3.setClickable(10)
        self.func3.sigClicked.connect(self.onCurveClicked3)
        self.graphicsView_3.addItem(self.func3)
        self.graphicsView_3.setLabel('left', "Offset", units='mm')

        self.offset_real = pg.PlotCurveItem(pen=pg.mkPen('g', width=2))
        self.graphicsView_3.addItem(self.offset_real)
        
        self.scatter3 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(30, 255, 35, 255))
        self.scatter3.sigClicked.connect(self.onPointsClicked3)
        self.graphicsView_3.addItem(self.scatter3)

        self.vibscatter3 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(255, 35, 35, 255))
        self.vibscatter3.sigClicked.connect(self.onVibratoClicked3)
        self.graphicsView_3.addItem(self.vibscatter3)

        self.filscatter3 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(35, 35, 255, 255))
        self.filscatter3.sigClicked.connect(self.onFilterClicked3)
        self.graphicsView_3.addItem(self.filscatter3)

        ## 4
        self.func4 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2))
        self.func4.setClickable(10)
        self.func4.sigClicked.connect(self.onCurveClicked4)
        self.graphicsView_4.addItem(self.func4)
        self.graphicsView_4.setLabel('left', "Flow", units='SLPM')

        self.flow_real = pg.PlotCurveItem(pen=pg.mkPen('g', width=2))
        self.graphicsView_4.addItem(self.flow_real)

        self.scatter4 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(30, 255, 35, 255))
        self.scatter4.sigClicked.connect(self.onPointsClicked4)
        self.graphicsView_4.addItem(self.scatter4)

        self.vibscatter4 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(255, 35, 35, 255))
        self.vibscatter4.sigClicked.connect(self.onVibratoClicked4)
        self.graphicsView_4.addItem(self.vibscatter4)

        self.filscatter4 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(35, 35, 255, 255))
        self.filscatter4.sigClicked.connect(self.onFilterClicked4)
        self.graphicsView_4.addItem(self.filscatter4)

        ## 5
        self.func5 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2))
        self.func5.setClickable(10)
        self.func5.sigClicked.connect(self.onCurveClicked5)
        self.graphicsView_5.addItem(self.func5)
        self.graphicsView_5.setLabel('left', "Notes", units='n')
        self.graphicsView_5.getAxis('left').setTicks([dict_notes.items()])

        self.freq_real = pg.PlotCurveItem(pen=pg.mkPen('g', width=2))
        self.graphicsView_5.addItem(self.freq_real)
        
        self.scatter5 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(30, 255, 35, 255))
        self.scatter5.sigClicked.connect(self.onPointsClicked5)
        self.graphicsView_5.addItem(self.scatter5)

        self.horizontalSlider.valueChanged.connect(self.move_coursor)
        self.vibscatter5 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(255, 35, 35, 255))
        self.vibscatter5.sigClicked.connect(self.onVibratoClicked5)
        self.graphicsView_5.addItem(self.vibscatter5)

        # self.filscatter5 = pg.ScatterPlotItem(size=8, brush=pg.mkBrush(35, 35, 255, 255))
        # self.filscatter5.sigClicked.connect(self.onFilterClicked)
        # self.graphicsView_5.addItem(self.filscatter5)

        self.graphicsView.setXLink(self.graphicsView_2)
        self.graphicsView_2.setXLink(self.graphicsView_3)
        self.graphicsView_3.setXLink(self.graphicsView_4)
        self.graphicsView_4.setXLink(self.graphicsView_5)

        #self.graphicsView_2.hide()
        #self.graphicsView_3.hide()
        #self.graphicsView_4.hide()
        #self.graphicsView_5.hide()

        self.checkBox.stateChanged.connect(self.checkBox_clicked)
        self.checkBox_2.stateChanged.connect(self.checkBox2_clicked)
        self.checkBox_3.stateChanged.connect(self.checkBox3_clicked)
        self.checkBox_4.stateChanged.connect(self.checkBox4_clicked)
        self.checkBox_5.stateChanged.connect(self.checkBox5_clicked)

        #help(self.graphicsView.scene())
        
        #self.graphicsView.scene().sigMouseMoved.connect(self.mouse_moved)
        #self.graphicsView.scene().sigMouseHover.connect(self.mouse_hover)

        self.pointMenu = QMenu(self)
        self.movePoint = self.pointMenu.addAction("Move")
        self.editPoint = self.pointMenu.addAction("Edit")
        self.deletePoint = self.pointMenu.addAction("Delete")
        self.vibratoMenu = QMenu(self)
        self.moveVibrato = self.vibratoMenu.addAction("Move")
        self.editVibrato = self.vibratoMenu.addAction("Edit")
        self.deleteVibrato = self.vibratoMenu.addAction("Delete")
        self.filterMenu = QMenu(self)
        self.moveFilter = self.filterMenu.addAction("Move")
        self.editFilter = self.filterMenu.addAction("Edit")
        self.deleteFilter = self.filterMenu.addAction("Delete")
        self.graphMenu = QMenu(self)
        self.addPoint = self.graphMenu.addAction("Add point")
        self.addVibrato = self.graphMenu.addAction("Add vibrato")
        self.addFilter = self.graphMenu.addAction("Add filter")
        self.openTable = self.graphMenu.addAction("Open as table")
        self.noteMenu = QMenu(self)
        self.addNote = self.noteMenu.addAction("Add note")
        self.addTrill = self.noteMenu.addAction("Add trill")
        self.openNotesTable = self.noteMenu.addAction("Open as table")

        self.moving_point = [False for i in range(5)]
        self.moving_vibrato = [False for i in range(5)]
        self.moving_filter = [False for i in range(5)]
        self.segundo_click = [False for i in range(5)]

        self.moving_point_index = [0 for i in range(5)]
        self.moving_vibrato_index = [0 for i in range(5)]
        self.moving_filter_index = [0 for i in range(5)]

        self.graphicsView.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.graphicsView.scene().sigMouseMoved.connect(self.mouse_moved)

        self.graphicsView_2.scene().sigMouseClicked.connect(self.mouse_clicked2)
        self.graphicsView_2.scene().sigMouseMoved.connect(self.mouse_moved2)

        self.graphicsView_3.scene().sigMouseClicked.connect(self.mouse_clicked3)
        self.graphicsView_3.scene().sigMouseMoved.connect(self.mouse_moved3)

        self.graphicsView_4.scene().sigMouseClicked.connect(self.mouse_clicked4)
        self.graphicsView_4.scene().sigMouseMoved.connect(self.mouse_moved4)

        self.graphicsView_5.scene().sigMouseClicked.connect(self.mouse_clicked5)
        self.graphicsView_5.scene().sigMouseMoved.connect(self.mouse_moved5)

        self.statesFromNotesButton.clicked.connect(self.get_states_from_notes)
        self.changeDurationButton.clicked.connect(self.change_score_duration)
        self.addCorrectionButton.clicked.connect(self.add_correction)
        self.scaleTimeButton.clicked.connect(self.scale_time)
        self.seeMotorRefsButton.clicked.connect(self.see_motor_refs)
        self.manualControlButton.clicked.connect(self.open_manual_control)
        self.psControlButton.clicked.connect(self.ps_control)
        self.softStopButton.clicked.connect(self.soft_stop)
        self.process_running = Event()
        self.ps_serial1 = ""
        self.ps_tracked1 = False
        self.ps_serial2 = ""
        self.ps_tracked2 = False

        self.actionNew.triggered.connect(self.new_file)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_as.triggered.connect(self.save_as)
        self.actionOpen.triggered.connect(self.open)

        #self.checkPathButton.clicked.connect(self.check_path)
        self.goToCoursorButton.clicked.connect(self.go_to_coursor)
        self.playButton.clicked.connect(self.play)
        self.stopButton.clicked.connect(self.stop)
        self.stop_playing.connect(self.stop)
        self.clearPlotButton.clicked.connect(self.clear_plot)
        self.clearPlotButton.setEnabled(False)
        self.r_error_funcs = []
        self.theta_error_funcs = []
        self.offset_error_funcs = []

        self.base_path = os.path.dirname(os.path.realpath(__file__))
        self.filename = None
        self.find_recent_files()

        self.actionLip_to_edge_distance.triggered.connect(self.measure_radius)
        self.actionIncident_angle.triggered.connect(self.measure_theta)
        self.actionOffset.triggered.connect(self.measure_offset)
        self.actionPosition.triggered.connect(self.measure_position)
        self.actionMouth_Pressure.triggered.connect(self.measure_mouth_presure)
        self.actionMass_Flow_Rate.triggered.connect(self.measure_mass_flow_rate)
        self.actionVolume_Flow_Rate.triggered.connect(self.measure_volume_flow_rate)
        self.actionAir_Temperature.triggered.connect(self.measure_temperature)
        self.actionSound_Frequency.triggered.connect(self.measure_sound_frequency)
        self.actionX.triggered.connect(self.measure_x_position)
        self.actionZ.triggered.connect(self.measure_z_position)
        self.actionAlpha.triggered.connect(self.measure_alpha_position)

        self.undo_list = []
        self.redo_list = []
        self.actionUndo.triggered.connect(self.undo)
        self.actionRedo.triggered.connect(self.redo)
        self.space_of_instruction = 0
        self.actionChange_to_joint_space.triggered.connect(self.change_to_joint_space)
        self.actionChange_to_task_space.triggered.connect(self.change_to_task_space)

        self.actionSettings.triggered.connect(self.change_settings)

        #self.noteComboBox.addItems(list(dict_notes.values()))

        self.populate_graph()
        r = self.get_copy_of_routes(self.route, self.route2, self.route3, self.route4, self.route5)
        self.undo_list.append(r)
        
        self.reprint_plot_2()
        self.reprint_plot_3()
        self.reprint_plot_4()
        self.reprint_plot_5()
        self.reprint_plot_1()

        self.setWindowTitle("Pierre - Flutist Robot")
        self.file_saved = True
    
    def get_copy_of_routes(self, r1, r2, r3, r4, r5):
        r1_copy = {'total_t': r1['total_t'], 'Fs': r1['Fs'], 'points': r1['points'].copy(), 'filters': r1['filters'].copy(), 'vibrato': r1['vibrato'].copy(), 'history': r1['history'].copy()}
        r2_copy = {'total_t': r2['total_t'], 'Fs': r2['Fs'], 'points': r2['points'].copy(), 'filters': r2['filters'].copy(), 'vibrato': r2['vibrato'].copy(), 'history': r2['history'].copy()}
        r3_copy = {'total_t': r3['total_t'], 'Fs': r3['Fs'], 'points': r3['points'].copy(), 'filters': r3['filters'].copy(), 'vibrato': r3['vibrato'].copy(), 'history': r3['history'].copy()}
        r4_copy = {'total_t': r4['total_t'], 'Fs': r4['Fs'], 'points': r4['points'].copy(), 'filters': r4['filters'].copy(), 'vibrato': r4['vibrato'].copy(), 'history': r4['history'].copy()}
        r5_copy = {'total_t': r5['total_t'], 'Fs': r5['Fs'], 'notes': r5['notes'].copy(), 'trill': r5['trill'].copy(), 'history': r5['history'].copy()}
        return [r1_copy, r2_copy, r3_copy, r4_copy, r5_copy]
        #print(len(self.undo_list), len(self.redo_list))

    def ps_control(self):
        self.process_running.set()
        thread = threading.Thread(target=self.psmove)
        thread.start()

    def get_l_theta_of_ps(self, x,z,alpha,xf,zf):
        alpha_f = pi/4
        alpha = alpha * pi / 180
        theta = alpha + alpha_f
        l = (xf - x) * cos(alpha) + (zf - z) * sin(alpha)
        of = - (xf - x) * sin(alpha) + (zf - z) * cos(alpha)
        return l, theta*180/pi, of
    
    def psmove(self):
        # Ejecutar el programa C precompilado
        #process = subprocess.call("C:/Users/ferna/Documents/psmoveapi/build-x64/psmove.exe test-tracker", stdout=subprocess.PIPE)
        process = subprocess.Popen("C:/Users/ferna/Documents/psmoveapi/build-x64/psmove.exe test-tracker", stdout=subprocess.PIPE)
        
        self.ps_l_hist = self.data['radius'][-1]*np.ones([1000])
        self.ps_theta_hist = self.data['theta'][-1]*np.ones([1000])
        self.ps_of_hist = self.data['offset'][-1]*np.ones([1000])

        Fs = 100
        fp = 0.05
        fs = 0.1
        fc = (fp+fs)/2
        n  = 100

        self.ps_flt = signal.firwin(numtaps=n, cutoff=fc, window="hamming", pass_zero="lowpass", fs=Fs)
        self.ps_A = [1] +  [0 for i in range(n-1)]

        # self.ps_w, self.ps_gd = signal.group_delay((self.ps_flt, self.ps_A), fs=Fs)
        
        while self.process_running.is_set():
            # Leer la salida del programa C
            output = process.stdout.readline().decode("utf-8").strip()
            
            # Comprobar si se ha alcanzado el estado final
            if output == "estado_final":
                break
            
            # Hacer algo con el estado
            palabras = output.split()
            if palabras[0] == "state":
                self.ps_serial1 = palabras[1]
                self.ps_trigger_v = int(palabras[2]) / 255
                self.ps_accel_x = int(palabras[3]) / 4500
                self.ps_accel_y = int(palabras[4]) / 4500
                self.ps_accel_z = int(palabras[5]) / 4500
                self.ps_gyro_x = int(palabras[6]) / 4500
                self.ps_gyro_y = int(palabras[7]) / 4500
                self.ps_gyro_z = int(palabras[8]) / 4500
                self.ps_magneto_x = int(palabras[9]) / 255
                self.ps_magneto_y = int(palabras[10]) / 255
                self.ps_magneto_z = int(palabras[11]) / 255
                botones = int(palabras[12], 16)
                self.ps_Btn_TRIANGLE = botones & 1 << 4 != 0
                self.ps_Btn_CIRCLE = botones & 1 << 5 != 0
                self.ps_Btn_CROSS = botones & 1 << 6 != 0
                self.ps_Btn_SQUARE = botones & 1 << 7 != 0

                self.ps_Btn_SELECT = botones & 1 << 8 != 0
                self.ps_Btn_START = botones & 1 << 11 != 0

                self.ps_Btn_PS = botones & 1 << 16 != 0
                self.ps_Btn_MOVE = botones & 1 << 19 != 0
                self.ps_Btn_T = botones & 1 << 20 != 0

                #self.request_gui_update.emit()
            elif palabras[0] == "state2":
                if palabras[1] == self.ps_serial1:
                    self.ps_tracked1 = palabras[2] == "1"
                    if self.ps_tracked1:
                        self.ps_x1 = float(palabras[3])
                        self.ps_y1 = float(palabras[4])
                        self.ps_r1 = float(palabras[5])
                else:
                    self.ps_serial2 = palabras[1]
                    self.ps_tracked2 = palabras[2] == "1"
                    if self.ps_tracked2:
                        self.ps_x2 = float(palabras[3])
                        self.ps_y2 = float(palabras[4])
                        self.ps_r2 = float(palabras[5])

            if self.ps_tracked1 and self.ps_tracked2 and self.ps_Btn_MOVE:
                flow = self.ps_trigger_v*50
                alpha = -self.ps_accel_y*45
                l, theta, of = self.get_l_theta_of_ps(self.ps_x1,self.ps_y1,alpha,self.ps_x2,self.ps_y2)
                of = of/30
                l  = max(0,l-20) / 10

                self.ps_theta_hist = np.hstack([self.ps_theta_hist[1:], theta])
                theta_filtrado = signal.lfilter(self.ps_flt, self.ps_A, self.ps_theta_hist)
                self.ps_l_hist = np.hstack([self.ps_l_hist[1:], l])
                l_filtrado = signal.lfilter(self.ps_flt, self.ps_A, self.ps_l_hist)
                self.ps_of_hist = np.hstack([self.ps_of_hist[1:], of])
                of_filtrado = signal.lfilter(self.ps_flt, self.ps_A, self.ps_of_hist)

                desired_state = State(l_filtrado[-1], theta_filtrado[-1], of_filtrado[-1], flow)
                self.musician_pipe.send(["move_to_final", desired_state])
            elif self.ps_tracked1 and self.ps_tracked2:
                self.ps_theta_hist = np.hstack([self.ps_theta_hist[1:], self.ps_theta_hist[-1]])
                self.ps_l_hist = np.hstack([self.ps_l_hist[1:], self.ps_l_hist[-1]])
                self.ps_of_hist = np.hstack([self.ps_of_hist[1:], self.ps_of_hist[-1]])

        # Esperar a que el proceso C termine
        process.kill()
        self.ps_tracked1 = False
        self.ps_tracked2 = False
        self.ps_serial1 = ""
        self.ps_serial2 = ""

        # Obtener el código de salida del programa C
        return_code = process.returncode
        print("Programa C terminado con código de salida:", return_code)

    def undo(self):
        if len(self.undo_list) >= 2:
            self.redo_list.append(self.undo_list.pop())
            r = self.get_copy_of_routes(self.undo_list[-1][0], self.undo_list[-1][1], self.undo_list[-1][2], self.undo_list[-1][3], self.undo_list[-1][4])
            self.route = r[0]
            self.route2 = r[1]
            self.route3 = r[2]
            self.route4 = r[3]
            self.route5 = r[4]
            self.reprint_plot_2()
            self.reprint_plot_3()
            self.reprint_plot_4()
            self.reprint_plot_5()
            self.reprint_plot_1()
            self.changes_made(from_hist=True)

    def redo(self):
        if len(self.redo_list) >= 1:
            to = self.redo_list.pop()
            self.undo_list.append(to)
            r = self.get_copy_of_routes(to[0], to[1], to[2], to[3], to[4])
            self.route = r[0]
            self.route2 = r[1]
            self.route3 = r[2]
            self.route4 = r[3]
            self.route5 = r[4]
            self.reprint_plot_2()
            self.reprint_plot_3()
            self.reprint_plot_4()
            self.reprint_plot_5()
            self.reprint_plot_1()
            self.changes_made(from_hist=True)

    def change_to_joint_space(self):
        self.space_of_instruction = 1
        self.graphicsView.setLabel('left', "X", units='mm')
        self.graphicsView_2.setLabel('left', "Z", units='mm')
        self.graphicsView_3.setLabel('left', "Alpha", units='°')
        self.checkBox.setText("X")
        self.checkBox_2.setText("Z")
        self.checkBox_3.setText("Alpha")
        # self.seeMotorRefsButton.setText(u"See r, \u03b8 and o")

    def change_to_task_space(self):
        self.space_of_instruction = 0
        self.graphicsView.setLabel('left', 'r', units='mm')
        self.graphicsView_2.setLabel('left', u"\u03b8", units='°')
        self.graphicsView_3.setLabel('left', "Offset", units='mm')
        self.checkBox.setText("Lip-to-edge distance")
        self.checkBox_2.setText("Angle of incidence")
        self.checkBox_3.setText("Offset")
        # self.seeMotorRefsButton.setText("See X, Z and Alpha")

    def soft_stop(self):
        self.musician_pipe.send(["stop"])
        if self.playing.is_set():
            self.stop()

    def open_manual_control(self):
        manual_control = ManualWindow(self.app, self.musician_pipe, self.data, parent=self)
        manual_control.setWindowTitle("Manual Control")
        manual_control.show()

    def clear_plot(self):
        self.r_real.setData([], [])
        self.theta_real.setData([], [])
        self.offset_real.setData([], [])
        self.flow_real.setData([], [])
        self.freq_real.setData([], [])
        self.clearPlotButton.setEnabled(False)
        
    def go_to_coursor(self):
        flow_route = []
        x_route = []
        z_route = []
        alpha_route = []
        notes = []

        Fs = self.route['total_t']
        t, f_flow, p, vib, fil = calculate_route(self.route4)
        t, f_notes, xp, yp, tx, ty = calculate_notes_route(self.route5)
        ti_index = int(len(t) * self.horizontalSlider.value() / 100)

        if self.space_of_instruction == 0:
            t, f_r, p, vib, fil = calculate_route(self.route)
            t, f_theta, p, vib, fil = calculate_route(self.route2)
            t, f_offset, p, vib, fil = calculate_route(self.route3)
            x_pos_ref, z_pos_ref, alpha_pos_ref = change_to_joint_space(f_r, f_theta, f_offset)
            desired_state = State(f_r[ti_index], f_theta[ti_index], f_offset[ti_index], 0)

        elif self.space_of_instruction == 1:
            t, x_pos_ref, p, vib, fil = calculate_route(self.route)
            t, z_pos_ref, p, vib, fil = calculate_route(self.route2)
            t, alpha_pos_ref, p, vib, fil = calculate_route(self.route3)
            desired_state = State(0, 0, 0, 0)
            desired_state.x = x_pos_ref[ti_index]
            desired_state.z = z_pos_ref[ti_index]
            desired_state.alpha = alpha_pos_ref[ti_index]

        x_pos_ref = mm2units(x_pos_ref)
        x_vel_ref = gradient(x_pos_ref)*Fs
        z_pos_ref = mm2units(z_pos_ref)
        z_vel_ref = gradient(z_pos_ref)*Fs
        alpha_pos_ref = angle2units(alpha_pos_ref)
        alpha_vel_ref = gradient(alpha_pos_ref)*Fs

        for i in range(len(t) - ti_index):
            flow_route.append([t[i], f_flow[i + ti_index]])
            x_route.append([t[i], x_pos_ref[i + ti_index], x_vel_ref[i + ti_index]])
            z_route.append([t[i], z_pos_ref[i + ti_index], z_vel_ref[i + ti_index]])
            alpha_route.append([t[i], alpha_pos_ref[i + ti_index], alpha_vel_ref[i + ti_index]])
            notes.append([t[i], f_notes[i + ti_index]])

        self.musician_pipe.send(["load_routes", x_route, z_route, alpha_route, flow_route, notes])
        self.musician_pipe.send(["move_to", desired_state, None, False, False, False, False, 50])
        x = threading.Thread(target=self.wait_musician_is_in_place, args=(desired_state,))
        x.start()

    def wait_musician_response(self):
        pass
    
    def wait_musician_is_in_place(self, desired_state):
        if self.connected:
            while True:
                if abs(self.data['x'][-1] - desired_state.x) < 0.5 and abs(self.data['z'][-1] - desired_state.z) < 0.5  and abs(self.data['alpha'][-1] - desired_state.alpha) < 1:
                    print(self.data['x'][-1] - desired_state.x, self.data['z'][-1] - desired_state.z, self.data['alpha'][-1] - desired_state.alpha)
                    self.playButton.setEnabled(True)
                    break
                sleep(0.1)
        else:
            self.playButton.setEnabled(True)

    def play(self):
        self.playing.set()
        self.clearPlotButton.setEnabled(False)
        rec = self.recordCheckBox.isChecked()
        self.musician_pipe.send(["start_loaded_script", rec])
        coursor = threading.Thread(target=self.move_coursor_and_plot, args=())
        coursor.start()
        self.stopButton.setEnabled(True)
        self.playButton.setEnabled(False)
        self.recordCheckBox.setEnabled(False)
    
    def move_coursor_and_plot(self):
        t, f_r, p, vib, fil = calculate_route(self.route)
        ti = int(len(t) * self.horizontalSlider.value() / 99)
        slider_initial_value = self.horizontalSlider.value()
        self.horizontalSlider.setEnabled(False)
        t_0 = time()
        r_plot = np.array([])
        theta_plot = np.array([])
        offset_plot = np.array([])
        flow_plot = np.array([])
        freq_plot = np.array([])
        t_plot = np.array([])
        last_t = self.data["times"][-1]
        first_t = self.data["times"][-1]
        while True:
            if self.playing.is_set():
                t_act = time() - t_0
                slider_move = slider_initial_value + (99 - slider_initial_value) * min(100, max(0, t_act / (t[-1] - t[ti])))
                self.horizontalSlider.setValue(int(slider_move))
                last_index = self.data["times"].searchsorted(last_t)
                try:
                    if self.space_of_instruction == 0:
                        r_plot = np.hstack([r_plot, self.data["radius"][last_index+1:]])
                        theta_plot = np.hstack([theta_plot, self.data["theta"][last_index+1:]])
                        offset_plot = np.hstack([offset_plot, self.data["offset"][last_index+1:]])
                    elif self.space_of_instruction == 1:
                        r_plot = np.hstack([r_plot, self.data["x"][last_index+1:]])
                        theta_plot = np.hstack([theta_plot, self.data["z"][last_index+1:]])
                        offset_plot = np.hstack([offset_plot, self.data["alpha"][last_index+1:]])
                    flow_plot = np.hstack([flow_plot, self.data["mass_flow"][last_index+1:]])
                    freq_plot = np.hstack([freq_plot, (12*np.log2(self.data["frequency"][last_index+1:]) - 12*np.log2(440*2**(-7/12))
) / 2])
                    t_plot = np.hstack([t_plot, self.data["times"][last_index+1:] - first_t + t[ti]])
                    # t_plot = np.hstack(t[ti], t[ti] + t_act, len(r_plot))
                    self.r_real.setData(t_plot, r_plot)
                    self.theta_real.setData(t_plot, theta_plot)
                    self.offset_real.setData(t_plot, offset_plot)
                    self.flow_real.setData(t_plot, flow_plot)
                    self.freq_real.setData(t_plot, freq_plot)
                except:
                    print("Hubo un error")
                last_t = self.data["times"][-1]
                if t_act + t[ti] > t[-1]:
                    self.stop_playing.emit()
                    break
                sleep(0.05)
            else:
                break
            
    def stop(self):
        self.playing.clear()
        rec = self.recordCheckBox.isChecked()
        self.musician_pipe.send(["stop_playing", rec])
        if rec:
            msg = QMessageBox()
            #msg.setIcon(QMessageBox.Critical)
            msg.setText("Save the data recorded during execution?")
            msg.setInformativeText("Data will be lost if you don't save them.")
            msg.setWindowTitle("Save data?")
            dont_save_button = msg.addButton("Don't save", QMessageBox.NoRole)
            save_button = msg.addButton("Save", QMessageBox.YesRole)

            retval = msg.exec_()
            if retval == 0: # don't save
                pass
            elif retval == 1: # save
                self.save_recorded_data()

        self.horizontalSlider.setEnabled(True)
        self.recordCheckBox.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.clearPlotButton.setEnabled(True)

    def save_recorded_data(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Open file', self.base_path,"CSV files (*.csv)")
        if fname[-4:] != '.csv':
            fname += '.csv'
        self.last_path = os.path.split(fname)[0]
        fname2, _ = QFileDialog.getSaveFileName(self, 'Open file', self.last_path,"WAV files (*.wav)")
        if fname2[-4:] != '.wav':
            fname2 += '.wav'
        self.last_path = os.path.split(fname2)[0]
        self.musician_pipe.send(["memory.save_recorded_data", fname, fname2])

    def check_path(self):
        for i in self.r_error_funcs:
            self.graphicsView.removeItem(i)
        # for i in self.theta_error_funcs:
        #     self.graphicsView_2.removeItem(i)
        for i in self.offset_error_funcs:
            self.graphicsView_3.removeItem(i)
        possible = True
        if self.space_of_instruction == 1:
            self.goToCoursorButton.setEnabled(True)
            self.seeMotorRefsButton.setEnabled(True)
        elif self.space_of_instruction == 0:
            t, f1, p, vib, fil = calculate_route(self.route)
            t, f2, p, vib, fil = calculate_route(self.route2)
            t, f3, p, vib, fil = calculate_route(self.route3)
            error = []
            for i in range(len(t)):
                try:
                    get_x_z_alpha(f1[i], f2[i], f3[i])
                except:
                    possible = False
                    error.append(i)
            if possible:
                self.goToCoursorButton.setEnabled(True)
                self.seeMotorRefsButton.setEnabled(True)
            else:
                all_areas = []
                last_area = []
                for i in range(len(error)):
                    last_area.append(error[i])
                    if i < len(error) - 1:
                        if error[i + 1] - 1 != error[i]:
                            all_areas.append(last_area)
                            last_area = []
                if len(last_area):
                    all_areas.append(last_area)
                for area in all_areas:
                    t_e = []
                    fr_e = []
                    #ft_e = []
                    fo_e = []
                    for i in area:
                        t_e.append(t[i])
                        fr_e.append(f1[i])
                        #ft_e.append(f2[i])
                        fo_e.append(f3[i])
                    func1 = pg.PlotCurveItem(pen=pg.mkPen((255,0,0,50), width=20))
                    #func2 = pg.PlotCurveItem(pen=pg.mkPen((255,0,0,50), width=20))
                    func3 = pg.PlotCurveItem(pen=pg.mkPen((255,0,0,50), width=20))
                    func1.setData(t_e, fr_e)
                    #func2.setData(t_e, ft_e)
                    func3.setData(t_e, fo_e)
                    self.graphicsView.addItem(func1)
                    #self.graphicsView_2.addItem(func2)
                    self.graphicsView_3.addItem(func3)
                    self.r_error_funcs.append(func1)
                    #self.theta_error_funcs.append(func2)
                    self.offset_error_funcs.append(func3)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        '''
        Esta función se ejecuta al cerrar el programa, para terminar todos los procesos que están corriendo
        '''
        self.playing.clear()
        self.running.clear()
        sleep(0.5)
        return super().closeEvent(a0)
    
    def change_settings(self):
        dlg = SettingsForm(parent=self)
        dlg.setWindowTitle("Settings")
        if dlg.exec():
            self.refresh_settings()

    def refresh_settings(self):
        self.musician_pipe.send(["x_driver.change_control", DATA["x_control"]])
        self.musician_pipe.send(["z_driver.change_control", DATA["z_control"]])
        self.musician_pipe.send(["alpha_driver.change_control", DATA["alpha_control"]])
        self.musician_pipe.send(["change_flute_pos", DATA["flute_position"]])
        self.musician_pipe.send(["microphone.change_frequency_detection", DATA["frequency_detection"]])

    def find_recent_files(self):
        '''
        Se usa esta función para encontrar los archivos guardados recientemente y añadirlos al menu de 'Recent Files'
        '''
        if 'recent_saves.txt' in os.listdir(self.base_path):
            recents = []
            with open(self.base_path + '/recent_saves.txt', 'r') as file:
                for line in file.readlines():
                    line = line.replace("\n", "")
                    if line in recents:
                        pass
                    else:
                        if len(recents) < 5:
                            recents.append(line)
                            head, tail = os.path.split(line)
                            editAct = self.menuOpen_recent.addAction(tail)
                            editAct.triggered.connect(partial(self.open, line))
        else:
            pass
    
    def new_file(self):
        '''
        Se usa esta función para comenzar una partitura nueva, si la actual no está guardada se ofrece la posibilidad de guardar los cambios antes de cerrarlos.
        '''
        if len(self.route['history']) != 0 or len(self.route2['history']) != 0 or len(self.route3['history']) != 0 or len(self.route4['history']) != 0 or len(self.route5['history']) != 0:
            msg = QMessageBox()
            msg.setText("Save changes to this score before creating a new file?")
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            msg.setWindowTitle("Save Score?")
            dont_save_button = msg.addButton("Don't save", QMessageBox.NoRole)
            cancel_button = msg.addButton("Cancel", QMessageBox.YesRole)
            save_button = msg.addButton("Save", QMessageBox.YesRole)

            retval = msg.exec_()
            if retval == 0: # don't save
                self.clean_score()
                self.filename = None
            elif retval == 1: # 
                pass
            elif retval == 2:
                self.save()
                self.clean_score()
                self.filename = None

    def save(self):
        '''
        Se usa esta función para guardar una partitura o los cambios realizados
        '''
        if len(self.route['history']) == 0 and len(self.route2['history']) == 0 and len(self.route3['history']) == 0 and len(self.route4['history']) == 0 and len(self.route5['history']) == 0:
            return False
        if self.filename:
            data = {'route_r': self.route, 'route_theta': self.route2, 'route_offset': self.route3, 'route_flow': self.route4, 'route_fingers': self.route5, 'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
            with open(self.filename, 'w') as file:
                json.dump(data, file, indent=4, sort_keys=True)
                self.changes_saved()
            if 'recent_saves.txt' in os.listdir(self.base_path):
                with open(self.base_path + '/recent_saves.txt', 'r+') as file:
                    content = file.read()
                    file.seek(0, 0)
                    file.write(self.filename + '\n' + content)
                # with open(self.base_path + '/utils/recent_saves.txt', 'a') as file:
                #     file.write('\n' + self.filename)
            else:
                with open(self.base_path + '/recent_saves.txt', 'w') as file:
                    file.write(self.filename)
        else:
            self.save_as()
        return True
        
    def save_as(self):
        '''
        Se usa esta función para guardar la partitura actual como un archivo nuevo.
        '''
        fname, _ = QFileDialog.getSaveFileName(self, 'Open file', self.base_path,"JSON files (*.json)")
        if fname != '':
            if fname[-5:] != '.json':
                fname += '.json'
            self.filename = fname
            #self.base_path = os.path.split(fname)[0]
            self.save()

    def clean_score(self):
        '''
        Se usa esta función para borrar todas las acciones ingresadas en una partitura
        '''
        self.populate_graph()
        self.horizontalSlider.setValue(0)
        self.clear_plot()
        self.reprint_plot_2()
        self.reprint_plot_3()
        self.reprint_plot_4()
        self.reprint_plot_5()
        self.reprint_plot_1()
        self.changes_saved()

    def open(self, fname=None):
        '''
        Se usa esta función para abrir una partitura que había sido guardada con anterioridad. Además, si hay trabajo sin guardar se ofrece la posibilidad de guardarlo antes de abrir el nuevo.
        '''
        if (len(self.route['history']) != 0 or len(self.route2['history']) != 0 or len(self.route3['history']) != 0 or len(self.route4['history']) != 0 or len(self.route5['history']) != 0) and not self.file_saved:
            msg = QMessageBox()
            #msg.setIcon(QMessageBox.Critical)
            msg.setText("Save changes to this score before opening other file?")
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            msg.setWindowTitle("Save Score?")
            dont_save_button = msg.addButton("Don't save", QMessageBox.NoRole)
            cancel_button = msg.addButton("Cancel", QMessageBox.YesRole)
            save_button = msg.addButton("Save", QMessageBox.YesRole)

            retval = msg.exec_()
            if retval == 0: # don't save
                self.clean_score()
                self.open(fname=fname)
            elif retval == 1: # 
                pass
            elif retval == 2:
                self.save()
                self.clean_score()
                self.open(fname=fname)
        else:
            if not fname:
                fname, _ = QFileDialog.getOpenFileName(self, 'Open file', self.base_path,"JSON files (*.json)")
            try:
                self.clean_score()
                with open(fname) as json_file:
                    data = json.load(json_file)
                    try:
                        self.route = data['route_r']
                        self.route2 = data['route_theta']
                        self.route3 = data['route_offset']
                        self.route4 = data['route_flow']
                        self.route5 = data['route_fingers']
                        self.reprint_plot_2()
                        self.reprint_plot_3()
                        self.reprint_plot_4()
                        self.reprint_plot_5()
                        self.reprint_plot_1()
                        self.filename = fname
                        self.changes_saved()
                    except:
                        self.clean_score()
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Critical)
                        msg.setText("Couldn't open file.")
                        msg.setInformativeText("File format does not coincide. Try with other file.")
                        msg.setWindowTitle("File Error")
                        #msg.setDetailedText("The details are as follows:")
                        retval = msg.exec_()
            except:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Couldn't find file.")
                msg.setInformativeText("Maybe the file was moved or removed.")
                msg.setWindowTitle("File not found")
                retval = msg.exec_()

    def changes_saved(self):
        '''
        Se llama esta función cuando la partitura no tiene cambios respecto a la versión guardada.
        '''
        self.setWindowTitle("Pierre - Flutist Robot")
        self.file_saved = True

    def changes_made(self, from_hist=False):
        '''
        Se llama esta función cuando la partitura sufre algun cambio.
        '''
        self.setWindowTitle("Pierre - Flutist Robot*")
        #self.goToCoursorButton.setEnabled(False)
        self.seeMotorRefsButton.setEnabled(False)
        self.file_saved = False
        if not from_hist:
            r = self.get_copy_of_routes(self.route, self.route2, self.route3, self.route4, self.route5)
            self.undo_list.append(r)
            self.redo_list = []

    def change_score_duration(self):
        data = [self.route['total_t']]
        dlg = DurationForm(parent=self, data=data)
        dlg.setWindowTitle("Change score duration")
        if dlg.exec():
            new_dur = data[0]
            self.route['total_t'] = new_dur
            self.route2['total_t'] = new_dur
            self.route3['total_t'] = new_dur
            self.route4['total_t'] = new_dur
            self.route5['total_t'] = new_dur
            self.reprint_plot_2()
            self.reprint_plot_3()
            self.reprint_plot_4()
            self.reprint_plot_5()
            self.reprint_plot_1()

    def add_correction(self):
        data = [0,0,0,0,0,0,0,0,0,0]
        dlg = CorrectionForm(parent=self, data=data, space=self.space_of_instruction)
        dlg.setWindowTitle("Add correction to states")
        if dlg.exec():
            r_dis = data[0]
            theta_dis = data[1]
            offset_dis = data[2]
            flow_dis = data[3]
            notes_dis = data[4]
            r_t_dis = data[5]
            theta_t_dis = data[6]
            offset_t_dis = data[7]
            flow_t_dis = data[8]
            notes_t_dis = data[9]
            for p in self.route['points']:
                p[0] += r_t_dis
                p[0] = min(self.route['total_t'], max(p[0], 0))
                p[1] += r_dis
            for p in self.route2['points']:
                p[0] += theta_t_dis
                p[0] = min(self.route['total_t'], max(p[0], 0))
                p[1] += theta_dis
            for p in self.route3['points']:
                p[0] += offset_t_dis
                p[0] = min(self.route['total_t'], max(p[0], 0))
                p[1] += offset_dis
            for p in self.route4['points']:
                p[0] += flow_t_dis
                p[0] = min(self.route['total_t'], max(p[0], 0))
                p[1] += flow_dis
            for p in self.route5['notes']:
                n = dict_notes_rev[p[1]]
                p[0] += notes_t_dis
                p[0] = min(self.route['total_t'], max(p[0], 0))
                p[1] = dict_notes[round((n + notes_dis/2)*2) / 2]
            self.reprint_plot_2()
            self.reprint_plot_3()
            self.reprint_plot_4()
            self.reprint_plot_5()
            self.reprint_plot_1()

    def scale_time(self):
        data = [1]
        dlg = ScaleTimeForm(parent=self, data=data)
        dlg.setWindowTitle("Scale time of score")
        if dlg.exec():
            scale = data[0]
            for route in [self.route, self.route2, self.route3, self.route4]:
                route['total_t'] *= scale
                for p in route['points']:
                    p[0] *= scale
                for v in route['vibrato']:
                    v[0] *= scale
                    v[1] *= scale
                for f in route['filters']:
                    f[0] *= scale
                    f[1] *= scale
            
            self.route5['total_t'] *= scale
            for p in self.route5['notes']:
                p[0] *= scale
            
            self.reprint_plot_2()
            self.reprint_plot_3()
            self.reprint_plot_4()
            self.reprint_plot_5()
            self.reprint_plot_1()

    def see_motor_refs(self):
        plotwin = PassivePlotWindow(self.app, self.route, self.route2, self.route3, parent=self, space=self.space_of_instruction)
        if plotwin.problem:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Couldn't calculate route.")
            msg.setInformativeText("There is a problem in the trajectory, a part of it is impossible to achieve. It is probably due to the relation between the lip-to-edge distance and the offset. Please check your requirements.")
            msg.setWindowTitle("Path error!")
            #msg.setDetailedText("The details are as follows:")
            retval = msg.exec_()
        else:
            plotwin.setWindowTitle("Motors references")
            plotwin.show()

    def get_states_from_notes(self):
        global LOOK_UP_TABLE
        self.route['points'] = []
        self.route2['points'] = []
        self.route3['points'] = []
        self.route4['points'] = []
        for i in range(len(self.route5['notes'])):
            t = self.route5['notes'][i][0]
            n = self.route5['notes'][i][1]
            self.add_item(0, 0, [t, LOOK_UP_TABLE[n]['l']], from_func=True)
            self.add_item(1, 0, [t, LOOK_UP_TABLE[n]['theta']], from_func=True)
            self.add_item(2, 0, [t, LOOK_UP_TABLE[n]['offset']], from_func=True)
            self.add_item(3, 0, [t, LOOK_UP_TABLE[n]['flow']], from_func=True)
        self.changes_made()

    def move_coursor(self, value):
        t = self.route['total_t'] * value / 99
        self.rule.setPos(t)
        self.rule2.setPos(t)
        self.rule3.setPos(t)
        self.rule4.setPos(t)
        self.rule5.setPos(t)
        self.playButton.setEnabled(False)

    def onFilterClicked(self, obj, point, event):
        if not self.moving_point[0] and not self.moving_vibrato[0] and not self.moving_filter[0]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.filterMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.moveFilter:
                self.changes_made()
                self.moving_filter[0] = True
                self.moving_filter_index[0] = self.find_closest_filter(self.route['filters'], x)
            elif action == self.editFilter:
                index = self.find_closest_filter(self.route['filters'], x)
                data = [0, 0] + [0 for i in range(14)] # time_i, time_f, filter_choice, window_choice, window_n, cutoff, Ap, As, fp, fs, chebN, chebAp, chebAs, chebfp, chebfs, chebrp
                new_data = self.route['filters'][index] # i_init, i_end, filter, params
                data[0] = new_data[0]
                data[1] = new_data[1]
                data[2] = filter_choices.index(new_data[2])
                if data[2] == 0:
                    data[3] = filter_windows.index(new_data[3][0])
                    data[4] = new_data[3][1]
                    data[5] = new_data[3][2]
                elif data[2] == 3:
                    data[10] = new_data[3][0]
                    data[11] = new_data[3][1]
                    data[12] = new_data[3][2]
                    data[13] = new_data[3][3]
                    data[14] = new_data[3][4]
                    data[15] = new_data[3][5]
                else:
                    data[6] = new_data[3][0]
                    data[7] = new_data[3][1]
                    data[8] = new_data[3][2]
                    data[9] = new_data[3][3]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.edit_item(0, 2, index, [time_i, time_f, filter_choice, params])
                            break
                        except:
                            self.route['filters'][index] = new_data
                            self.route['filters'].sort(key=lambda x: x[0])
                    else:
                        break
            elif action == self.deleteFilter:
                index = self.find_closest_filter(self.route['filters'], x)
                p = self.route['filters'][index]
                self.route['filters'].remove(p)
                self.route['history'].append(['delete_filter', p])
                self.reprint_plot_1()
                self.changes_made()
        else:
            self.moving_point[0] = False
            self.moving_vibrato[0] = False
            self.moving_filter[0] = False
            self.segundo_click[0] = False

    def onVibratoClicked(self, obj, point, event):
        if not self.moving_point[0] and not self.moving_vibrato[0] and not self.moving_filter[0]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.vibratoMenu.exec_(QtCore.QPoint(x_screen,y_screen))

            if action == self.moveVibrato:
                self.changes_made()
                self.moving_vibrato[0] = True
                self.moving_vibrato_index[0] = self.find_closest_vibrato(self.route['vibrato'], x)
            elif action == self.editVibrato:
                index = self.find_closest_vibrato(self.route['vibrato'], x)
                data = self.route['vibrato'][index]
                data[4] = windows_vibrato.index(data[4])
                dlg = VibratoForm(parent=self, data=data, max_t=self.route['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.edit_item(0, 1, index, [time_i, duration, amp, freq, window_v])
            elif action == self.deleteVibrato:
                index = self.find_closest_vibrato(self.route['vibrato'], x)
                p = self.route['vibrato'][index]
                self.route['vibrato'].remove(p)
                self.route['history'].append(['delete_vibrato', p])
                self.reprint_plot_1()
                self.changes_made()
        else:
            self.moving_point[0] = False
            self.moving_vibrato[0] = False
            self.moving_filter[0] = False
            self.segundo_click[0] = False
        
    def onCurveClicked(self, obj, event):
        if not self.moving_point[0] and not self.moving_vibrato[0] and not self.moving_filter[0]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.graphMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.addPoint:
                self.route['points'].append([x, y])
                self.route['points'].sort(key=lambda x: x[0])
                self.route['history'].append(['add_point', [x, y]])
                self.reprint_plot_1()
                self.changes_made()
            elif action == self.addVibrato:
                data=[x, 0, 0, 0, 0]
                dlg = VibratoForm(parent=self, data=data, max_t=self.route['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.route['vibrato'].append([time_i, duration, amp, freq, window_v])
                    self.route['history'].append(['vibrato', [time_i, duration, amp, freq, window_v]])
                    self.reprint_plot_1()
                    self.changes_made()
            elif action == self.addFilter:
                data=[x, x] + [0 for i in range(14)]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.route['filters'].append([time_i, time_f, filter_choice, params])
                            self.route['history'].append(['filter', [time_i, time_f, filter_choice, params]])
                            self.reprint_plot_1()
                            self.changes_made()
                            break
                        except:
                            self.route['filters'].remove([time_i, time_f, filter_choice, params])
                            self.route['history'].remove(['filter', [time_i, time_f, filter_choice, params]])
                    else:
                        break
                    
            elif action == self.openTable:
                data = [0, 0, self.route, self.route2, self.route3, self.route4, self.route5]
                dlg = FuncTableForm(parent=self, data=data)
                dlg.setWindowTitle("Function as table")
                if dlg.exec():
                    pass
        else:
            self.moving_point[0] = False
            self.moving_vibrato[0] = False
            self.moving_filter[0] = False
            self.segundo_click[0] = False

    def onPointsClicked(self, obj, point, event):
        if not self.moving_point[0] and not self.moving_vibrato[0] and not self.moving_filter[0]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.pointMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.movePoint:
                self.changes_made()
                self.moving_point[0] = True
                self.moving_point_index[0] = self.find_closest_point(self.route['points'], x, y)
            elif action == self.editPoint:
                index = self.find_closest_point(self.route['points'], x, y)
                data = self.route['points'][index]
                dlg = PointForm(parent=self, data=data, max_t=self.route['total_t'])
                dlg.setWindowTitle("Add Point")
                if dlg.exec():
                    self.edit_item(0, 0, index, data)
            elif action == self.deletePoint:
                p = self.route['points'][self.find_closest_point(self.route['points'], x, y)]
                self.route['points'].remove(p)
                self.route['history'].append(['delete_point', p])
                self.changes_made()
                try:
                    self.reprint_plot_1()
                except:
                    pass
        else:
            self.moving_point[0] = False
            self.moving_vibrato[0] = False
            self.moving_filter[0] = False
            self.segundo_click[0] = False

    def mouse_moved(self, event):
        if self.moving_point[0]:
            self.segundo_click[0] = True
            vb = self.graphicsView.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = max(0,round(mouse_point.y(), 2))
            min_x, max_x = self.find_moving_point_limits(self.route['points'], self.moving_point_index[0], self.route['total_t'])
            if x > min_x and x < max_x:
                self.route['points'][self.moving_point_index[0]] = [x, y]
                self.reprint_plot_1()
        if self.moving_vibrato[0]:
            self.segundo_click[0] = True
            vb = self.graphicsView.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_vibrato_limits(self.route['vibrato'], self.moving_vibrato_index[0], self.route['total_t'])
            if x >= min_x and x <= max_x:
                self.route['vibrato'][self.moving_vibrato_index[0]][0] = x
                self.reprint_plot_1()
        if self.moving_filter[0]:
            self.segundo_click[0] = True
            vb = self.graphicsView.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_filter_limits(self.route['filters'], self.moving_filter_index[0], self.route['total_t'])
            if x >= min_x and x <= max_x:
                diff = self.route['filters'][self.moving_filter_index[0]][1] - self.route['filters'][self.moving_filter_index[0]][0]
                self.route['filters'][self.moving_filter_index[0]][0] = x
                self.route['filters'][self.moving_filter_index[0]][1] = x + diff
                self.reprint_plot_1()

    def mouse_clicked(self, event):
        #print(event.scenePos())

        if (self.moving_point[0] or self.moving_vibrato[0] or self.moving_filter[0]) and self.segundo_click[0]:
            self.moving_point[0] = False
            self.moving_vibrato[0] = False
            self.moving_filter[0] = False
            self.segundo_click[0] = False
        else:
            if event.double():
                vb = self.graphicsView.plotItem.vb
                mouse_point = vb.mapSceneToView(event.scenePos())
                x = round(mouse_point.x(), 2)
                y = max(0,round(mouse_point.y(), 2))
                self.route['points'].append([x, y])
                self.route['points'].sort(key=lambda x: x[0])
                self.route['history'].append(['add_point', [x, y]])
                self.reprint_plot_1()
                self.changes_made()

    def onFilterClicked2(self, obj, point, event):
        if not self.moving_point[1] and not self.moving_vibrato[1] and not self.moving_filter[1]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.filterMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.moveFilter:
                self.changes_made()
                self.moving_filter[1] = True
                self.moving_filter_index[1] = self.find_closest_filter(self.route2['filters'], x)
            elif action == self.editFilter:
                index = self.find_closest_filter(self.route2['filters'], x)
                data = [0, 0] + [0 for i in range(14)] # time_i, time_f, filter_choice, window_choice, window_n, cutoff, Ap, As, fp, fs, chebN, chebAp, chebAs, chebfp, chebfs, chebrp
                new_data = self.route2['filters'][index] # i_init, i_end, filter, params
                data[0] = new_data[0]
                data[1] = new_data[1]
                data[2] = filter_choices.index(new_data[2])
                if data[2] == 0:
                    data[3] = filter_windows.index(new_data[3][0])
                    data[4] = new_data[3][1]
                    data[5] = new_data[3][2]
                elif data[2] == 3:
                    data[10] = new_data[3][0]
                    data[11] = new_data[3][1]
                    data[12] = new_data[3][2]
                    data[13] = new_data[3][3]
                    data[14] = new_data[3][4]
                    data[15] = new_data[3][5]
                else:
                    data[6] = new_data[3][0]
                    data[7] = new_data[3][1]
                    data[8] = new_data[3][2]
                    data[9] = new_data[3][3]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.edit_item(1, 2, index, [time_i, time_f, filter_choice, params])
                            break
                        except:
                            self.route2['filters'][index] = new_data
                            self.route2['filters'].sort(key=lambda x: x[0])
                    else:
                        break
            elif action == self.deleteFilter:
                index = self.find_closest_filter(self.route2['filters'], x)
                p = self.route2['filters'][index]
                self.route2['filters'].remove(p)
                self.route2['history'].append(['delete_filter', p])
                self.reprint_plot_2()
                self.changes_made()
        else:
            self.moving_point[1] = False
            self.moving_vibrato[1] = False
            self.moving_filter[1] = False
            self.segundo_click[1] = False

    def onVibratoClicked2(self, obj, point, event):
        if not self.moving_point[1] and not self.moving_vibrato[1] and not self.moving_filter[1]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.vibratoMenu.exec_(QtCore.QPoint(x_screen,y_screen))

            if action == self.moveVibrato:
                self.changes_made()
                self.moving_vibrato[1] = True
                self.moving_vibrato_index[1] = self.find_closest_vibrato(self.route2['vibrato'], x)
            elif action == self.editVibrato:
                index = self.find_closest_vibrato(self.route2['vibrato'], x)
                data = self.route2['vibrato'][index]
                data[4] = windows_vibrato.index(data[4])
                dlg = VibratoForm(parent=self, data=data, max_t=self.route2['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.edit_item(1, 1, index, [time_i, duration, amp, freq, window_v])
            elif action == self.deleteVibrato:
                index = self.find_closest_vibrato(self.route2['vibrato'], x)
                p = self.route2['vibrato'][index]
                self.route2['vibrato'].remove(p)
                self.route2['history'].append(['delete_vibrato', p])
                self.reprint_plot_2()
                self.changes_made()
        else:
            self.moving_point[1] = False
            self.moving_vibrato[1] = False
            self.moving_filter[1] = False
            self.segundo_click[1] = False
        
    def onCurveClicked2(self, obj, event):
        if not self.moving_point[1] and not self.moving_vibrato[1] and not self.moving_filter[1]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.graphMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.addPoint:
                self.route2['points'].append([x, y])
                self.route2['points'].sort(key=lambda x: x[0])
                self.route2['history'].append(['add_point', [x, y]])
                self.reprint_plot_2()
                self.changes_made()
            elif action == self.addVibrato:
                data=[x, 0, 0, 0, 0]
                dlg = VibratoForm(parent=self, data=data, max_t=self.route2['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.route2['vibrato'].append([time_i, duration, amp, freq, window_v])
                    self.route2['history'].append(['vibrato', [time_i, duration, amp, freq, window_v]])
                    self.reprint_plot_2()
                    self.changes_made()
            elif action == self.addFilter:
                data=[x, x] + [0 for i in range(14)]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.route2['filters'].append([time_i, time_f, filter_choice, params])
                            self.route2['history'].append(['filter', [time_i, time_f, filter_choice, params]])
                            self.reprint_plot_2()
                            self.changes_made()
                            break
                        except:
                            self.route2['filters'].remove([time_i, time_f, filter_choice, params])
                            self.route2['history'].remove(['filter', [time_i, time_f, filter_choice, params]])
                    else:
                        break
                    
            elif action == self.openTable:
                data = [1, 0, self.route, self.route2, self.route3, self.route4, self.route5]
                dlg = FuncTableForm(parent=self, data=data)
                dlg.setWindowTitle("Function as table")
                if dlg.exec():
                    pass
        else:
            self.moving_point[1] = False
            self.moving_vibrato[1] = False
            self.moving_filter[1] = False
            self.segundo_click[1] = False

    def onPointsClicked2(self, obj, point, event):
        if not self.moving_point[1] and not self.moving_vibrato[1] and not self.moving_filter[1]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.pointMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.movePoint:
                self.changes_made()
                self.moving_point[1] = True
                self.moving_point_index[1] = self.find_closest_point(self.route2['points'], x, y)
            elif action == self.editPoint:
                index = self.find_closest_point(self.route2['points'], x, y)
                data = self.route2['points'][index]
                dlg = PointForm(parent=self, data=data, max_t=self.route2['total_t'], min_v=20, max_v=70)
                dlg.setWindowTitle("Add Point")
                if dlg.exec():
                    self.edit_item(1, 0, index, data)
            elif action == self.deletePoint:
                p = self.route2['points'][self.find_closest_point(self.route2['points'], x, y)]
                self.route2['points'].remove(p)
                self.route2['history'].append(['delete_point', p])
                try:
                    self.reprint_plot_2()
                    self.changes_made()
                except:
                    pass
        else:
            self.moving_point[1] = False
            self.moving_vibrato[1] = False
            self.moving_filter[1] = False
            self.segundo_click[1] = False

    def mouse_moved2(self, event):
        if self.moving_point[1]:
            self.segundo_click[1] = True
            vb = self.graphicsView_2.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = max(20,min(70,round(mouse_point.y(), 2)))
            min_x, max_x = self.find_moving_point_limits(self.route2['points'], self.moving_point_index[1], self.route2['total_t'])
            if x > min_x and x < max_x:
                self.route2['points'][self.moving_point_index[1]] = [x, y]
                self.reprint_plot_2()
        if self.moving_vibrato[1]:
            self.segundo_click[1] = True
            vb = self.graphicsView_2.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = max(20,min(70,round(mouse_point.y(), 2)))
            min_x, max_x = self.find_moving_vibrato_limits(self.route2['vibrato'], self.moving_vibrato_index[1], self.route2['total_t'])
            if x >= min_x and x <= max_x:
                self.route2['vibrato'][self.moving_vibrato_index[1]][0] = x
                self.reprint_plot_2()
        if self.moving_filter[1]:
            self.segundo_click[1] = True
            vb = self.graphicsView_2.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_filter_limits(self.route2['filters'], self.moving_filter_index[1], self.route2['total_t'])
            if x >= min_x and x <= max_x:
                diff = self.route2['filters'][self.moving_filter_index[1]][1] - self.route2['filters'][self.moving_filter_index[1]][0]
                self.route2['filters'][self.moving_filter_index[1]][0] = x
                self.route2['filters'][self.moving_filter_index[1]][1] = x + diff
                self.reprint_plot_2()

    def mouse_clicked2(self, event):
        if (self.moving_point[1] or self.moving_vibrato[1] or self.moving_filter[1]) and self.segundo_click[1]:
            self.moving_point[1] = False
            self.moving_vibrato[1] = False
            self.moving_filter[1] = False
            self.segundo_click[1] = False
        else:
            if event.double():
                vb = self.graphicsView_2.plotItem.vb
                mouse_point = vb.mapSceneToView(event.scenePos())
                x = round(mouse_point.x(), 2)
                y = round(mouse_point.y(), 2)
                self.route2['points'].append([x, y])
                self.route2['points'].sort(key=lambda x: x[0])
                self.route2['history'].append(['add_point', [x, y]])
                self.reprint_plot_2()
                self.changes_made()

    def onFilterClicked3(self, obj, point, event):
        if not self.moving_point[2] and not self.moving_vibrato[2] and not self.moving_filter[2]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.filterMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.moveFilter:
                self.changes_made()
                self.moving_filter[2] = True
                self.moving_filter_index[2] = self.find_closest_filter(self.route3['filters'], x)
            elif action == self.editFilter:
                index = self.find_closest_filter(self.route3['filters'], x)
                data = [0, 0] + [0 for i in range(14)] # time_i, time_f, filter_choice, window_choice, window_n, cutoff, Ap, As, fp, fs, chebN, chebAp, chebAs, chebfp, chebfs, chebrp
                new_data = self.route3['filters'][index] # i_init, i_end, filter, params
                data[0] = new_data[0]
                data[1] = new_data[1]
                data[2] = filter_choices.index(new_data[2])
                if data[2] == 0:
                    data[3] = filter_windows.index(new_data[3][0])
                    data[4] = new_data[3][1]
                    data[5] = new_data[3][2]
                elif data[2] == 3:
                    data[10] = new_data[3][0]
                    data[11] = new_data[3][1]
                    data[12] = new_data[3][2]
                    data[13] = new_data[3][3]
                    data[14] = new_data[3][4]
                    data[15] = new_data[3][5]
                else:
                    data[6] = new_data[3][0]
                    data[7] = new_data[3][1]
                    data[8] = new_data[3][2]
                    data[9] = new_data[3][3]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.edit_item(2, 2, index, [time_i, time_f, filter_choice, params])
                            break
                        except:
                            self.route3['filters'][index] = new_data
                            self.route3['filters'].sort(key=lambda x: x[0])
                    else:
                        break
            elif action == self.deleteFilter:
                index = self.find_closest_filter(self.route3['filters'], x)
                p = self.route3['filters'][index]
                self.route3['filters'].remove(p)
                self.route3['history'].append(['delete_filter', p])
                self.changes_made()
                self.reprint_plot_3()
        else:
            self.moving_point[2] = False
            self.moving_vibrato[2] = False
            self.moving_filter[2] = False
            self.segundo_click[2] = False

    def onVibratoClicked3(self, obj, point, event):
        if not self.moving_point[2] and not self.moving_vibrato[2] and not self.moving_filter[2]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.vibratoMenu.exec_(QtCore.QPoint(x_screen,y_screen))

            if action == self.moveVibrato:
                self.changes_made()
                self.moving_vibrato[2] = True
                self.moving_vibrato_index[2] = self.find_closest_vibrato(self.route3['vibrato'], x)
            elif action == self.editVibrato:
                index = self.find_closest_vibrato(self.route3['vibrato'], x)
                data = self.route3['vibrato'][index]
                data[4] = windows_vibrato.index(data[4])
                dlg = VibratoForm(parent=self, data=data, max_t=self.route3['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.edit_item(2, 1, index, [time_i, duration, amp, freq, window_v])
            elif action == self.deleteVibrato:
                index = self.find_closest_vibrato(self.route3['vibrato'], x)
                p = self.route3['vibrato'][index]
                self.route3['vibrato'].remove(p)
                self.route3['history'].append(['delete_vibrato', p])
                self.changes_made()
                self.reprint_plot_3()
        else:
            self.moving_point[2] = False
            self.moving_vibrato[2] = False
            self.moving_filter[2] = False
            self.segundo_click[2] = False
        
    def onCurveClicked3(self, obj, event):
        if not self.moving_point[2] and not self.moving_vibrato[2] and not self.moving_filter[2]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.graphMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.addPoint:
                self.route3['points'].append([x, y])
                self.route3['points'].sort(key=lambda x: x[0])
                self.route3['history'].append(['add_point', [x, y]])
                self.reprint_plot_3()
                self.changes_made()
            elif action == self.addVibrato:
                data=[x, 0, 0, 0, 0]
                dlg = VibratoForm(parent=self, data=data, max_t=self.route3['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.route3['vibrato'].append([time_i, duration, amp, freq, window_v])
                    self.route3['history'].append(['vibrato', [time_i, duration, amp, freq, window_v]])
                    self.changes_made()
                    self.reprint_plot_3()
            elif action == self.addFilter:
                data=[x, x] + [0 for i in range(14)]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.route3['filters'].append([time_i, time_f, filter_choice, params])
                            self.route3['history'].append(['filter', [time_i, time_f, filter_choice, params]])
                            self.reprint_plot_3()
                            self.changes_made()
                            break
                        except:
                            self.route3['filters'].remove([time_i, time_f, filter_choice, params])
                            self.route3['history'].remove(['filter', [time_i, time_f, filter_choice, params]])
                    else:
                        break
                    
            elif action == self.openTable:
                data = [2, 0, self.route, self.route2, self.route3, self.route4, self.route5]
                dlg = FuncTableForm(parent=self, data=data)
                dlg.setWindowTitle("Function as table")
                if dlg.exec():
                    pass
        else:
            self.moving_point[2] = False
            self.moving_vibrato[2] = False
            self.moving_filter[2] = False
            self.segundo_click[2] = False

    def onPointsClicked3(self, obj, point, event):
        if not self.moving_point[2] and not self.moving_vibrato[2] and not self.moving_filter[2]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.pointMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.movePoint:
                self.changes_made()
                self.moving_point[2] = True
                self.moving_point_index[2] = self.find_closest_point(self.route3['points'], x, y)
            elif action == self.editPoint:
                index = self.find_closest_point(self.route3['points'], x, y)
                data = self.route3['points'][index]
                dlg = PointForm(parent=self, data=data, max_t=self.route3['total_t'], min_v=-99, max_v=99)
                dlg.setWindowTitle("Add Point")
                if dlg.exec():
                    self.edit_item(2, 0, index, data)
            elif action == self.deletePoint:
                p = self.route3['points'][self.find_closest_point(self.route3['points'], x, y)]
                self.route3['points'].remove(p)
                self.route3['history'].append(['delete_point', p])
                self.changes_made()
                try:
                    self.reprint_plot_3()
                except:
                    pass
        else:
            self.moving_point[2] = False
            self.moving_vibrato[2] = False
            self.moving_filter[2] = False
            self.segundo_click[2] = False

    def mouse_moved3(self, event):
        if self.moving_point[2]:
            self.segundo_click[2] = True
            vb = self.graphicsView_3.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_point_limits(self.route3['points'], self.moving_point_index[2], self.route3['total_t'])
            if x > min_x and x < max_x:
                self.route3['points'][self.moving_point_index[2]] = [x, y]
                self.reprint_plot_3()
        if self.moving_vibrato[2]:
            self.segundo_click[2] = True
            vb = self.graphicsView_3.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_vibrato_limits(self.route3['vibrato'], self.moving_vibrato_index[2], self.route3['total_t'])
            if x >= min_x and x <= max_x:
                self.route3['vibrato'][self.moving_vibrato_index[2]][0] = x
                self.reprint_plot_3()
        if self.moving_filter[2]:
            self.segundo_click[2] = True
            vb = self.graphicsView_3.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_filter_limits(self.route3['filters'], self.moving_filter_index[2], self.route3['total_t'])
            if x >= min_x and x <= max_x:
                diff = self.route3['filters'][self.moving_filter_index[2]][1] - self.route3['filters'][self.moving_filter_index[2]][0]
                self.route3['filters'][self.moving_filter_index[2]][0] = x
                self.route3['filters'][self.moving_filter_index[2]][1] = x + diff
                self.reprint_plot_3()

    def mouse_clicked3(self, event):
        if (self.moving_point[2] or self.moving_vibrato[2] or self.moving_filter[2]) and self.segundo_click[2]:
            self.moving_point[2] = False
            self.moving_vibrato[2] = False
            self.moving_filter[2] = False
            self.segundo_click[2] = False
        else:
            if event.double():
                vb = self.graphicsView_3.plotItem.vb
                mouse_point = vb.mapSceneToView(event.scenePos())
                x = round(mouse_point.x(), 2)
                y = round(mouse_point.y(), 2)
                self.route3['points'].append([x, y])
                self.route3['points'].sort(key=lambda x: x[0])
                self.route3['history'].append(['add_point', [x, y]])
                self.reprint_plot_3()
                self.changes_made()

    def onFilterClicked4(self, obj, point, event):
        if not self.moving_point[3] and not self.moving_vibrato[3] and not self.moving_filter[3]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.filterMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.moveFilter:
                self.changes_made()
                self.moving_filter[3] = True
                self.moving_filter_index[3] = self.find_closest_filter(self.route4['filters'], x)
            elif action == self.editFilter:
                index = self.find_closest_filter(self.route4['filters'], x)
                data = [0, 0] + [0 for i in range(14)] # time_i, time_f, filter_choice, window_choice, window_n, cutoff, Ap, As, fp, fs, chebN, chebAp, chebAs, chebfp, chebfs, chebrp
                new_data = self.route4['filters'][index] # i_init, i_end, filter, params
                data[0] = new_data[0]
                data[1] = new_data[1]
                data[2] = filter_choices.index(new_data[2])
                if data[2] == 0:
                    data[3] = filter_windows.index(new_data[3][0])
                    data[4] = new_data[3][1]
                    data[5] = new_data[3][2]
                elif data[2] == 3:
                    data[10] = new_data[3][0]
                    data[11] = new_data[3][1]
                    data[12] = new_data[3][2]
                    data[13] = new_data[3][3]
                    data[14] = new_data[3][4]
                    data[15] = new_data[3][5]
                else:
                    data[6] = new_data[3][0]
                    data[7] = new_data[3][1]
                    data[8] = new_data[3][2]
                    data[9] = new_data[3][3]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.edit_item(3, 2, index, [time_i, time_f, filter_choice, params])
                            break
                        except:
                            self.route4['filters'][index] = new_data
                            self.route4['filters'].sort(key=lambda x: x[0])
                    else:
                        break
            elif action == self.deleteFilter:
                index = self.find_closest_filter(self.route4['filters'], x)
                p = self.route4['filters'][index]
                self.route4['filters'].remove(p)
                self.route4['history'].append(['delete_filter', p])
                self.changes_made()
                self.reprint_plot_4()
        else:
            self.moving_point[3] = False
            self.moving_vibrato[3] = False
            self.moving_filter[3] = False
            self.segundo_click[3] = False

    def onVibratoClicked4(self, obj, point, event):
        if not self.moving_point[3] and not self.moving_vibrato[3] and not self.moving_filter[3]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.vibratoMenu.exec_(QtCore.QPoint(x_screen,y_screen))

            if action == self.moveVibrato:
                self.changes_made()
                self.moving_vibrato[3] = True
                self.moving_vibrato_index[3] = self.find_closest_vibrato(self.route4['vibrato'], x)
            elif action == self.editVibrato:
                index = self.find_closest_vibrato(self.route4['vibrato'], x)
                data = self.route4['vibrato'][index]
                data[4] = windows_vibrato.index(data[4])
                dlg = VibratoForm(parent=self, data=data, max_t=self.route4['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.edit_item(3, 1, index, [time_i, duration, amp, freq, window_v])
            elif action == self.deleteVibrato:
                index = self.find_closest_vibrato(self.route4['vibrato'], x)
                p = self.route4['vibrato'][index]
                self.route4['vibrato'].remove(p)
                self.route4['history'].append(['delete_vibrato', p])
                self.changes_made()
                self.reprint_plot_4()
        else:
            self.moving_point[3] = False
            self.moving_vibrato[3] = False
            self.moving_filter[3] = False
            self.segundo_click[3] = False
        
    def onCurveClicked4(self, obj, event):
        if not self.moving_point[3] and not self.moving_vibrato[3] and not self.moving_filter[3]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.graphMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.addPoint:
                self.route4['points'].append([x, y])
                self.route4['points'].sort(key=lambda x: x[0])
                self.route4['history'].append(['add_point', [x, y]])
                self.reprint_plot_4()
                self.changes_made()
            elif action == self.addVibrato:
                data=[x, 0, 0, 0, 0]
                dlg = VibratoForm(parent=self, data=data, max_t=self.route4['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.route4['vibrato'].append([time_i, duration, amp, freq, window_v])
                    self.route4['history'].append(['vibrato', [time_i, duration, amp, freq, window_v]])
                    self.changes_made()
                    self.reprint_plot_4()
            elif action == self.addFilter:
                data=[x, x] + [0 for i in range(14)]
                while True:
                    dlg = FilterForm(parent=self, data=data)
                    dlg.setWindowTitle("Add Filter")
                    if dlg.exec():
                        time_i = data[0]
                        time_f = data[1]
                        choice = data[2]
                        if choice == 0:
                            params = [filter_windows[data[3]], data[4], data[5]]
                        elif choice == 3:
                            params = [data[10], data[11], data[12], data[13], data[14], data[15]]
                        else:
                            params = [data[6], data[7], data[8], data[9]]
                        filter_choice = filter_choices[choice]
                        try:
                            self.route4['filters'].append([time_i, time_f, filter_choice, params])
                            self.route4['history'].append(['filter', [time_i, time_f, filter_choice, params]])
                            self.reprint_plot_4()
                            self.changes_made()
                            break
                        except:
                            self.route4['filters'].remove([time_i, time_f, filter_choice, params])
                            self.route4['history'].remove(['filter', [time_i, time_f, filter_choice, params]])
                    else:
                        break
                    
            elif action == self.openTable:
                data = [3, 0, self.route, self.route2, self.route3, self.route4, self.route5]
                dlg = FuncTableForm(parent=self, data=data)
                dlg.setWindowTitle("Function as table")
                if dlg.exec():
                    pass
        else:
            self.moving_point[3] = False
            self.moving_vibrato[3] = False
            self.moving_filter[3] = False
            self.segundo_click[3] = False

    def onPointsClicked4(self, obj, point, event):
        if not self.moving_point[3] and not self.moving_vibrato[3] and not self.moving_filter[3]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.pointMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.movePoint:
                self.changes_made()
                self.moving_point[3] = True
                self.moving_point_index[3] = self.find_closest_point(self.route4['points'], x, y)
            elif action == self.editPoint:
                index = self.find_closest_point(self.route4['points'], x, y)
                data = self.route4['points'][index]
                dlg = PointForm(parent=self, data=data, max_t=self.route4['total_t'], min_v=0, max_v=50)
                dlg.setWindowTitle("Add Point")
                if dlg.exec():
                    self.edit_item(3, 0, index, data)
            elif action == self.deletePoint:
                p = self.route4['points'][self.find_closest_point(self.route4['points'], x, y)]
                self.route4['points'].remove(p)
                self.route4['history'].append(['delete_point', p])
                self.changes_made()
                try:
                    self.reprint_plot_4()
                except:
                    pass
        else:
            self.moving_point[3] = False
            self.moving_vibrato[3] = False
            self.moving_filter[3] = False
            self.segundo_click[3] = False

    def mouse_moved4(self, event):
        if self.moving_point[3]:
            self.segundo_click[3] = True
            vb = self.graphicsView_4.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = min(50,max(0, round(mouse_point.y(), 2)))
            min_x, max_x = self.find_moving_point_limits(self.route4['points'], self.moving_point_index[3], self.route4['total_t'])
            if x > min_x and x < max_x:
                self.route4['points'][self.moving_point_index[3]] = [x, y]
                self.reprint_plot_4()
        if self.moving_vibrato[3]:
            self.segundo_click[3] = True
            vb = self.graphicsView_4.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_vibrato_limits(self.route4['vibrato'], self.moving_vibrato_index[3], self.route4['total_t'])
            if x >= min_x and x <= max_x:
                self.route4['vibrato'][self.moving_vibrato_index[3]][0] = x
                self.reprint_plot_4()
        if self.moving_filter[3]:
            self.segundo_click[3] = True
            vb = self.graphicsView_4.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_filter_limits(self.route4['filters'], self.moving_filter_index[3], self.route4['total_t'])
            if x >= min_x and x <= max_x:
                diff = self.route4['filters'][self.moving_filter_index[3]][1] - self.route4['filters'][self.moving_filter_index[3]][0]
                self.route4['filters'][self.moving_filter_index[3]][0] = x
                self.route4['filters'][self.moving_filter_index[3]][1] = x + diff
                self.reprint_plot_4()

    def mouse_clicked4(self, event):
        if (self.moving_point[3] or self.moving_vibrato[3] or self.moving_filter[3]) and self.segundo_click[3]:
            self.moving_point[3] = False
            self.moving_vibrato[3] = False
            self.moving_filter[3] = False
            self.segundo_click[3] = False
        else:
            if event.double():
                vb = self.graphicsView_4.plotItem.vb
                mouse_point = vb.mapSceneToView(event.scenePos())
                x = round(mouse_point.x(), 2)
                y = min(50,max(0, round(mouse_point.y(), 2)))
                self.route4['points'].append([x, y])
                self.route4['points'].sort(key=lambda x: x[0])
                self.route4['history'].append(['add_point', [x, y]])
                self.reprint_plot_4()
                self.changes_made()
    
    def onCurveClicked5(self, obj, event):
        if not self.moving_point[4] and not self.moving_vibrato[4]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.noteMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.addNote:
                data = [x, int(round(2*y,0))]
                dlg = NoteForm(parent=self, data=data, max_t=self.route5['total_t'])
                dlg.setWindowTitle("Add Note")
                if dlg.exec():
                    new_x = data[0]
                    new_y = dict_notes[data[1]/2]
                    self.route5['notes'].append([new_x, new_y])
                    self.route5['notes'].sort(key=lambda x: x[0])
                    self.route5['history'].append(['add_notes', [new_x, new_y]])
                    self.changes_made()
                    self.reprint_plot_5()
            elif action == self.addTrill:
                data = [x, 0, 0, 0]
                dlg = TrillForm(parent=self, data=data, max_t=self.route5['total_t'])
                dlg.setWindowTitle("Add Note")
                if dlg.exec():
                    time = data[0]
                    dist = data[1]/2
                    freq = data[2]
                    duration = data[3]
                    self.route5['trill'].append([time, dist, freq, duration])
                    self.route5['trill'].sort(key=lambda x: x[0])
                    self.route5['history'].append(['add_trill', [time, dist, freq, duration]])
                    self.changes_made()
                    self.reprint_plot_5()
            elif action == self.openNotesTable:
                data = [4, 0, self.route, self.route2, self.route3, self.route4, self.route5]
                dlg = FuncTableForm(parent=self, data=data)
                dlg.setWindowTitle("Function as table")
                if dlg.exec():
                    pass
        else:
            self.moving_point[4] = False
            self.segundo_click[4] = False
            self.moving_vibrato[4] = False

    def onPointsClicked5(self, obj, point, event):
        if not self.moving_point[4] and not self.moving_vibrato[4]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.pointMenu.exec_(QtCore.QPoint(x_screen,y_screen))
            if action == self.movePoint:
                self.changes_made()
                self.moving_point[4] = True
                self.moving_point_index[4] = self.find_closest_note(self.route5['notes'], x, y)
            elif action == self.editPoint:
                index = self.find_closest_note(self.route5['notes'], x, y)
                data = self.route5['notes'][index]
                data[1] = int(round(dict_notes_rev[data[1]]*2, 0))
                dlg = NoteForm(parent=self, data=data, max_t=self.route5['total_t'])
                dlg.setWindowTitle("Edit Note")
                if dlg.exec():
                    data[1] = dict_notes[data[1]/2]
                    self.edit_item(4, 0, index, data)
            elif action == self.deletePoint:
                p = self.route5['notes'][self.find_closest_note(self.route5['notes'], x, y)]
                self.route5['notes'].remove(p)
                self.route5['history'].append(['delete_notes', p])
                self.changes_made()
                try:
                    self.reprint_plot_5()
                except:
                    pass
        else:
            self.moving_point[4] = False
            self.segundo_click[4] = False
            self.moving_vibrato[4] = False

    def onVibratoClicked5(self, obj, point, event):
        if not self.moving_point[4] and not self.moving_vibrato[4]:
            x = event.pos()[0]
            y = event.pos()[1]
            x_screen = int(event.screenPos()[0])
            y_screen = int(event.screenPos()[1])
            action = self.vibratoMenu.exec_(QtCore.QPoint(x_screen,y_screen))

            if action == self.moveVibrato:
                self.changes_made()
                self.moving_vibrato[4] = True
                self.moving_vibrato_index[4] = self.find_closest_trill(self.route5['trill'], x)
            elif action == self.editVibrato:
                index = self.find_closest_trill(self.route5['trill'], x)
                data = self.route5['trill'][index]
                #data[4] = windows_vibrato.index(data[4])
                data[1] *= 2
                dlg = TrillForm(parent=self, data=data, max_t=self.route4['total_t'])
                dlg.setWindowTitle("Edit Trill")
                if dlg.exec():
                    time = data[0]
                    dist = data[1]/2
                    freq = data[2]
                    duration = data[3]
                    self.edit_item(4, 1, index, [time, dist, freq, duration])
            elif action == self.deleteVibrato:
                index = self.find_closest_trill(self.route5['trill'], x)
                p = self.route5['trill'][index]
                self.route5['trill'].remove(p)
                self.route5['history'].append(['delete_trill', p])
                self.changes_made()
                self.reprint_plot_5()
        else:
            self.moving_point[3] = False
            self.moving_vibrato[4] = False

    def mouse_moved5(self, event):
        if self.moving_point[4]:
            self.segundo_click[4] = True
            vb = self.graphicsView_5.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_note_limits(self.route5['notes'], self.moving_point_index[4], self.route5['total_t'])
            if x > min_x and x < max_x:
                if y >= 0 and y < 15.75:
                    note = dict_notes[round(y * 2) / 2]
                    self.route5['notes'][self.moving_point_index[4]] = [x, note]
                    self.reprint_plot_5()
                elif y >= 15.75:
                    note = dict_notes[17]
                    self.route5['notes'][self.moving_point_index[4]] = [x, note]
                    self.reprint_plot_5()
        if self.moving_vibrato[4]:
            self.segundo_click[4] = True
            vb = self.graphicsView_5.plotItem.vb
            mouse_point = vb.mapSceneToView(event)
            x = round(mouse_point.x(), 2)
            y = round(mouse_point.y(), 2)
            min_x, max_x = self.find_moving_trill_limits(self.route5['trill'], self.moving_vibrato_index[4], self.route5['total_t'])
            if x >= min_x and x <= max_x:
                self.route5['trill'][self.moving_vibrato_index[4]][0] = x
                self.reprint_plot_5()

    def mouse_clicked5(self, event):
        if (self.moving_point[4] or self.moving_vibrato[4]) and self.segundo_click[4]:
            self.moving_point[4] = False
            self.segundo_click[4] = False
            self.moving_vibrato[4] = False
        else:
            if event.double():
                vb = self.graphicsView_5.plotItem.vb
                mouse_point = vb.mapSceneToView(event.scenePos())
                x = round(mouse_point.x(), 2)
                y = round(mouse_point.y(), 2)
                if y < 0:
                    note = dict_notes[0]
                elif y >= 0 and y < 15.75:
                    note = dict_notes[round(y * 2) / 2]
                elif y >= 15.75:
                    note = dict_notes[17]
                self.route5['notes'].append([x, note])
                self.route5['notes'].sort(key=lambda x: x[0])
                self.route5['history'].append(['add_note', [x, note]])
                self.reprint_plot_5()
                self.changes_made()

    def find_moving_note_limits(self, notes, index, total_t):
        lim_inf = 0
        lim_sup = total_t
        if index > 0:
            lim_inf = notes[index - 1][0]
        if index < len(notes) - 1:
            lim_sup = notes[index + 1][0]
        return lim_inf, lim_sup
    
    def find_moving_filter_limits(self, filters, index, total_t):
        return 0, total_t - filters[index][1]
    
    def find_moving_vibrato_limits(self, vibratos, index, total_t):
        return 0, total_t - vibratos[index][1]
    
    def find_moving_trill_limits(self, trills, index, total_t):
        return 0, total_t - trills[index][3]
    
    def find_moving_point_limits(self, points, index, total_t):
        lim_inf = 0
        lim_sup = total_t
        if index > 0:
            lim_inf = points[index - 1][0]
        if index < len(points) - 1:
            lim_sup = points[index + 1][0]
        return lim_inf, lim_sup
    
    def find_closest_note(self, notes, x, y):
        if len(notes) == 0:
            return -1
        else:
            closest = 0
            dist = abs(notes[0][0] - x) + abs(dict_notes_rev[notes[0][1]] - y)
            for i in range(len(notes)):
                new_dist = abs(notes[i][0] - x) + abs(dict_notes_rev[notes[0][1]] - y)
                if new_dist < dist:
                    closest = i
                    dist = new_dist
            return closest

    def find_closest_point(self, points, x, y):
        if len(points) == 0:
            return -1
        else:
            closest = 0
            dist = abs(points[0][0] - x) + abs(points[0][1] - y)
            for i in range(len(points)):
                new_dist = abs(points[i][0] - x) + abs(points[i][1] - y)
                if new_dist < dist:
                    closest = i
                    dist = new_dist
            return closest
    
    def find_closest_filter(self, filters, x):
        if len(filters) == 0:
            return -1
        else:
            closest = 0
            dist = abs(filters[0][0] - x)
            for i in range(len(filters)):
                new_dist = abs(filters[i][0] - x)
                if new_dist < dist:
                    closest = i
                    dist = new_dist
            return closest
        
    def find_closest_vibrato(self, vibratos, x):
        if len(vibratos) == 0:
            return -1
        else:
            closest = 0
            dist = abs(vibratos[0][0] - x)
            for i in range(len(vibratos)):
                new_dist = abs(vibratos[i][0] - x)
                if new_dist < dist:
                    closest = i
                    dist = new_dist
            return closest
    
    def find_closest_trill(self, trills, x):
        if len(trills) == 0:
            return -1
        else:
            closest = 0
            dist = abs(trills[0][0] - x)
            for i in range(len(trills)):
                new_dist = abs(trills[i][0] - x)
                if new_dist < dist:
                    closest = i
                    dist = new_dist
            return closest
        
    def edit_item(self, func, prop, index, params):
        self.changes_made()
        if func == 0:
            if prop == 0:
                self.route['points'][index] = params
                self.route['points'].sort(key=lambda x: x[0])
            elif prop == 1:
                self.route['vibrato'][index] = params
                self.route['vibrato'].sort(key=lambda x: x[0])
            elif prop == 2:
                self.route['filters'][index] = params
                self.route['filters'].sort(key=lambda x: x[0])
            self.reprint_plot_1()
        elif func == 1:
            if prop == 0:
                self.route2['points'][index] = params
                self.route2['points'].sort(key=lambda x: x[0])
            elif prop == 1:
                self.route2['vibrato'][index] = params
                self.route2['vibrato'].sort(key=lambda x: x[0])
            elif prop == 2:
                self.route2['filters'][index] = params
                self.route2['filters'].sort(key=lambda x: x[0])
            self.reprint_plot_2()
        elif func == 2:
            if prop == 0:
                self.route3['points'][index] = params
                self.route3['points'].sort(key=lambda x: x[0])
            elif prop == 1:
                self.route3['vibrato'][index] = params
                self.route3['vibrato'].sort(key=lambda x: x[0])
            elif prop == 2:
                self.route3['filters'][index] = params
                self.route3['filters'].sort(key=lambda x: x[0])
            self.reprint_plot_3()
        elif func == 3:
            if prop == 0:
                self.route4['points'][index] = params
                self.route4['points'].sort(key=lambda x: x[0])
            elif prop == 1:
                self.route4['vibrato'][index] = params
                self.route4['vibrato'].sort(key=lambda x: x[0])
            elif prop == 2:
                self.route4['filters'][index] = params
                self.route4['filters'].sort(key=lambda x: x[0])
            self.reprint_plot_4()
        elif func == 4:
            if prop == 0:
                self.route5['notes'][index] = params
                self.route5['notes'].sort(key=lambda x: x[0])
            elif prop == 1:
                self.route5['trill'][index] = params
                self.route5['trill'].sort(key=lambda x: x[0])
            self.reprint_plot_5()

    def delete_item(self, func, prop, index):
        self.changes_made()
        if func == 0:
            if prop == 0:
                p = self.route['points'].pop(index)
                self.route['history'].append(['delete_point', p])
            elif prop == 1:
                p = self.route['vibrato'].pop(index)
                self.route['history'].append(['delete_vibrato', p])
            elif prop == 2:
                p = self.route['filters'].pop(index)
                self.route['history'].append(['delete_filter', p])
            self.reprint_plot_1()
        elif func == 1:
            if prop == 0:
                p = self.route2['points'].pop(index)
                self.route2['history'].append(['delete_point', p])
            elif prop == 1:
                p = self.route2['vibrato'].pop(index)
                self.route2['history'].append(['delete_vibrato', p])
            elif prop == 2:
                p = self.route2['filters'].pop(index)
                self.route2['history'].append(['delete_filter', p])
            self.reprint_plot_2()
        elif func == 2:
            if prop == 0:
                p = self.route3['points'].pop(index)
                self.route3['history'].append(['delete_point', p])
            elif prop == 1:
                p = self.route3['vibrato'].pop(index)
                self.route3['history'].append(['delete_vibrato', p])
            elif prop == 2:
                p = self.route3['filters'].pop(index)
                self.route3['history'].append(['delete_filter', p])
            self.reprint_plot_3()
        elif func == 3:
            if prop == 0:
                p = self.route4['points'].pop(index)
                self.route4['history'].append(['delete_point', p])
            elif prop == 1:
                p = self.route4['vibrato'].pop(index)
                self.route4['history'].append(['delete_vibrato', p])
            elif prop == 2:
                p = self.route4['filters'].pop(index)
                self.route4['history'].append(['delete_filter', p])
            self.reprint_plot_4()
        elif func == 4:
            if prop == 0:
                p = self.route5['notes'].pop(index)
                self.route5['history'].append(['delete_note', p])
            self.reprint_plot_5()

    def add_item(self, func, prop, params, from_func=False):
        if not from_func:
            self.changes_made()
        if func == 0:
            if prop == 0:
                self.route['points'].append(params)
                self.route['points'].sort(key=lambda x: x[0])
                self.route['history'].append(['add_point', params])
            elif prop == 1:
                self.route['vibrato'].append(params)
                self.route['vibrato'].sort(key=lambda x: x[0])
                self.route['history'].append(['vibrato', params])
            elif prop == 2:
                self.route['filters'].append(params)
                self.route['filters'].sort(key=lambda x: x[0])
                self.route['history'].append(['filter', params])
            self.reprint_plot_1()
        elif func == 1:
            if prop == 0:
                self.route2['points'].append(params)
                self.route2['points'].sort(key=lambda x: x[0])
                self.route2['history'].append(['add_point', params])
            elif prop == 1:
                self.route2['vibrato'].append(params)
                self.route2['vibrato'].sort(key=lambda x: x[0])
                self.route2['history'].append(['vibrato', params])
            elif prop == 2:
                self.route2['filters'].append(params)
                self.route2['filters'].sort(key=lambda x: x[0])
                self.route2['history'].append(['filter', params])
            self.reprint_plot_2()
        elif func == 2:
            if prop == 0:
                self.route3['points'].append(params)
                self.route3['points'].sort(key=lambda x: x[0])
                self.route3['history'].append(['add_point', params])
            elif prop == 1:
                self.route3['vibrato'].append(params)
                self.route3['vibrato'].sort(key=lambda x: x[0])
                self.route3['history'].append(['vibrato', params])
            elif prop == 2:
                self.route3['filters'].append(params)
                self.route3['filters'].sort(key=lambda x: x[0])
                self.route3['history'].append(['filter', params])
            self.reprint_plot_3()
        elif func == 3:
            if prop == 0:
                self.route4['points'].append(params)
                self.route4['points'].sort(key=lambda x: x[0])
                self.route4['history'].append(['add_point', params])
            elif prop == 1:
                self.route4['vibrato'].append(params)
                self.route4['vibrato'].sort(key=lambda x: x[0])
                self.route4['history'].append(['vibrato', params])
            elif prop == 2:
                self.route4['filters'].append(params)
                self.route4['filters'].sort(key=lambda x: x[0])
                self.route4['history'].append(['filter', params])
            self.reprint_plot_4()
        elif func == 4:
            if prop == 0:
                self.route5['notes'].append(params)
                self.route5['notes'].sort(key=lambda x: x[0])
                self.route5['history'].append(['add_note', params])
            self.reprint_plot_5()

    def populate_graph(self):
        self.route = {  
                        'total_t': 20,
                        'Fs': 100,
                        'points': [[0, 10]],
                        'filters': [],
                        'vibrato': [],
                        'history': []
                     }
        self.route2 = {  
                        'total_t': 20,
                        'Fs': 100,
                        'points': [[0, 45]],
                        'filters': [],
                        'vibrato': [],
                        'history': []
                     }
        self.route3 = {  
                        'total_t': 20,
                        'Fs': 100,
                        'points': [[0, 0]],
                        'filters': [],
                        'vibrato': [],
                        'history': []
                     }
        self.route4 = {  
                        'total_t': 20,
                        'Fs': 100,
                        'points': [[0, 0]],
                        'filters': [],
                        'vibrato': [],
                        'history': []
                     }
        self.route5 = {  
                        'total_t': 20,
                        'Fs': 100,
                        'notes': [],
                        'trill': [],
                        'history': []
                     }

    def reprint_plot_1(self):
        t, f, p, vib, fil = calculate_route(self.route)
        x = []
        y = []
        for point in p:
            x.append(point[0])
            y.append(point[1])
        vib_x = []
        vib_y = []
        for v in vib:
            vib_x.append(v)
            vib_y.append(f[int(round(v*100, 0))] + 1)
        fil_x = []
        fil_y = []
        for fi in fil:
            fil_x.append(fi)
            fil_y.append(f[int(round(fi*100, 0))] - 1)
        self.func1.setData(t, f)
        self.scatter1.setData(x, y)
        self.vibscatter1.setData(vib_x, vib_y)
        self.filscatter1.setData(fil_x, fil_y)
    
    def reprint_plot_2(self):
        t, f, p, vib, fil = calculate_route(self.route2)
        x = []
        y = []
        for point in p:
            x.append(point[0])
            y.append(point[1])
        vib_x = []
        vib_y = []
        for v in vib:
            vib_x.append(v)
            vib_y.append(f[int(round(v*100, 0))] + 1)
        fil_x = []
        fil_y = []
        for fi in fil:
            fil_x.append(fi)
            fil_y.append(f[int(round(fi*100, 0))] - 1)
        self.func2.setData(t, f)
        self.scatter2.setData(x, y)
        self.vibscatter2.setData(vib_x, vib_y)
        self.filscatter2.setData(fil_x, fil_y)
    
    def reprint_plot_3(self):
        t, f, p, vib, fil = calculate_route(self.route3)
        x = []
        y = []
        for point in p:
            x.append(point[0])
            y.append(point[1])
        vib_x = []
        vib_y = []
        for v in vib:
            vib_x.append(v)
            vib_y.append(f[int(round(v*100, 0))] + 1)
        fil_x = []
        fil_y = []
        for fi in fil:
            fil_x.append(fi)
            fil_y.append(f[int(round(fi*100, 0))] - 1)
        self.func3.setData(t, f)
        self.scatter3.setData(x, y)
        self.vibscatter3.setData(vib_x, vib_y)
        self.filscatter3.setData(fil_x, fil_y)
    
    def reprint_plot_4(self):
        t, f, p, vib, fil = calculate_route(self.route4)
        x = []
        y = []
        for point in p:
            x.append(point[0])
            y.append(point[1])
        vib_x = []
        vib_y = []
        for v in vib:
            vib_x.append(v)
            vib_y.append(f[int(round(v*100, 0))] + 1)
        fil_x = []
        fil_y = []
        for fi in fil:
            fil_x.append(fi)
            fil_y.append(f[int(round(fi*100, 0))] - 1)
        self.func4.setData(t, f)
        self.scatter4.setData(x, y)
        self.vibscatter4.setData(vib_x, vib_y)
        self.filscatter4.setData(fil_x, fil_y)
    
    def reprint_plot_5(self):
        t, f, px, py, tr_x, tr_y = calculate_notes_route(self.route5)
        self.func5.setData(t, f)
        self.scatter5.setData(px, py)
        self.vibscatter5.setData(tr_x, tr_y)

    def checkBox_clicked(self, value):
        if value:
            self.graphicsView.show()
        else:
            self.graphicsView.hide()
    
    def checkBox2_clicked(self, value):
        if value:
            self.graphicsView_2.show()
        else:
            self.graphicsView_2.hide()

    def checkBox3_clicked(self, value):
        if value:
            self.graphicsView_3.show()
        else:
            self.graphicsView_3.hide()

    def checkBox4_clicked(self, value):
        if value:
            self.graphicsView_4.show()
        else:
            self.graphicsView_4.hide()

    def checkBox5_clicked(self, value):
        if value:
            self.graphicsView_5.show()
        else:
            self.graphicsView_5.hide()

    def plot_measure(self, measure, title):
        '''
        Se usa esta función para desplegar una ventana con el gráfico de alguna variable de interés
        '''
        plotwin = LivePlotWindow(self.app, measure, self.data, parent=self)
        plotwin.setWindowTitle(title)
        plotwin.show()

    def measure_radius(self):
        '''
        Para graficar la evolución en el tiempo del radio
        '''
        self.plot_measure(0, "Radius Plot")

    def measure_theta(self):
        '''
        Para graficar la evolución en el tiempo del ángulo de incidencia
        '''
        self.plot_measure(1, "Theta Plot")

    def measure_offset(self):
        '''
        Para graficar la evolución en el tiempo del offset
        '''
        self.plot_measure(2, "Offset Plot")

    def measure_position(self):
        '''
        Para graficar la evolución en el tiempo de la posición (plano XZ)
        '''
        self.plot_measure(3, "Position Plot")

    def measure_mouth_presure(self):
        '''
        Para graficar la evolución en el tiempo de la presión en la boca
        '''
        self.plot_measure(4, "Mouth Preasure Plot")

    def measure_mass_flow_rate(self):
        '''
        Para graficar la evolución en el tiempo del flujo másico
        '''
        self.plot_measure(5, "Mass Flow Rate Plot")

    def measure_volume_flow_rate(self):
        '''
        Para graficar la evolución en el tiempo del flujo volumétrico
        '''
        self.plot_measure(6, "Volume Flow Rate Plot")

    def measure_temperature(self):
        '''
        Para graficar la evolución en el tiempo de la temperatura del flujo
        '''
        self.plot_measure(7, "Flow Temperature Plot")

    def measure_sound_frequency(self):
        '''
        Para graficar la evolución en el tiempo de la frecuencia del sonido
        '''
        self.plot_measure(8, "Sound Frequency Plot")

    def measure_x_position(self):
        '''
        Para graficar la evolución en el tiempo de x
        '''
        self.plot_measure(9, "X Position Plot")

    def measure_z_position(self):
        '''
        Para graficar la evolución en el tiempo de z
        '''
        self.plot_measure(10, "Z Position Plot")
    
    def measure_alpha_position(self):
        '''
        Para graficar la evolución en el tiempo de alpha
        '''
        self.plot_measure(11, "Alpha Position Plot")

if __name__ == "__main__":

    app = QApplication(sys.argv)
    pipe2pierre, pierre_pipe = Pipe()
    s = StartUpWindow(app, pipe2pierre)
    s.location_on_the_screen()
    s.show()

    from drivers import Musician
    host = "192.168.2.10"
    connections = ["192.168.2.102", "192.168.2.104", "192.168.2.103", "192.168.2.101", "192.168.2.100", "COM3"]
    event = Event()
    event.set()

    mgr = Manager()
    data = mgr.dict()
    
    t0 = time()
    connect = True
    pierre = Musician(host, connections, event, pierre_pipe, data, fingers_connect=False, x_connect=True, z_connect=True, alpha_connect=connect, flow_connect=connect, pressure_sensor_connect=connect, mic_connect=True)
    pierre.start()

    # x_driver_started z_driver_started alpha_driver_started memory_started microphone_started flow_driver_started pressure_sensor_started finger_driver_started

    s.wait_loading()
    win = Window(app, event, pipe2pierre, data, connected=True)
    win.show()

    sys.exit(app.exec())