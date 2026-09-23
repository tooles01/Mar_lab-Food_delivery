'''
HX711_Calibration.py


PyQt5-based GUI for connecting to, reading from, and calibrating load cell.

To be used with HX711_Calibration.ino

Requirements
    PtQt5
    pyserial


ST 2026
'''

import sys
import logging

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtSerialPort
from serial.tools import list_ports

def create_console_handler():    
    console_handler_formatter = logging.Formatter('%(asctime)s : %(name)-14s :%(levelname)-8s: %(message)s',datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_handler_formatter)
    
    return console_handler

# CREATE LOGGER
logger = logging.getLogger(name='flow sensor')
logger.setLevel(logging.DEBUG)
logger.propagate = False        # removes duplicate log messages
console_handler = create_console_handler()
logger.addHandler(console_handler)

flowSens_baud = 9600
noPortMsg = ' ~ No COM ports detected ~'

class app(QGroupBox):
    def __init__(self, port=""):
        super().__init__()
        self.port = port

        self.generate_ui()
        self.set_connected(False)

    # CREATE GUI ELEMENTS
    def generate_ui(self):
        self.create_connect_box()
        self.create_settings_box()
        self.create_calibration_factor_box()
        self.create_data_receive_box()

        top_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self.connect_box)
        col1.addWidget(self.settings_box)
        col1.addWidget(self.calibration_factor_box)
        col2 = QVBoxLayout()
        col2.addWidget(self.data_receive_box)
        top_layout.addLayout(col1)
        top_layout.addLayout(col2)

        self.layout = QVBoxLayout()
        self.layout.addLayout(top_layout)
        self.setLayout(self.layout)
        self.setTitle('Load Cell Reading')

        self.connect_box.setMaximumHeight(self.connect_box.sizeHint().height())
        self.settings_box.setMaximumHeight(self.settings_box.sizeHint().height())

    def create_connect_box(self):
        self.connect_box = QGroupBox("Connect")

        self.portLbl = QLabel(text="Port/Device:")
        self.port_widget = QComboBox(currentIndexChanged=self.port_changed)
        self.connect_btn = QPushButton(checkable=True,toggled=self.toggled_connect)
        self.refresh_btn = QPushButton(text="Refresh",clicked=self.get_ports)
        self.get_ports()

        connect_box_layout = QFormLayout()
        connect_box_layout.addRow(self.portLbl,self.port_widget)
        connect_box_layout.addRow(self.refresh_btn,self.connect_btn)
        self.connect_box.setLayout(connect_box_layout)

    def create_settings_box(self):
        self.settings_box = QGroupBox('Settings')
        
        self.tare_lbl = QLabel("<--- Only click this if there is nothing on the scale")
        self.tare_btn = QPushButton(text="Tare")
        self.tare_btn.clicked.connect(lambda: self.send_to_arduino("tare"))
        
        layout = QFormLayout()
        layout.addRow(self.tare_btn,self.tare_lbl)
        self.settings_box.setLayout(layout)

    def create_calibration_factor_box(self):
        self.calibration_factor_box = QGroupBox("Calibration Factor")

        self.dec_factor = QPushButton("-10")
        self.inc_factor = QPushButton("+10")
        self.dec_factor.setToolTip("Decrease calibration factor by 10")
        self.inc_factor.setToolTip("Increase calibration factor by 10")
        self.dec_factor.clicked.connect(lambda: self.send_to_arduino("z"))
        self.inc_factor.clicked.connect(lambda: self.send_to_arduino("a"))
        
        self.send_lineedit = QLineEdit()
        self.send_lineedit.setPlaceholderText("-1870")
        self.send_lineedit.setToolTip("Enter calibration factor")
        self.send_btn = QPushButton("Send")
        self.send_lineedit.returnPressed.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        self.send_btn.clicked.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        
        layout = QFormLayout()
        layout.addRow(self.dec_factor,self.inc_factor)
        layout.addRow(self.send_lineedit,self.send_btn)
        self.calibration_factor_box.setLayout(layout)

    def create_data_receive_box(self):
        self.data_receive_box = QGroupBox()

        self.receive_box = QTextEdit(readOnly=True)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear previous values from display")
        self.clear_btn.clicked.connect(lambda: self.receive_box.clear())
        
        receive_box_layout = QFormLayout()
        receive_box_layout.addRow(QLabel("Data received"),self.clear_btn)
        receive_box_layout.addRow(self.receive_box)
        self.data_receive_box.setLayout(receive_box_layout)
    
    # CONNECT TO DEVICE
    def get_ports(self):
        self.port_widget.clear()
        ports = list_ports.comports()
        if ports:
            for ser in ports:
                port_device = ser[0]
                port_description = ser[1]
                if port_device in port_description:
                    idx1 = port_description.find(port_device)
                    port_description = port_description[:idx1-2]
                ser_str = ('{}: {}').format(port_device,port_description)
                self.port_widget.addItem(ser_str)
        else:
            self.port_widget.addItem(noPortMsg)

        # if any are 'Arduino', set the first one to the current index
        for item_idx in range(0,self.port_widget.count()):
            this_item = self.port_widget.itemText(item_idx)
            if 'Arduino' in this_item:
                break
        if item_idx != []:
            self.port_widget.setCurrentIndex(item_idx)
        else:
            logger.debug('no Arduinos detected :(')
    
    def port_changed(self):
        if self.port_widget.count() != 0:
            self.port = self.port_widget.currentText()
            if self.port == noPortMsg:
                self.portStr = noPortMsg
                self.connect_btn.setEnabled(False)
                self.connect_btn.setText(noPortMsg)
            else:
                self.portStr = self.port[:self.port.index(':')]
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("Connect to  " + self.portStr)
        
    def toggled_connect(self, checked):
        if checked:
            i = self.port.index(':')
            self.comPort = self.port[:i]
            self.serial = QtSerialPort.QSerialPort(self.comPort,baudRate=flowSens_baud,readyRead=self.receive)
            if not self.serial.isOpen():
                if self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.set_connected(True)
                else:
                    self.set_connected(False)
            else:
                self.set_connected(True)
        else:
            try:
                self.serial.close()
                self.set_connected(False)
            except AttributeError as err:
                logger.error("error :( --> %s", err)
    
    def set_connected(self, connected):
        if connected == True:
            logger.info('Connected to ' + self.port_widget.currentText())
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setToolTip("Disconnect from " + self.portStr)
            self.refresh_btn.setEnabled(False)
            self.port_widget.setEnabled(False)
            self.settings_box.setEnabled(True)
            self.calibration_factor_box.setEnabled(True)
        
        else:
            logger.info('Disconnected from ' + self.port_widget.currentText())
            self.connect_btn.setText("Connect")
            self.connect_btn.setToolTip("Connect to " + self.portStr)
            self.connect_btn.setChecked(False)
            self.refresh_btn.setEnabled(True)
            self.port_widget.setEnabled(True)
            self.settings_box.setEnabled(False)
            self.calibration_factor_box.setEnabled(False)

    # SEND/RECEIVE DATA
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            try:
                text = text.decode("utf-8")
                text = text.rstrip('\r\n')
                str_value = text
                dataStr = str_value + '\t'
                self.receive_box.append(dataStr)

                # Send to main window for recording
                try: self.window().receive_data_from_device('flow sensor','FL',str_value)
                except AttributeError as err: pass

            except UnicodeDecodeError as err:   logger.error('Serial read error: %s',err)
    
    def send_to_arduino(self, strToSend):
        bArr_send = strToSend.encode()
        try:
            if self.serial.isOpen():
                self.serial.write(bArr_send)                # send to Arduino
            else:
                logger.warning('Serial port not open, cannot send parameter: %s', strToSend)
        except AttributeError as err:
            logger.warning('(Attribute Error) Serial port not open, cannot send parameter: %s', strToSend)

    
if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    theWindow = app()
    theWindow.show()
    theWindow.setWindowTitle('Flow Sensor Widget')
    sys.exit(app1.exec_())