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
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtCore import QTimer
from serial.tools import list_ports
from datetime import datetime, timedelta
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

def_cal_duration = '10'
def_new_cal_table_name = 'Honeywell_3300V'  # TODO 10/12/2026 change this to date or something
def_weight_value = '100'

class app(QGroupBox):
    def __init__(self, port=""):
        super().__init__()
        self.port = port
        self.calibration_on = False

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
        self.create_new_calibration_box()

        top_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self.connect_box)
        col1.addWidget(self.settings_box)
        col1.addWidget(self.calibration_factor_box)
        col1.addWidget(self.datafile_groupbox)
        col1.addWidget(self.new_cal_box)
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
        self.data_receive_box.setMinimumWidth(370)
        
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
        
        self.send_lineedit = QLineEdit()
        self.send_lineedit.setPlaceholderText("-1870")
        self.send_lineedit.setToolTip("Enter new calibration factor to send")
        self.send_btn = QPushButton("Send")
        self.send_lineedit.returnPressed.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        self.send_btn.clicked.connect(lambda: self.send_to_arduino(self.send_lineedit.text()))
        
        layout = QFormLayout()
        layout.addRow(self.send_lineedit,self.send_btn)
        self.calibration_factor_box.setLayout(layout)

    def create_data_receive_box(self):
        self.data_receive_box = QGroupBox()

        self.raw_write_display = QTextEdit(readOnly=True)
        self.raw_read_display = QTextEdit(readOnly=True)

        self.clear_btn_write = QPushButton("Clear")
        self.clear_btn_read = QPushButton("Clear")
        self.clear_btn_write.setToolTip("Clear display")
        self.clear_btn_read.setToolTip("Clear display (Does not affect data collection)")
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
            # find the number of the last data file **with today's date
            last_datafile = list_of_files[len(list_of_files)-1]

            # get the date
            idx_first_underscore = last_datafile.find('_')
            last_datafile_date = last_datafile[0:idx_first_underscore]
            # if it is today's date: find the last datafile number
            if last_datafile_date == current_date:
                # get the number after 'datafile'
                idx_datafile = last_datafile.rfind('datafile')
                idx_next_underscore = last_datafile.find('_', idx_datafile, len(last_datafile))
                idx_nextnext_underscore = last_datafile.find('_', idx_next_underscore+1, len(last_datafile))
                idx_nextnext_period = last_datafile.find('.', idx_next_underscore+1, len(last_datafile))
                # Filter out "not found" (-1) results, then take the smallest index
                candidates = [i for i in (idx_nextnext_underscore,idx_nextnext_period) if i != -1]
                result = min(candidates) if candidates else -1
                last_datafile_num = last_datafile[idx_next_underscore+1:result]
                self.last_datafile_number = int(last_datafile_num)
            # if not: set the number to 0
            else:
                self.last_datafile_number = -1
        
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

    def create_new_calibration_box(self):
        self.new_cal_box = QGroupBox('New calibration')
        
        # File name/Directory
        cal_file_name = def_new_cal_table_name + '_' + current_date
        self.cal_file_dir_wid = QLineEdit(text=main_datafile_directory)
        self.cal_file_name_wid = QLineEdit(text=cal_file_name)

        # Weight (g)
        self.weight_value_wid = QLineEdit(text=def_weight_value)
        self.weight_value_wid.returnPressed.connect(lambda: self.start_calibration_btn.toggle())
        
        # Create new file / Start
        self.create_new_cal_file_btn = QPushButton(text='Create file',checkable=True)
        self.create_new_cal_file_btn.toggled.connect(self.create_new_cal_file_toggled)
        self.start_calibration_btn = QPushButton(text='Start',checkable=True,toggled=self.start_calibration)
        
        # Widget for calibration duration (& timer for visual)
        self.cal_duration_wid = QLineEdit(text=def_cal_duration)
        self.cal_duration_wid.setToolTip('Max 99 seconds')
        self.cal_duration_wid.returnPressed.connect(lambda: self.start_calibration_btn.toggle())
        self.calibration_duration_timer = QTimer()
        self.calibration_duration_timer.setTimerType(0)     # set to millisecond accuracy
        self.calibration_duration_timer.timeout.connect(self.show_cal_duration_time)
        self.calibration_duration_label = QLabel('000.00')

        # Collected values
        self.collected_values_lbl = QLabel('Collected Values:')
        self.collected_values_wid = QTextEdit()
        self.collected_values_wid.setToolTip('Values collected during calibration at this weight rate')
        layout_collected_vals = QVBoxLayout()
        layout_collected_vals.addWidget(self.collected_values_lbl)
        layout_collected_vals.addWidget(self.collected_values_wid)

        # Calibration results
        self.cal_results_min_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_max_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_med_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_mean_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_range_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_num_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_mean_wid.setText('0')
        self.write_to_file_wid = QLineEdit()
        self.write_to_file_btn = QPushButton(text='Write to file')
        self.write_to_file_wid.returnPressed.connect(self.save_calibration_value)
        self.write_to_file_btn.clicked.connect(self.save_calibration_value)
        self.write_to_file_wid.setToolTip('[weight, calibration factor] Results to write to calibration file\nBy default, mean of collected values is put here. Pairs can also be manually entered.')
        self.write_to_file_btn.setToolTip('Write pair to calibration file')
        layout_results = QGridLayout()
        layout_results.addWidget(QLabel('Median:'),     0,0);   layout_results.addWidget(self.cal_results_med_wid,  0,1)
        layout_results.addWidget(QLabel('Mean:'),       0,2);   layout_results.addWidget(self.cal_results_mean_wid, 0,3)
        layout_results.addWidget(QLabel('Range:'),      1,0);   layout_results.addWidget(self.cal_results_range_wid,1,1)
        layout_results.addWidget(QLabel('# of Vals:'),  1,2);   layout_results.addWidget(self.cal_results_num_wid,  1,3)
        final_row_layout = QHBoxLayout()
        final_row_layout.addWidget(QLabel('Results:'))
        final_row_layout.addWidget(self.write_to_file_wid)
        final_row_layout.addWidget(self.write_to_file_btn)
        layout_results.addLayout(final_row_layout,3,0,1,4)
        
        # Written to cal file
        self.cal_file_written_display = QTextEdit(readOnly=True)
        layout_cal_file_output = QVBoxLayout()
        layout_cal_file_output.addWidget(QLabel('Written to file:'))
        layout_cal_file_output.addWidget(self.cal_file_written_display)
        
        # Fix GUI
        self.weight_value_wid.setEnabled(False)
        self.cal_duration_wid.setEnabled(False)
        self.start_calibration_btn.setEnabled(False)
        
        # LAYOUT
        layout_directory = QFormLayout()
        layout_directory.addRow(QLabel("Directory:"),self.cal_file_dir_wid)
        
        layout_file_name = QHBoxLayout()
        layout_file_name.addWidget(QLabel("File name:"))
        layout_file_name.addWidget(self.cal_file_name_wid)
        layout_weight_value = QHBoxLayout()
        layout_weight_value.addWidget(QLabel("Weight (g):"))
        layout_weight_value.addWidget(self.weight_value_wid)
        layout_cal_duration = QHBoxLayout()
        layout_cal_duration.addWidget(QLabel("Duration (s):"))
        layout_cal_duration.addWidget(self.cal_duration_wid)
        layout_cal_duration.addWidget(self.calibration_duration_label)        

        layout_entered_vals = QFormLayout()
        layout_entered_vals.addRow(layout_file_name)
        layout_entered_vals.addRow(layout_cal_duration)
        layout_entered_vals.addRow(layout_weight_value)
        layout_entered_vals.addRow(self.create_new_cal_file_btn,self.start_calibration_btn)

        layout_calibration_box = QGridLayout()
        layout_calibration_box.addLayout(layout_directory,0,0,1,4)      # row0, col0, rowSpan1, colSpan4
        layout_calibration_box.addLayout(layout_entered_vals,1,0)
        layout_calibration_box.addLayout(layout_collected_vals,1,1)
        layout_calibration_box.addLayout(layout_results,1,2)
        layout_calibration_box.addLayout(layout_cal_file_output,1,3)

        self.new_cal_box.setLayout(layout_calibration_box)
        
        # Sizing
        self.collected_values_wid.setMaximumHeight(100)
        self.cal_file_written_display.setMaximumHeight(100)

        self.collected_values_wid.setMaximumWidth(80)
        self.write_to_file_wid.setFixedWidth(80)
        self.write_to_file_btn.setMaximumWidth(80)
        self.cal_file_written_display.setMaximumWidth(115)

    
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
    # CALIBRATION FUNCTIONS
    def create_new_cal_file_toggled(self):
        # Create new file
        if self.create_new_cal_file_btn.isChecked() == True:
            # UI THINGS
            self.create_new_cal_file_btn.setText('End && Save file')
            self.create_new_cal_file_btn.setToolTip('End calibration\n(the file is already saved though)\n(bc it writes the values in real time)')
            self.cal_file_dir_wid.setEnabled(False)
            self.cal_file_name_wid.setEnabled(False)
            
            # Get calibration file name & directory
            self.new_cal_file_name = self.cal_file_name_wid.text()
            self.new_cal_file_dir = self.cal_file_dir_wid.text() + '\\' + self.new_cal_file_name + '.csv'

            # Create calibration file
            if not os.path.exists(self.new_cal_file_dir):
                self.create_file()
            else:
                # Ask user if they want to overwrite the current file
                msg_box = QMessageBox()
                msg_box.setWindowTitle('Confirm Overwrite')
                msg_box.setText(self.new_cal_file_name + ' already exists: overwrite?')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                ret = msg_box.exec()
                if ret == QMessageBox.Yes:
                    logger.info('Deleting %s.csv (%s)', self.new_cal_file_name, self.new_cal_file_dir)
                    os.remove(self.new_cal_file_dir)
                    self.create_file()
                if ret == QMessageBox.No:
                    logger.debug('Enter new file name to create a calibration file')
                    self.create_new_cal_file_btn.setChecked(False)
        
        # Done with calibration - reset user interface
        else:
            logger.info('Ended recording to calibration file %s.csv', self.new_cal_file_name)
            
            # UI THINGS
            self.create_new_cal_file_btn.setText('Create new file')
            self.create_new_cal_file_btn.setToolTip('')
            self.cal_file_dir_wid.setEnabled(True)
            self.cal_file_name_wid.setEnabled(True)
            
            # Disable the weight stuff
            self.weight_value_wid.setEnabled(False)
            self.cal_duration_wid.setEnabled(False)
            self.start_calibration_btn.setEnabled(False)
    
    def start_calibration(self, checked):
        if checked:
            
            # Get weight value & duration
            self.this_cal_weight_value = self.weight_value_wid.text()
            self.this_cal_duration = self.cal_duration_wid.text()

            logger.debug('Starting calibration at %s g', self.this_cal_weight_value)
                        
            # Fix the GUI
            self.write_to_file_btn.setEnabled(False)
            self.create_new_cal_file_btn.setEnabled(False)
            self.start_calibration_btn.setText('End early')
            self.start_calibration_btn.setToolTip('Stop collecting calibration data')
            self.collected_values_wid.clear()
            
            # Initialize empty data arrays
            self.weight_readings = []
            self.calibration_factors = []
            self.serial_values_std = []
            self.start_of_good_values = []
            self.duration_of_good_values = timedelta(0,10)  # 10 sec
            self.all_std_devs = []
            self.values_means = []
            
            # Set calibration object to ON (add incoming values to collected calibration values)
            self.calibration_on = True

            # Start calibration timer
            self.start_cal_duration_timer(int(self.this_cal_duration))

        else:
            # Fix the GUI
            self.write_to_file_btn.setEnabled(True)
            self.create_new_cal_file_btn.setEnabled(True)
            self.start_calibration_btn.setText('Start')
            self.start_calibration_btn.setToolTip('Collect weight data for x seconds')

            # Stop the timer
            if self.calibration_duration_timer.isActive() == True:  self.end_cal_duration_timer()    
    
    def create_file(self):
        logger.info('Creating calibration file: %s.csv (%s)', self.new_cal_file_name, self.new_cal_file_dir)
        file_created_time = get_current_time()
        File = self.new_cal_file_name,file_created_time
        row_headers = 'weight (g)','calibration factor'
        
        # Write file header
        with open(self.new_cal_file_dir,'a',newline='') as f:
            writer = csv.writer(f,delimiter=',')
            writer.writerow(File)
            writer.writerow(row_headers)
        
        # Fix the GUI
        self.weight_value_wid.setEnabled(True)
        self.cal_duration_wid.setEnabled(True)
        self.start_calibration_btn.setEnabled(True)
        self.collected_values_wid.clear()
        self.cal_file_written_display.clear()
    
    def analyze_cal_session(self):
        weight_median = np.median(self.weight_readings)
        weight_mean = round(np.mean(self.weight_readings),3)
        this_round_calibration_factor = round(np.mean(self.calibration_factors),2)
        
        # TODO drop the max and min values
        try:
            # Calculations
            weight_min = min(self.weight_readings)
            weight_max = max(self.weight_readings)
            weight_range = weight_max - weight_min
            self.cal_results_min_wid.setText(str(weight_min))
            self.cal_results_max_wid.setText(str(weight_max))
            self.cal_results_med_wid.setText(str(weight_median))
            self.cal_results_mean_wid.setText(str(weight_mean))
            self.cal_results_range_wid.setText(str(weight_range))
            self.cal_results_num_wid.setText(str(len(self.weight_readings)))
            logger.debug(self.this_cal_weight_value + ' g:' +
                         '\t median: ' + str(weight_median) +
                         '\t mean: ' + str(weight_mean) +
                         '\t range: ' + str(weight_range) +
                         '\t (' + str(self.this_cal_duration) + 'sec, ' + str(len(self.weight_readings)) + ' values)')
            
            # Put mean value in the widget so the user can decide whether to keep it or not
            self.this_cal_weight_mean = weight_mean
            if type(self.this_cal_weight_mean) is np.float64:
                pair = str(self.this_cal_weight_value) + ', ' + str(round(self.this_cal_weight_mean,2))
                pair = str(round(self.this_cal_weight_mean,4)) + ',' + str(this_round_calibration_factor)
                self.write_to_file_wid.setText(pair)
            else:
                logger.warning('calculated value was not an int - cannot save this value')
        
        except ValueError as err:
            # 11/8/2023: got this error when trying to write to file while calibration was running  -this should be fixed now 6/21/2024
            logger.warning('ValueError:' + str(err))
        
        # Clear the array
        self.weight_readings = []
    
    def save_calibration_value(self):
        # Write the data from the widget to the file
        pair_to_write = eval(self.write_to_file_wid.text())     # Convert from string to tuple
        logger.debug('Writing to cal file: %s', pair_to_write)
        try:
            with open(self.new_cal_file_dir,'a',newline='') as f:
                writer = csv.writer(f,delimiter=',')
                writer.writerow(pair_to_write)
        except PermissionError as err:
            logger.warning('Cannot write to file: make sure you don''t have it open anywhere')

        # Display what we wrote to the table
        str_to_display = self.write_to_file_wid.text()
        self.cal_file_written_display.append(str_to_display)
        
        # Clear lists
        self.weight_readings = []
        self.serial_converted = []

        # Reset
        self.calibration_on = False
        self.start_calibration_btn.setChecked(False)


    # CALIBRATION TIMER
    def start_cal_duration_timer(self, duration):
        self.calibration_start_time = datetime.now()
        self.calibration_full_duration = timedelta(0,int(duration))
        self.calibration_duration_timer.start(int(duration))

    def show_cal_duration_time(self):
        current_time = datetime.now()
        current_cal_dur = current_time - self.calibration_start_time
        if current_cal_dur >= self.calibration_full_duration:
            self.end_cal_duration_timer()
        
        cal_dur_display_value = str(current_cal_dur)
        cal_dur_display_value = cal_dur_display_value[5:]   # remove beginning digits, 2 values before decimal point
        cal_dur_display_value = cal_dur_display_value[:-3]  # leave 3 digits after the decimal point
        self.calibration_duration_label.setText(cal_dur_display_value)
    
    def end_cal_duration_timer(self):
        self.calibration_duration_timer.stop()
        self.calibration_on = False
        
        self.start_calibration_btn.setChecked(False)
        self.analyze_cal_session()
    
    
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

                    # if calibration is ON:
                    if self.calibration_on == True:
                        self.weight_readings.append(reading)
                        self.calibration_factors.append(calibration_value)
                        self.collected_values_wid.append(str(calibration_value))

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