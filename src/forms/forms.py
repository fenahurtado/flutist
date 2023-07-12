from PyQt5.QtWidgets import QDialog, QLabel, QCheckBox, QHBoxLayout, QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout
from PyQt5.QtCore import QEventLoop, Qt
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap

from src.forms.point import Ui_Dialog as PointFormDialog
from src.forms.vibrato import Ui_Dialog as VibratoFormDialog
from src.forms.filter import Ui_Dialog as FilterFormDialog
from src.forms.func_table import Ui_Dialog as FuncTableDialog
from src.forms.notes import Ui_Dialog as NotesFormDialog
from src.forms.duration import Ui_Dialog as DurationFormDialog
from src.forms.correction import Ui_Dialog as CorrectionFormDialog
from src.forms.scale_time import Ui_Dialog as ScaleTimeFormDialog
from src.forms.settings import Ui_Dialog as SettingsFormDialog
from src.forms.trill import Ui_Dialog as TrillFormDialog
from src.route import dict_notes, dict_notes_rev
from functools import partial
from src.cinematica import *
from src.route import dict_notes
from sounddevice import query_hostapis, query_devices

class SettingsForm(QDialog, SettingsFormDialog):
    def __init__(self, parent=None, data=[0 for i in range(34)]):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data
        self.setAllValues()
        self.connectAllSignals()

    def get_available_mics(self):
        devices = query_devices()
        hostapis = query_hostapis()
        l = []
        for d in devices:
            i = d['index']
            n = d['name']
            h = hostapis[d['hostapi']]['name']
            inp = d['max_input_channels']
            out = d['max_output_channels']
            l.append(f'{i} {n}, {h} ({inp} in, {out} out)')
        return l

    def setAllValues(self):
        global DATA
        self.xFlutePos.setValue(DATA["flute_position"]["X_F"])
        self.zFlutePos.setValue(DATA["flute_position"]["Z_F"])
        pixmap = QPixmap('src/forms/flute_pos2.png')
        self.image_flute_pos.setPixmap(pixmap)

        self.micDevices.addItems(self.get_available_mics())
        self.micDevices.setCurrentIndex(DATA["frequency_detection"]["device"])
        self.frequencyDetectionMethod.setCurrentIndex(DATA["frequency_detection"]["method"])
        self.YINfmin.setValue(DATA["frequency_detection"]["YIN"]["fmin"])
        self.YINfmax.setValue(DATA["frequency_detection"]["YIN"]["fmax"])
        self.YINframe_length.setValue(DATA["frequency_detection"]["YIN"]["frame_length"])
        self.YINwin_length.setValue(DATA["frequency_detection"]["YIN"]["win_length"])
        self.YINhop_length.setValue(DATA["frequency_detection"]["YIN"]["hop_length"])
        self.YINtrough_threshold.setValue(DATA["frequency_detection"]["YIN"]["trough_threshold"])
        self.YINcenter.setChecked(DATA["frequency_detection"]["YIN"]["center"])
        self.YINpad_mode.setCurrentIndex(DATA["frequency_detection"]["YIN"]["pad_mode"])
        self.pYINfmin.setValue(DATA["frequency_detection"]["pYIN"]["fmin"])
        self.pYINfmax.setValue(DATA["frequency_detection"]["pYIN"]["fmax"])
        self.pYINframe_length.setValue(DATA["frequency_detection"]["pYIN"]["frame_length"])
        self.pYINwin_length.setValue(DATA["frequency_detection"]["pYIN"]["win_length"])
        self.pYINhop_length.setValue(DATA["frequency_detection"]["pYIN"]["hop_length"])
        self.pYINn_thresholds.setValue(DATA["frequency_detection"]["pYIN"]["n_threshold"])
        self.pYINbeta_parameter_a.setValue(DATA["frequency_detection"]["pYIN"]["beta_parameter_a"])
        self.pYINbeta_parameter_b.setValue(DATA["frequency_detection"]["pYIN"]["beta_parameter_b"])
        self.pYINcenter.setChecked(DATA["frequency_detection"]["pYIN"]["center"])
        self.pYINmax_transition_rate.setValue(DATA["frequency_detection"]["pYIN"]["max_transition_rate"])
        self.pYINresolution.setValue(DATA["frequency_detection"]["pYIN"]["resolution"])
        self.pYINboltzmann_parameter.setValue(DATA["frequency_detection"]["pYIN"]["boltzmann_parameter"])
        self.pYINswitch_prob.setValue(DATA["frequency_detection"]["pYIN"]["switch_prob"])
        self.pYINno_trough_prob.setValue(DATA["frequency_detection"]["pYIN"]["no_trough_prob"])
        self.pYINfill_na.setCurrentIndex(DATA["frequency_detection"]["pYIN"]["fill_na"])
        self.pYINfill_na_float.setValue(DATA["frequency_detection"]["pYIN"]["fill_na_float"])
        self.pYINpad_mode.setCurrentIndex(DATA["frequency_detection"]["pYIN"]["pad_mode"])
        if DATA["frequency_detection"]["method"] == 0:
            self.pYINGroupBox.hide()
        else:
            self.YINGroupBox.hide()

        self.flowVarToControl.setCurrentIndex(DATA["flow_control"]["var_to_control"])
        self.flowControlLoop.setCurrentIndex(DATA["flow_control"]["control_loop"])
        self.flowKp.setValue(DATA["flow_control"]["kp"])
        self.flowKi.setValue(DATA["flow_control"]["ki"])
        self.flowKd.setValue(DATA["flow_control"]["kd"])

        self.X_kp_value.setValue(DATA["x_control"]["kp"])
        self.X_ki_value.setValue(DATA["x_control"]["ki"])
        self.X_kd_value.setValue(DATA["x_control"]["kd"])
        self.X_acc_value.setValue(DATA["x_control"]["acceleration"])
        self.X_dec_value.setValue(DATA["x_control"]["deceleration"])
        self.X_prop_value.setValue(DATA["x_control"]["proportional_coef"])
        self.X_kp_vel_value.setValue(DATA["x_control"]["kp_vel"])
        self.X_ki_vel_value.setValue(DATA["x_control"]["ki_vel"])
        self.X_kd_vel_value.setValue(DATA["x_control"]["kd_vel"])
        pixmap = QPixmap('src/forms/control_motores.drawio.png')
        self.control_image.setPixmap(pixmap)
        self.control_image2.setPixmap(pixmap)
        self.control_image3.setPixmap(pixmap)

        self.Z_kp_value.setValue(DATA["z_control"]["kp"])
        self.Z_ki_value.setValue(DATA["z_control"]["ki"])
        self.Z_kd_value.setValue(DATA["z_control"]["kd"])
        self.Z_acc_value.setValue(DATA["z_control"]["acceleration"])
        self.Z_dec_value.setValue(DATA["z_control"]["deceleration"])
        self.Z_prop_value.setValue(DATA["z_control"]["proportional_coef"])
        self.Z_kp_vel_value.setValue(DATA["z_control"]["kp_vel"])
        self.Z_ki_vel_value.setValue(DATA["z_control"]["ki_vel"])
        self.Z_kd_vel_value.setValue(DATA["z_control"]["kd_vel"])

        self.A_kp_value.setValue(DATA["alpha_control"]["kp"])
        self.A_ki_value.setValue(DATA["alpha_control"]["ki"])
        self.A_kd_value.setValue(DATA["alpha_control"]["kd"])
        self.A_acc_value.setValue(DATA["alpha_control"]["acceleration"])
        self.A_dec_value.setValue(DATA["alpha_control"]["deceleration"])
        self.A_prop_value.setValue(DATA["alpha_control"]["proportional_coef"])
        self.A_kp_vel_value.setValue(DATA["alpha_control"]["kp_vel"])
        self.A_ki_vel_value.setValue(DATA["alpha_control"]["ki_vel"])
        self.A_kd_vel_value.setValue(DATA["alpha_control"]["kd_vel"])
        
    def connectAllSignals(self):
        self.xFlutePos.valueChanged.connect(partial(self.update_data, ["flute_position", "X_F"]))
        self.zFlutePos.valueChanged.connect(partial(self.update_data, ["flute_position", "Z_F"]))

        self.frequencyDetectionMethod.currentIndexChanged.connect(partial(self.update_data, ["frequency_detection", "method"]))
        self.micDevices.currentIndexChanged.connect(partial(self.update_data, ["frequency_detection", "device"]))
        self.YINfmin.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "fmin"]))
        self.YINfmax.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "fmax"]))
        self.YINframe_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "frame_length"]))
        self.YINwin_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "win_length"]))
        self.YINhop_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "hop_length"]))
        self.YINtrough_threshold.valueChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "trough_threshold"]))
        self.YINcenter.stateChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "center"]))
        self.YINpad_mode.currentIndexChanged.connect(partial(self.update_data, ["frequency_detection", "YIN", "pad_mode"]))
        self.pYINfmin.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "fmin"]))
        self.pYINfmax.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "fmax"]))
        self.pYINframe_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "frame_length"]))
        self.pYINwin_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "win_length"]))
        self.pYINhop_length.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "hop_length"]))
        self.pYINn_thresholds.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "n_threshold"]))
        self.pYINbeta_parameter_a.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "beta_parameter_a"]))
        self.pYINbeta_parameter_b.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "beta_parameter_b"]))
        self.pYINcenter.stateChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "center"]))
        self.pYINmax_transition_rate.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "max_transition_rate"]))
        self.pYINresolution.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "resolution"]))
        self.pYINboltzmann_parameter.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "boltzmann_parameter"]))
        self.pYINswitch_prob.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "switch_prob"]))
        self.pYINno_trough_prob.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "no_trough_prob"]))
        self.pYINfill_na.currentIndexChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "fill_na"]))
        self.pYINfill_na_float.valueChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "fill_na_float"]))
        self.pYINpad_mode.currentIndexChanged.connect(partial(self.update_data, ["frequency_detection", "pYIN", "pad_mode"]))

        self.flowVarToControl.currentIndexChanged.connect(partial(self.update_data, ["flow_control", "var_to_control"]))
        self.flowControlLoop.currentIndexChanged.connect(partial(self.update_data, ["flow_control", "control_loop"]))
        self.flowKp.valueChanged.connect(partial(self.update_data, ["flow_control", "kp"]))
        self.flowKi.valueChanged.connect(partial(self.update_data, ["flow_control", "ki"]))
        self.flowKd.valueChanged.connect(partial(self.update_data, ["flow_control", "kd"]))

        self.X_kp_value.valueChanged.connect(partial(self.update_data, ["x_control", "kp"]))
        self.X_ki_value.valueChanged.connect(partial(self.update_data, ["x_control", "ki"]))
        self.X_kd_value.valueChanged.connect(partial(self.update_data, ["x_control", "kd"]))
        self.X_acc_value.valueChanged.connect(partial(self.update_data, ["x_control", "acceleration"]))
        self.X_dec_value.valueChanged.connect(partial(self.update_data, ["x_control", "deceleration"]))
        self.X_prop_value.valueChanged.connect(partial(self.update_data, ["x_control", "proportional_coef"]))
        self.X_kp_vel_value.valueChanged.connect(partial(self.update_data, ["x_control", "kp_vel"]))
        self.X_ki_vel_value.valueChanged.connect(partial(self.update_data, ["x_control", "ki_vel"]))
        self.X_kd_vel_value.valueChanged.connect(partial(self.update_data, ["x_control", "kd_vel"]))

        self.Z_kp_value.valueChanged.connect(partial(self.update_data, ["z_control", "kp"]))
        self.Z_ki_value.valueChanged.connect(partial(self.update_data, ["z_control", "ki"]))
        self.Z_kd_value.valueChanged.connect(partial(self.update_data, ["z_control", "kd"]))
        self.Z_acc_value.valueChanged.connect(partial(self.update_data, ["z_control", "acceleration"]))
        self.Z_dec_value.valueChanged.connect(partial(self.update_data, ["z_control", "deceleration"]))
        self.Z_prop_value.valueChanged.connect(partial(self.update_data, ["z_control", "proportional_coef"]))
        self.Z_kp_vel_value.valueChanged.connect(partial(self.update_data, ["z_control", "kp_vel"]))
        self.Z_ki_vel_value.valueChanged.connect(partial(self.update_data, ["z_control", "ki_vel"]))
        self.Z_kd_vel_value.valueChanged.connect(partial(self.update_data, ["z_control", "kd_vel"]))

        self.A_kp_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "kp"]))
        self.A_ki_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "ki"]))
        self.A_kd_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "kd"]))
        self.A_acc_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "acceleration"]))
        self.A_dec_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "deceleration"]))
        self.A_prop_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "proportional_coef"]))
        self.A_kp_vel_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "kp_vel"]))
        self.A_ki_vel_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "ki_vel"]))
        self.A_kd_vel_value.valueChanged.connect(partial(self.update_data, ["alpha_control", "kd_vel"]))

        self.buttonBox.clicked.connect(self.button_clicked)
        self.storeSettings.clicked.connect(self.store_settings)

    def update_data(self, index, value):
        global DATA
        if index == ["frequency_detection", "method"]:
            if value:
                self.YINGroupBox.hide()
                self.pYINGroupBox.show()
            else:
                self.pYINGroupBox.hide()
                self.YINGroupBox.show()

        #print(index)
        if len(index) == 1:
            DATA[index[0]] = value
            print(DATA[index[0]])
        elif len(index) == 2:
            DATA[index[0]][index[1]] = value
            print(DATA[index[0]][index[1]])
        elif len(index) == 3:
            DATA[index[0]][index[1]][index[2]] = value
            print(DATA[index[0]][index[1]][index[2]])
    
    def button_clicked(self, button):
        global DATA
        if button.text() == 'Apply':
            self.parent.refresh_settings()
        elif button.text() == 'Restore Defaults':
            DATA = read_variables()
            self.setAllValues()

    def store_settings(self):
        global DATA, DATA_dir
        #dir = os.path.dirname(os.path.realpath(__file__)) + '\settings.json'
        with open(DATA_dir, 'w') as json_file:
            json.dump(DATA, json_file, indent=4, sort_keys=True)

class PointForm(QDialog, PointFormDialog):
    def __init__(self, parent=None, data=[0,0], max_t=100, min_v=0, max_v=100):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.time.setValue(data[0])
        self.time.setMaximum(max_t)
        
        self.value.setMaximum(max_v)
        self.value.setMinimum(min_v)
        self.value.setValue(data[1])

        self.time.valueChanged.connect(partial(self.update_data, 'time'))
        self.value.valueChanged.connect(partial(self.update_data, 'value'))

    def update_data(self, tag, value):
        if tag == 'time':
            self.data[0] = value
        elif tag == 'value':
            self.data[1] = value

class TrillForm(QDialog, TrillFormDialog):
    def __init__(self, parent=None, data=[0,0,0,0], max_t=100):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.time.setValue(data[0])
        self.time.setMaximum(max_t)

        # self.noteComboBox.addItems(list(dict_notes.values()))
        # self.noteComboBox.setCurrentIndex(data[1])
        self.distance.setValue(int(data[1]))
        self.duration.setMaximum(max_t-data[0])
        
        self.frequency.setValue(data[2])
        self.duration.setValue(data[3])
        
        self.time.valueChanged.connect(partial(self.update_data, 'time'))
        self.distance.valueChanged.connect(partial(self.update_data, 'distance'))
        self.frequency.valueChanged.connect(partial(self.update_data, 'frequency'))
        self.duration.valueChanged.connect(partial(self.update_data, 'duration'))

    def update_data(self, tag, value):
        if tag == 'time':
            self.data[0] = value
        elif tag == 'distance':
            self.data[1] = value
        elif tag == 'frequency':
            self.data[2] = value
        elif tag == 'duration':
            self.data[3] = value

class ScaleTimeForm(QDialog, ScaleTimeFormDialog):
    def __init__(self, parent=None, data=[0]):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.scaleFactor.setValue(data[0])
        self.scaleFactor.valueChanged.connect(self.update_data)

    def update_data(self, value):
        self.data[0] = value

class CorrectionForm(QDialog, CorrectionFormDialog):
    def __init__(self, parent=None, data=[0,0,0,0,0,0,0,0,0,0], space=0):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data
        self.space = space

        self.r_dis.setValue(data[0])
        self.theta_dis.setValue(data[1])
        self.offset_dis.setValue(data[2])
        self.flow_dis.setValue(data[3])
        self.notes_dis.setValue(data[4])

        self.leadDelayR.setValue(data[5])
        self.leadDelayTheta.setValue(data[6])
        self.leadDelayOffset.setValue(data[7])
        self.leadDelayFlow.setValue(data[8])
        self.leadDelayNotes.setValue(data[9])

        if self.space == 1:
            self.label.setText("X (mm)")
            self.label_2.setText("Z (mm)")
            self.label_3.setText("Alpha (°)")
            self.label_6.setText("Lead or delay X (s)")
            self.label_7.setText("Lead or delay Z (s)")
            self.label_8.setText("Lead or delay Alpha (s)")

        self.r_dis.valueChanged.connect(partial(self.update_data, 'r'))
        self.theta_dis.valueChanged.connect(partial(self.update_data, 'theta'))
        self.offset_dis.valueChanged.connect(partial(self.update_data, 'offset'))
        self.flow_dis.valueChanged.connect(partial(self.update_data, 'flow'))
        self.notes_dis.valueChanged.connect(partial(self.update_data, 'notes'))

        self.leadDelayR.valueChanged.connect(partial(self.update_data, 'leadDelayR'))
        self.leadDelayTheta.valueChanged.connect(partial(self.update_data, 'leadDelayTheta'))
        self.leadDelayOffset.valueChanged.connect(partial(self.update_data, 'leadDelayOffset'))
        self.leadDelayFlow.valueChanged.connect(partial(self.update_data, 'leadDelayFlow'))
        self.leadDelayNotes.valueChanged.connect(partial(self.update_data, 'leadDelayNotes'))

    def update_data(self, tag, value):
        if tag == 'r':
            self.data[0] = value
        elif tag == 'theta':
            self.data[1] = value
        elif tag == 'offset':
            self.data[2] = value
        elif tag == 'flow':
            self.data[3] = value
        elif tag == 'notes':
            self.data[4] = value
        elif tag == 'leadDelayR':
            self.data[5] = value
        elif tag == 'leadDelayTheta':
            self.data[6] = value
        elif tag == 'leadDelayOffset':
            self.data[7] = value
        elif tag == 'leadDelayFlow':
            self.data[8] = value
        elif tag == 'leadDelayNotes':
            self.data[9] = value

class DurationForm(QDialog, DurationFormDialog):
    def __init__(self, parent=None, data=[0]):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.time.setValue(data[0])
        self.time.valueChanged.connect(self.change_time)

    def change_time(self, value):
        self.data[0] = value

class NoteForm(QDialog, NotesFormDialog):
    def __init__(self, parent=None, data=[0,0], max_t=100):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.time.setValue(data[0])
        self.time.setMaximum(max_t)
        self.note_choice.addItems(list(dict_notes.values()))
        self.note_choice.setCurrentIndex(data[1])

        self.time.valueChanged.connect(partial(self.update_data, 'time'))
        self.note_choice.currentIndexChanged.connect(partial(self.update_data, 'value'))

    def update_data(self, tag, value):
        if tag == 'time':
            self.data[0] = value
        elif tag == 'value':
            self.data[1] = value

windows_vibrato = ['rect', 'triangular', 'blackman', 'hamming', 'hanning', 'kaiser1', 'kaiser2', 'kaiser3', 'kaiser4', 'ramp']
class VibratoForm(QDialog, VibratoFormDialog):
    def __init__(self, parent=None, data=[0,0,0,0,0], max_t=100):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data
        self.max_t = max_t

        self.time_i.setValue(data[0])
        self.duration.setValue(data[1])
        self.duration.setMaximum(max_t - data[0])
        self.amp.setValue(data[2])
        self.freq.setValue(data[3])
        self.window_v.setCurrentIndex(data[4])

        self.time_i.valueChanged.connect(partial(self.update_data, 'time_i'))
        self.duration.valueChanged.connect(partial(self.update_data, 'duration'))
        self.amp.valueChanged.connect(partial(self.update_data, 'amp'))
        self.freq.valueChanged.connect(partial(self.update_data, 'freq'))
        self.window_v.currentIndexChanged.connect(partial(self.update_data, 'window_v'))

    def update_data(self, tag, *args):
        if tag == 'time_i':
            self.data[0] = args[0]
            self.duration.setMaximum(self.max_t - self.data[0])
        elif tag == 'duration':
            self.data[1] = args[0]
        elif tag == 'amp':
            self.data[2] = args[0]
        elif tag == 'freq':
            self.data[3] = args[0]
        elif tag == 'window_v':
            self.data[4] = args[0]

filter_choices = ['firwin', 'remez', 'butter', 'chebyshev', 'elliptic']
filter_windows = ['hamming', 'hann', 'blackman', 'bartlett', 'rect']
class FilterForm(QDialog, FilterFormDialog):
    def __init__(self, parent=None, data=[0 for i in range(16)]):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data

        self.time_i.setValue(data[0])
        self.time_f.setValue(data[1])
        self.filter_choice.setCurrentIndex(data[2])

        self.window_choice.setCurrentIndex(data[3])
        self.window_n.setValue(data[4])
        self.cutoff.setValue(data[5])

        self.Ap.setValue(data[6])
        self.As.setValue(data[7])
        self.fp.setValue(data[8])
        self.fs.setValue(data[9])

        self.chebN.setCurrentIndex(data[10])
        self.chebAp.setValue(data[11])
        self.chebAs.setValue(data[12])
        self.chebfp.setValue(data[13])
        self.chebfs.setValue(data[14])
        self.chebrp.setValue(data[15])

        self.time_i.valueChanged.connect(partial(self.update_data, 'time_i'))
        self.time_f.valueChanged.connect(partial(self.update_data, 'time_f'))
        self.filter_choice.currentIndexChanged.connect(self.update_form)

        self.window_choice.currentIndexChanged.connect(partial(self.update_data, 'window_choice'))
        self.window_n.valueChanged.connect(partial(self.update_data, 'window_n'))
        self.cutoff.valueChanged.connect(partial(self.update_data, 'cutoff'))

        self.Ap.valueChanged.connect(partial(self.update_data, 'Ap'))
        self.As.valueChanged.connect(partial(self.update_data, 'As'))
        self.fp.valueChanged.connect(partial(self.update_data, 'fp'))
        self.fs.valueChanged.connect(partial(self.update_data, 'fs'))

        self.chebN.currentIndexChanged.connect(partial(self.update_data, 'chebN'))
        self.chebAp.valueChanged.connect(partial(self.update_data, 'chebAp'))
        self.chebAs.valueChanged.connect(partial(self.update_data, 'chebAs'))
        self.chebfp.valueChanged.connect(partial(self.update_data, 'chebfp'))
        self.chebfs.valueChanged.connect(partial(self.update_data, 'chebfs'))
        self.chebrp.valueChanged.connect(partial(self.update_data, 'chebrp'))

        if self.data[2] == 0:
            #self.windowGroup.hide()
            self.OtherGroup.hide()
            self.ChebGroup.hide()
        elif self.data[2] == 3:
            self.windowGroup.hide()
            self.OtherGroup.hide()
            #self.ChebGroup.hide()
        else:
            self.windowGroup.hide()
            #self.OtherGroup.hide()
            self.ChebGroup.hide()
        self.resize(400,100)
        self.min_size = self.size()

    def update_form(self, new_index):
        if new_index == 0:
            self.windowGroup.show()
            self.OtherGroup.hide()
            self.ChebGroup.hide()
            self.adjustSize()
            self.resize(self.min_size)
        elif new_index == 3:
            self.windowGroup.hide()
            self.OtherGroup.hide()
            self.ChebGroup.show()
            self.adjustSize()
            self.resize(self.min_size)
        else:
            self.windowGroup.hide()
            self.OtherGroup.show()
            self.ChebGroup.hide()
            self.adjustSize()
            self.resize(self.min_size)
        self.data[2] = new_index

    def update_data(self, tag, *args):
        if tag == 'time_i':
            self.data[0] = args[0]
        elif tag == 'time_f':
            self.data[1] = args[0]
        elif tag == 'window_choice':
            self.data[3] = args[0]
        elif tag == 'window_n':
            self.data[4] = args[0]
        elif tag == 'cutoff':
            self.data[5] = args[0]
        elif tag == 'Ap':
            self.data[6] = args[0]
        elif tag == 'As':
            self.data[7] = args[0]
        elif tag == 'fp':
            self.data[8] = args[0]
        elif tag == 'fs':
            self.data[9] = args[0]
        elif tag == 'chebN':
            self.data[10] = args[0]
        elif tag == 'chebAp':
            self.data[11] = args[0]
        elif tag == 'chebAs':
            self.data[12] = args[0]
        elif tag == 'chebfp':
            self.data[13] = args[0]
        elif tag == 'chebfs':
            self.data[14] = args[0]
        elif tag == 'chebrp':
            self.data[15] = args[0]


class FuncTableForm(QDialog, FuncTableDialog):
    def __init__(self, parent=None, data=[]):
        super().__init__(parent) #super(Form, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.data = data
        self.item_selected = None
        self.last_note_t = 0
        self.last_note = 0

        self.function_choice.setCurrentIndex(data[0])
        if data[0] == 4:
            self.property_choice.clear()
            self.property_choice.addItems(['notes'])
        self.property_choice.setCurrentIndex(data[1])

        self.function_choice.currentIndexChanged.connect(self.function_change)
        self.property_choice.currentIndexChanged.connect(self.property_change)

        self.addButton.clicked.connect(self.add_action)
        self.editButton.clicked.connect(self.edit_action)
        self.deleteButton.clicked.connect(self.delete_action)
        self.poblate()

    def add_action(self):
        if self.data[0] != 4:
            if self.data[1] == 0:
                data = [0, 0]
                if data[0] == 0:
                    min_v, max_v = 0, 100
                elif data[0] == 1:
                    min_v, max_v = 20, 70
                elif data[0] == 2:
                    min_v, max_v = -99, 99
                elif data[0] == 3:
                    min_v, max_v = 0, 50
                dlg = PointForm(parent=self, data=data, max_t=self.data[2]['total_t'], min_v=min_v, max_v=max_v)
                dlg.setWindowTitle("Add Point")
                if dlg.exec():
                    new_x = data[0]
                    new_y = data[1]
                    self.parent.add_item(self.data[0], self.data[1], [new_x, new_y])
                    self.poblate()
            elif self.data[1] == 1:
                data=[0, 0, 0, 0, 0]
                dlg = VibratoForm(parent=self, data=data, max_t=self.data[2]['total_t'])
                dlg.setWindowTitle("Add Vibrato")
                if dlg.exec():
                    time_i = data[0]
                    duration = data[1]
                    amp = data[2]
                    freq = data[3]
                    window_v = windows_vibrato[data[4]]
                    self.parent.add_item(self.data[0], self.data[1], [time_i, duration, amp, freq, window_v])
                    self.poblate()
            elif self.data[1] == 2:
                data=[0, 0] + [0 for i in range(14)]
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
                        if self.parent.check_filter(time_i, time_f, filter_choice, params):
                            self.parent.add_item(self.data[0], self.data[1], [time_i, time_f, filter_choice, params])
                            self.poblate()
                            break
                    else:
                        break
        else:
            data = [self.last_note_t+0.1, self.last_note]
            dlg = NoteForm(parent=self, data=data, max_t=self.data[2]['total_t'])
            dlg.setWindowTitle("Add Note")
            if dlg.exec():
                new_x = data[0]
                new_y = dict_notes[data[1]/2]
                self.last_note_t = data[0]
                self.last_note = data[1]
                self.parent.add_item(4, 0, [new_x, new_y])
                self.poblate()

    def edit_action(self):
        if self.item_selected == None:
            pass
        else:
            if self.data[0] != 4:
                route=self.data[self.data[0] + 2]
                if self.data[1] == 0:
                    data = route['points'][self.item_selected]
                    dlg = PointForm(parent=self, data=data, max_t=self.data[2]['total_t'])
                    dlg.setWindowTitle("Add Point")
                    if dlg.exec():
                        new_x = data[0]
                        new_y = data[1]
                        self.parent.edit_item(self.data[0], self.data[1], self.item_selected, [new_x, new_y])
                        self.poblate()
                elif self.data[1] == 1:
                    data = route['vibrato'][self.item_selected]
                    data[4] = windows_vibrato.index(data[4])
                    dlg = VibratoForm(parent=self, data=data, max_t=self.data[2]['total_t'])
                    dlg.setWindowTitle("Add Vibrato")
                    if dlg.exec():
                        time_i = data[0]
                        duration = data[1]
                        amp = data[2]
                        freq = data[3]
                        window_v = windows_vibrato[data[4]]
                        self.parent.edit_item(self.data[0], self.data[1], self.item_selected, [time_i, duration, amp, freq, window_v])
                        self.poblate()
                elif self.data[1] == 2:
                    data = [0, 0] + [0 for i in range(14)] # time_i, time_f, filter_choice, window_choice, window_n, cutoff, Ap, As, fp, fs, chebN, chebAp, chebAs, chebfp, chebfs, chebrp
                    new_data = route['filters'][self.item_selected] # i_init, i_end, filter, params
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
                            if self.parent.check_filter(time_i, time_f, filter_choice, params):
                                self.parent.edit_item(self.data[0], self.data[1], self.item_selected, [time_i, time_f, filter_choice, params])
                                self.poblate()
                                break
                        else:
                            break
            else:
                data = self.data[6]['notes'][self.item_selected]
                data[1] = int(round(dict_notes_rev[data[1]]*2, 0))
                dlg = NoteForm(parent=self, data=data, max_t=self.data[6]['total_t'])
                dlg.setWindowTitle("Edit Note")
                if dlg.exec():
                    data[1] = dict_notes[data[1]/2]
                    self.parent.edit_item(4, 0, self.item_selected, data)
                    self.poblate()

    def delete_action(self):
        if self.item_selected == None:
            pass
        else:
            self.parent.delete_item(self.data[0], self.data[1], self.item_selected)
            self.listWidget.takeItem(self.item_selected)
        self.item_selected = None

    def function_change(self, new_val):
        self.item_selected = None
        self.data[0] = new_val
        if new_val == 4:
            self.data[1] = 0
            self.property_choice.clear()
            self.property_choice.addItems(['notes'])
        else:
            self.property_choice.clear()
            self.property_choice.addItems(['points', 'vibratos', 'filters'])
        self.poblate()

    def property_change(self, new_val):
        self.item_selected = None
        self.data[1] = new_val
        self.poblate()

    def poblate(self):
        self.listWidget.clear()
        self.route = self.data[self.data[0]+2]
        if self.data[0] != 4:
            if self.data[1] == 0:
                for dot in self.route['points']:
                    self.listWidget.addItem(f"t: {dot[0]}, y: {dot[1]}")
            if self.data[1] == 1:
                for vib in self.route['vibrato']:
                    self.listWidget.addItem(f"ti: {vib[0]}, d: {vib[1]}, amp: {vib[2]}, freq: {vib[3]}, win: {vib[4]}")
            if self.data[1] == 2:
                for fil in self.route['filters']:
                    self.listWidget.addItem(f"ti: {fil[0]}, tf: {fil[1]}, fil: {fil[2]}, params: {fil[3]}")
        else:
            for n in self.route['notes']:
                self.listWidget.addItem(f"{n[0]} s -> {n[1]}")
        self.listWidget.itemClicked.connect(self.item_clicked)
    
    def item_clicked(self, item):
        self.item_selected = self.listWidget.row(item)