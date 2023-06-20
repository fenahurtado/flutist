# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'manual_move.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(615, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 2, 0, 1, 3)
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.noteComboBox = QtWidgets.QComboBox(self.groupBox_3)
        self.noteComboBox.setObjectName("noteComboBox")
        self.gridLayout_7.addWidget(self.noteComboBox, 0, 1, 1, 1)
        self.label_12 = QtWidgets.QLabel(self.groupBox_3)
        self.label_12.setObjectName("label_12")
        self.gridLayout_7.addWidget(self.label_12, 0, 0, 1, 1)
        self.moveToNoteCheckBox = QtWidgets.QCheckBox(self.groupBox_3)
        self.moveToNoteCheckBox.setObjectName("moveToNoteCheckBox")
        self.gridLayout_7.addWidget(self.moveToNoteCheckBox, 1, 0, 1, 2)
        self.gridLayout.addWidget(self.groupBox_3, 1, 1, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.tabWidget = QtWidgets.QTabWidget(self.groupBox)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.jointSpaceGrid = QtWidgets.QGridLayout()
        self.jointSpaceGrid.setObjectName("jointSpaceGrid")
        self.label_3 = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.jointSpaceGrid.addWidget(self.label_3, 0, 0, 1, 1)
        self.xSpinBox = QtWidgets.QDoubleSpinBox(self.tab)
        self.xSpinBox.setMaximum(300.0)
        self.xSpinBox.setSingleStep(0.5)
        self.xSpinBox.setObjectName("xSpinBox")
        self.jointSpaceGrid.addWidget(self.xSpinBox, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.jointSpaceGrid.addWidget(self.label_5, 2, 0, 1, 1)
        self.alphaSpinBox = QtWidgets.QDoubleSpinBox(self.tab)
        self.alphaSpinBox.setMinimum(-45.0)
        self.alphaSpinBox.setMaximum(45.0)
        self.alphaSpinBox.setSingleStep(0.5)
        self.alphaSpinBox.setObjectName("alphaSpinBox")
        self.jointSpaceGrid.addWidget(self.alphaSpinBox, 2, 1, 1, 1)
        self.zSpinBox = QtWidgets.QDoubleSpinBox(self.tab)
        self.zSpinBox.setMaximum(300.0)
        self.zSpinBox.setSingleStep(0.5)
        self.zSpinBox.setObjectName("zSpinBox")
        self.jointSpaceGrid.addWidget(self.zSpinBox, 1, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.jointSpaceGrid.addWidget(self.label_4, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.jointSpaceGrid, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.taskSpaceGrid = QtWidgets.QGridLayout()
        self.taskSpaceGrid.setObjectName("taskSpaceGrid")
        self.label_8 = QtWidgets.QLabel(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy)
        self.label_8.setObjectName("label_8")
        self.taskSpaceGrid.addWidget(self.label_8, 2, 0, 1, 1)
        self.offsetSpinBox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.offsetSpinBox.setMinimum(-100.0)
        self.offsetSpinBox.setMaximum(100.0)
        self.offsetSpinBox.setSingleStep(0.5)
        self.offsetSpinBox.setObjectName("offsetSpinBox")
        self.taskSpaceGrid.addWidget(self.offsetSpinBox, 2, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.taskSpaceGrid.addWidget(self.label_6, 0, 0, 1, 1)
        self.thetaSpinBox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.thetaSpinBox.setMinimum(0.0)
        self.thetaSpinBox.setMaximum(90.0)
        self.thetaSpinBox.setSingleStep(0.5)
        self.thetaSpinBox.setObjectName("thetaSpinBox")
        self.taskSpaceGrid.addWidget(self.thetaSpinBox, 1, 1, 1, 1)
        self.rSpinBox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.rSpinBox.setMaximum(300.0)
        self.rSpinBox.setSingleStep(0.5)
        self.rSpinBox.setObjectName("rSpinBox")
        self.taskSpaceGrid.addWidget(self.rSpinBox, 0, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)
        self.label_7.setObjectName("label_7")
        self.taskSpaceGrid.addWidget(self.label_7, 1, 0, 1, 1)
        self.gridLayout_6.addLayout(self.taskSpaceGrid, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_15 = QtWidgets.QLabel(self.tab_3)
        self.label_15.setObjectName("label_15")
        self.gridLayout_4.addWidget(self.label_15, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.tab_3)
        self.label.setObjectName("label")
        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)
        self.pivotDeltaX = QtWidgets.QDoubleSpinBox(self.tab_3)
        self.pivotDeltaX.setObjectName("pivotDeltaX")
        self.gridLayout_4.addWidget(self.pivotDeltaX, 0, 1, 1, 1)
        self.label_14 = QtWidgets.QLabel(self.tab_3)
        self.label_14.setObjectName("label_14")
        self.gridLayout_4.addWidget(self.label_14, 1, 0, 1, 1)
        self.pivotAngle = QtWidgets.QDoubleSpinBox(self.tab_3)
        self.pivotAngle.setMinimum(-45.0)
        self.pivotAngle.setMaximum(45.0)
        self.pivotAngle.setObjectName("pivotAngle")
        self.gridLayout_4.addWidget(self.pivotAngle, 2, 1, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.tab_3)
        self.label_13.setObjectName("label_13")
        self.gridLayout_4.addWidget(self.label_13, 0, 2, 1, 1)
        self.pivotDeltaZ = QtWidgets.QDoubleSpinBox(self.tab_3)
        self.pivotDeltaZ.setObjectName("pivotDeltaZ")
        self.gridLayout_4.addWidget(self.pivotDeltaZ, 0, 3, 1, 1)
        self.pivotReference = QtWidgets.QComboBox(self.tab_3)
        self.pivotReference.setObjectName("pivotReference")
        self.pivotReference.addItem("")
        self.pivotReference.addItem("")
        self.pivotReference.addItem("")
        self.gridLayout_4.addWidget(self.pivotReference, 1, 1, 1, 3)
        self.pivotGoButton = QtWidgets.QPushButton(self.tab_3)
        self.pivotGoButton.setObjectName("pivotGoButton")
        self.gridLayout_4.addWidget(self.pivotGoButton, 2, 2, 1, 2)
        self.tabWidget.addTab(self.tab_3, "")
        self.gridLayout_3.addWidget(self.tabWidget, 0, 0, 1, 2)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)
        self.speedSlider1 = QtWidgets.QSlider(self.groupBox)
        self.speedSlider1.setMinimum(1)
        self.speedSlider1.setMaximum(100)
        self.speedSlider1.setProperty("value", 50)
        self.speedSlider1.setOrientation(QtCore.Qt.Horizontal)
        self.speedSlider1.setObjectName("speedSlider1")
        self.gridLayout_3.addWidget(self.speedSlider1, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 2, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.label_9 = QtWidgets.QLabel(self.groupBox_2)
        self.label_9.setObjectName("label_9")
        self.gridLayout_5.addWidget(self.label_9, 0, 0, 1, 1)
        self.flowSpinBox = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.flowSpinBox.setMaximum(50.0)
        self.flowSpinBox.setSingleStep(0.5)
        self.flowSpinBox.setObjectName("flowSpinBox")
        self.gridLayout_5.addWidget(self.flowSpinBox, 0, 1, 1, 1)
        self.label_10 = QtWidgets.QLabel(self.groupBox_2)
        self.label_10.setObjectName("label_10")
        self.gridLayout_5.addWidget(self.label_10, 1, 0, 1, 1)
        self.ampSpinBox = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.ampSpinBox.setSingleStep(0.5)
        self.ampSpinBox.setObjectName("ampSpinBox")
        self.gridLayout_5.addWidget(self.ampSpinBox, 1, 1, 1, 1)
        self.label_11 = QtWidgets.QLabel(self.groupBox_2)
        self.label_11.setObjectName("label_11")
        self.gridLayout_5.addWidget(self.label_11, 2, 0, 1, 1)
        self.freqSpinBox = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.freqSpinBox.setSingleStep(0.5)
        self.freqSpinBox.setObjectName("freqSpinBox")
        self.gridLayout_5.addWidget(self.freqSpinBox, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox_2, 0, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 615, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Fingers"))
        self.label_12.setText(_translate("MainWindow", "Note"))
        self.moveToNoteCheckBox.setText(_translate("MainWindow", "Move to note"))
        self.groupBox.setTitle(_translate("MainWindow", "Three-axes"))
        self.label_3.setText(_translate("MainWindow", "X"))
        self.label_5.setText(_translate("MainWindow", "Alpha"))
        self.label_4.setText(_translate("MainWindow", "Z"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Joint Space"))
        self.label_8.setText(_translate("MainWindow", "Offset"))
        self.label_6.setText(_translate("MainWindow", "L"))
        self.label_7.setText(_translate("MainWindow", "Theta"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Task Space"))
        self.label_15.setText(_translate("MainWindow", "Angle to pivot"))
        self.label.setText(_translate("MainWindow", "Delta X"))
        self.label_14.setText(_translate("MainWindow", "Respect to"))
        self.label_13.setText(_translate("MainWindow", "Delta Z"))
        self.pivotReference.setItemText(0, _translate("MainWindow", "Mouth end"))
        self.pivotReference.setItemText(1, _translate("MainWindow", "Flute labium"))
        self.pivotReference.setItemText(2, _translate("MainWindow", "Absolute zero"))
        self.pivotGoButton.setText(_translate("MainWindow", "GO"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Pivot"))
        self.label_2.setText(_translate("MainWindow", "Speed"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Flow"))
        self.label_9.setText(_translate("MainWindow", "Flow"))
        self.label_10.setText(_translate("MainWindow", "Vibrato amp"))
        self.label_11.setText(_translate("MainWindow", "Vibrato freq"))
