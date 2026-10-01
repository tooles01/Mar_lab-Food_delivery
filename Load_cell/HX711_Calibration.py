'''
HX711_Calibration.py


PyQt5-based GUI for connecting to, reading from, and calibrating load cell.

To be used with HX711_Calibration.ino

Requirements
    PyQt5
    pyserial


ST 2026
'''

import sys
import logging
import os, csv

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtSerialPort
from serial.tools import list_ports
from datetime import datetime
import re


def create_console_handler():    
    console_handler_formatter = logging.Formatter('%(asctime)s : %(name)-14s :%(levelname)-8s: %(message)s',datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_handler_formatter)
    
    return console_handler

########################################
# CREATE LOGGER
logger = logging.getLogger(name='load cell')
logger.setLevel(logging.DEBUG)
logger.propagate = False        # removes duplicate log messages
console_handler = create_console_handler()
logger.addHandler(console_handler)

def find_log_directory():
    '''
    Returns directory where log file will be stored
        data_file_directory = directory_to_save_to + "\\data_files"
    '''
    
    directory_to_save_to = os.getcwd()
    data_file_directory = os.path.join(directory_to_save_to,'data_files')
    if not os.path.exists(data_file_directory):   # If folder does not exist, create it
        logger.info('creating result file directory at %s', data_file_directory)
        os.mkdir(data_file_directory)
    
    return data_file_directory

def get_current_time():
    current_time = datetime.time(datetime.now())
    current_time_f = current_time.strftime('%H:%M:%S.%f')
    current_time_str = current_time_f[:-3]
    return current_time_str

########################################
current_date = str(datetime.date(datetime.now()))
main_datafile_directory = find_log_directory()
FLOAT = r"[-+]?\d*\.?\d+"

flowSens_baud = 9600
noPortMsg = ' ~ No COM ports detected ~'

class app(QGroupBox):
    def __init__(self, port=""):
        super().__init__()
        self.port = port

        self.generate_ui()
        self.set_connected(False)


    ########################################
    # CREATE GUI ELEMENTS
    def generate_ui(self):
        self.create_connect_box()
        self.create_settings_box()
        self.create_calibration_factor_box()
        self.create_data_receive_box()
        self.create_datafile_box()

        top_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self.connect_box)
        col1.addWidget(self.settings_box)
        col1.addWidget(self.calibration_factor_box)
        col1.addWidget(self.datafile_groupbox)
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
        self.send_lineedit.setToolTip("Enter new calibration factor to send")
        self.send_btn = QPushButton("Send")
        self.send_lineedit.returnPressed.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        self.send_btn.clicked.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        
        layout = QFormLayout()
        layout.addRow(self.dec_factor,self.inc_factor)
        layout.addRow(self.send_lineedit,self.send_btn)
        self.calibration_factor_box.setLayout(layout)

    def create_data_receive_box(self):
        self.data_receive_box = QGroupBox()

        self.raw_write_display = QTextEdit(readOnly=True)
        self.raw_read_display = QTextEdit(readOnly=True)

        self.clear_btn_write = QPushButton("Clear")
        self.clear_btn_read = QPushButton("Clear")
        self.clear_btn_write.setToolTip("Clear previous values from display")
        self.clear_btn_read.setToolTip("Clear previous values from display")
        self.clear_btn_write.clicked.connect(lambda: self.raw_write_display.clear())
        self.clear_btn_read.clicked.connect(lambda: self.raw_read_display.clear())
        
        receive_box_layout = QFormLayout()
        receive_box_layout.addRow(QLabel("Data sent:"),self.clear_btn_write)
        receive_box_layout.addRow(self.raw_write_display)
        receive_box_layout.addRow(QLabel("Data received:"),self.clear_btn_read)
        receive_box_layout.addRow(self.raw_read_display)
        self.data_receive_box.setLayout(receive_box_layout)

    def create_datafile_box(self):
        self.datafile_groupbox = QGroupBox('Data File')
        
        # Get number of last datafile in the folder
        # Check what files are in this folder
        list_of_files = os.listdir(main_datafile_directory)
        list_of_files = [x for x in list_of_files if '.csv' in x]   # only get csv files
        if not list_of_files:
            self.last_datafile_number = -1  # if there are no files
        else:
            # find the number of the last data file
            last_datafile = list_of_files[len(list_of_files)-1]
            idx_fileExt = last_datafile.rfind('.')
            last_datafile = last_datafile[:idx_fileExt] # remove file extension
            idx_underscore = last_datafile.rfind('_')   # find last underscore
            last_datafile_num = last_datafile[idx_underscore+1:]
            if last_datafile_num.isnumeric():   # if what's after the underscore is a number
                self.last_datafile_number = int(last_datafile_num)
            else:
                self.last_datafile_number = 98  # if the last file doesn't have a number
                logger.warning('last datafile in this folder is %s',last_datafile)
        
        # Create datafile name
        self.this_datafile_number = self.last_datafile_number + 1
        self.this_datafile_number_padded = str(self.this_datafile_number).zfill(2) # zero pad
        data_file_name = current_date + '_datafile_' + self.this_datafile_number_padded
        
        # GUI FEATURES
        self.data_file_name_lineEdit = QLineEdit(text=data_file_name)
        self.data_file_textedit = QTextEdit(readOnly=True)
        self.data_file_dir_lineEdit = QLineEdit(text=main_datafile_directory,readOnly=True)
        self.data_file_notes_wid = QLineEdit()
        
        # BUTTONS
        self.begin_record_btn = QPushButton(text='Create File && Begin Recording',checkable=True)
        self.begin_record_btn.clicked.connect(self.begin_record_btn_clicked)
        self.end_record_btn = QPushButton(text='End Recording',checkable=True)
        self.end_record_btn.clicked.connect(self.end_recording)
        self.end_record_btn.setEnabled(False)
        
        record_layout = QHBoxLayout()
        record_layout.addWidget(self.begin_record_btn)
        record_layout.addWidget(self.end_record_btn)
        
        # LAYOUT
        layout = QFormLayout()
        layout.addRow(QLabel('Directory:'),self.data_file_dir_lineEdit)
        layout.addRow(QLabel('File Name:'),self.data_file_name_lineEdit)
        layout.addRow(QLabel('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'))
        layout.addRow(QLabel('Notes:'),self.data_file_notes_wid)
        layout.addRow(QLabel('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'))
        layout.addRow(record_layout)
        layout.addRow(self.data_file_textedit)
        self.datafile_groupbox.setLayout(layout)

    
    ########################################
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
            self.datafile_groupbox.setEnabled(True)
        
        else:
            logger.info('Disconnected from ' + self.port_widget.currentText())
            self.connect_btn.setText("Connect")
            self.connect_btn.setToolTip("Connect to " + self.portStr)
            self.connect_btn.setChecked(False)
            self.refresh_btn.setEnabled(True)
            self.port_widget.setEnabled(True)
            self.settings_box.setEnabled(False)
            self.calibration_factor_box.setEnabled(False)
            self.datafile_groupbox.setEnabled(False)

    ########################################
    # RECORD DATA
    def begin_record_btn_clicked(self):
        # Record button was checked- Begin Recording
        if self.begin_record_btn.isChecked() == True:
            logger.debug('begin record button clicked')
            self.begin_record_btn.setText('Pause Recording')
            self.end_record_btn.setEnabled(True)
            
            # Get file name & directory from GUI
            datafile_name = self.data_file_name_lineEdit.text()
            self.datafile_dir = os.path.join(self.data_file_dir_lineEdit.text(),f"{datafile_name}.csv")
            
            # If directory does not already exist: Create it
            if not os.path.exists(self.data_file_dir_lineEdit.text()):
                os.makedirs(self.data_file_dir_lineEdit.text(), exist_ok=True)
                #os.mkdir(self.data_file_dir_lineEdit.text())
                logger.debug('created folder at %s', self.data_file_dir_lineEdit.text())
            
            # If file does not already exist: Create it & write header
            if not os.path.exists(self.datafile_dir):
                logger.info('Creating new file: %s (%s)', datafile_name, self.datafile_dir)
                File = datafile_name, ' '
                file_created_time = get_current_time()
                file_created_time = file_created_time[:-4]
                Time = 'File Created: ', str(current_date + ' ' + file_created_time)
                # Write file header
                with open(self.datafile_dir,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=',')
                    writer.writerow(File)
                    writer.writerow(Time)
                # Display (for the user)
                self.data_file_textedit.append(datafile_name)
                self.data_file_textedit.append('File Created: ' + str(current_date + ' ' + file_created_time))

                # Write notes to file
                self.this_file_notes = self.data_file_notes_wid.text()
                notes_line_header = 'Notes: ', self.this_file_notes
                with open(self.datafile_dir,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=',')
                    writer.writerow(notes_line_header)
                self.data_file_textedit.append('Notes: ' + self.this_file_notes)
                
                # Write variable headers to file
                DataHead = 'Time','Instrument','Unit','Value'
                with open(self.datafile_dir,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=',')
                    writer.writerow("")
                    writer.writerow("")
                    writer.writerow(DataHead)
            
            # If file already exists
            else:
                logger.warning('File already exists: resuming recording to %s',self.datafile_dir)
        # Record button was unchecked - Pause Recording
        else:
            logger.info('Recording paused')
            self.begin_record_btn.setText('Resume Recording')

    def end_recording(self):
        logger.info('Ended recording to file: %s', self.data_file_name_lineEdit.text())        
        
        self.last_datafile_number = self.this_datafile_number + 1
        
        # update file number in box
        self.this_datafile_number = self.this_datafile_number + 1
        self.this_datafile_number_padded = str(self.this_datafile_number).zfill(2) # zero pad
        data_file_name = current_date + '_datafile_' + self.this_datafile_number_padded
        self.data_file_name_lineEdit.setText(data_file_name)

        self.begin_record_btn.setText('Create File && Begin Recording')
        self.begin_record_btn.setChecked(False)
        self.end_record_btn.setChecked(False)
        self.end_record_btn.setEnabled(False)
        self.data_file_textedit.clear()
   
    
    ########################################
    # SEND/RECEIVE DATA
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            try:
                text = text.decode("utf-8")
                text = text.rstrip('\r\n')
                self.raw_read_display.append(text)

                # Pull out the reading and calibration value
                r = re.search(rf"reading\s*[:=]?\s*({FLOAT})", text, re.IGNORECASE)
                c = re.search(rf"calibration[\s_-]*factor\s*[:=]?\s*({FLOAT})", text, re.IGNORECASE)
                if r and c:
                    reading = float(r.group(1))
                    calibration_value = float(c.group(1))

                    # if recording is ON: write to datafile
                    if self.begin_record_btn.isChecked():
                        current_time = get_current_time()
                        write_to_file = current_time,reading,calibration_value
                        with open(self.datafile_dir,'a',newline='') as f:
                            writer = csv.writer(f,delimiter=',')
                            writer.writerow(write_to_file)
                        display_to_box = str(write_to_file)
                        self.data_file_textedit.append(display_to_box[1:-1])

            except UnicodeDecodeError as err:   logger.error('Serial read error: %s',err)
    
    def send_to_arduino(self, strToSend):
        bArr_send = strToSend.encode()
        try:
            if self.serial.isOpen():
                if len(bArr_send) > 0:
                    self.serial.write(bArr_send)                # send to Arduino
                    self.raw_write_display.append(strToSend)    # Display string that was sent
                else:
                    logger.warning("Nothing to send")
            else:
                logger.warning('Serial port not open, cannot send parameter: %s', strToSend)
        except AttributeError as err:
            logger.warning('(Attribute Error) Serial port not open, cannot send parameter: %s', strToSend)

    
if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    theWindow = app()
    theWindow.show()
    theWindow.setWindowTitle('Load Cell Widget')
    sys.exit(app1.exec_())