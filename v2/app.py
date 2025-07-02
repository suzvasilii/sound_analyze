from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from thread import PThread
from maket import Ui_MainWindow
import sys
import pyaudio as pa
import numpy as np
import pyqtgraph as pg
class MainWindow(QMainWindow):

    start_thread = QtCore.pyqtSignal(list)
    change_thread_params = QtCore.pyqtSignal(list)
    reset_thread = QtCore.pyqtSignal()
    play_signal = QtCore.pyqtSignal(list)
    def __init__(self):
        super(MainWindow, self).__init__()
        self.p = pa.PyAudio()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initCurves()
        self.initUi()
        self.worker = PThread()
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()
        self.start_thread.connect(self.worker.run)
        self.worker.send_results.connect(self.print_results)
        self.reset_thread.connect(self.worker.reset)
        self.play_signal.connect(self.worker.play)
        self.points = []
        self.cX = []
        self.startX = 0
        self.endX = 0
        self.worker.send_data_to_waveform.connect(self.print_wave)
        self.ui.waveform_plot.scene().sigMouseClicked.connect(self.print_point)
        self.worker.send_data_to_oscilloscope.connect(self.print_osc)
        self.worker.send_data_to_spectrum.connect(self.print_spec)

        self.ui.start_button.clicked.connect(self.start)
        self.ui.stop_button.clicked.connect(self.stop)
        self.ui.reset_button.clicked.connect(self.reset)
        self.ui.apply_button.clicked.connect(self.send_params)
        self.ui.play_button.clicked.connect(self.send_x)
        self.ui.reset_play.clicked.connect(self.reset_play_points)

    def start(self):
        self.start_thread.emit([int(self.ui.chanks_choose.currentText()),
                                int(self.ui.channels_choose.currentText()),
                                int(self.ui.freq_choose.currentText())])
        self.changeUi(start=False, stop = True, reset = False, apply=True)

    def stop(self):
        self.worker.stop()
        self.worker.send_res_to_table()
        self.changeUi(start=True, stop=False, reset=True, apply=False)

    def send_params(self):
        print('params')
        self.worker.stop()
        self.start_thread.emit([int(self.ui.chanks_choose.currentText()),
                                int(self.ui.channels_choose.currentText()),
                                int(self.ui.freq_choose.currentText())])

    def print_wave(self, chunks):
        self.wave_curve.setData(chunks)

    def print_point(self,event):
        pos = event.scenePos()
        self.x = self.ui.waveform_plot.plotItem.vb.mapSceneToView(pos).x()
        self.y = self.ui.waveform_plot.plotItem.vb.mapSceneToView(pos).y()
        point = pg.ScatterPlotItem([self.x], [self.y], pen='r', brush='r', size=10)
        self.ui.waveform_plot.addItem(point)
        self.points.append(point)
        self.cX.append(self.x)
        if len(self.points) > 0:
            self.ui.play_button.setEnabled(True)
            self.ui.reset_play.setEnabled(True)
        self.define_x(self.x)

    def send_x(self):
        self.play_signal.emit([int(self.startX), int(self.endX)])

    def define_x(self,x):
        if len(self.points) == 1:
            self.startX = x
        elif len(self.points) == 2:
            if x > self.startX:
                self.endX = x
            else:
                self.endX = self.startX
                self.startX = x
        else:
            self.ui.waveform_plot.removeItem(self.points[0])
            if x < self.cX[1]:
                self.startX = x
                self.endX = self.cX[1]
            else:
                self.startX = self.cX[1]
                self.endX = x
            self.points = self.points[1:]
            self.cX = self.cX[1:]

    def print_osc(self, data):
        self.osc_curve.setData(data[0], data[1])

    def print_spec(self, spectrum):
        self.spec_curve.setData(spectrum)
    
    def reset(self):
        for i in [self.osc_curve, self.wave_curve, self.spec_curve]:
            i.setData(np.array([]))
        self.reset_thread.emit()

    def reset_play_points(self):
        for i in self.points:
            self.ui.waveform_plot.removeItem(i)
        self.startX = 0
        self.endX = 0
        self.cX = []
        self.points = []
        self.ui.play_button.setEnabled(False)
        self.ui.reset_play.setEnabled(False)

    def initUi(self):
        info = self.p.get_default_input_device_info()
        if int(info['maxInputChannels']) < 2:
            self.ui.channels_choose.model().item(1).setEnabled(False) 
            self.ui.channels_choose.setItemText(1, "2 (недоступно вашим микрофоном)")
        self.ui.stop_button.setEnabled(False)
        self.ui.apply_button.setEnabled(False)
        self.ui.play_button.setEnabled(False)
        self.ui.reset_play.setEnabled(False)

    def initCurves(self):
        self.wave_curve = self.ui.waveform_plot.plot(pen='c')
        self.osc_curve = self.ui.oscilloscope_plot.plot(pen='y')
        self.spec_curve = self.ui.spectrum_plot.plot(pen='m')

    def changeUi(self, start, stop, reset, apply):
        self.ui.start_button.setEnabled(start)
        self.ui.stop_button.setEnabled(stop)
        self.ui.reset_button.setEnabled(reset)
        self.ui.apply_button.setEnabled(apply)

    def print_results(self, chunks):
        self.ui.tabRes.setItem(0,0,QTableWidgetItem(str(chunks.min())))
        self.ui.tabRes.setItem(0,1,QTableWidgetItem(str(chunks.max())))
        self.ui.tabRes.setItem(0,2,QTableWidgetItem(str(chunks.mean())))
        self.ui.tabRes.setItem(0,3,QTableWidgetItem(str(chunks.std())))
        self.ui.tabRes.setItem(0,4,QTableWidgetItem(str(chunks.max() - chunks.min())))

app = QApplication(sys.argv)
mwindow = MainWindow()
mwindow.show()
sys.exit(app.exec_())
