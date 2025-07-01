from PyQt5 import QtCore
import pyaudio
import numpy as np
import time
from PyQt5.QtCore import  QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot

class PThread(QtCore.QObject):

    send_data_to_waveform = QtCore.pyqtSignal(np.ndarray)
    send_data_to_oscilloscope = QtCore.pyqtSignal(np.ndarray)
    send_data_to_spectrum = QtCore.pyqtSignal(np.ndarray)
    send_results = QtCore.pyqtSignal(np.ndarray)
    def __init__(self):
        super().__init__()
        self.running = False
        self.p = pyaudio.PyAudio()
        self.i = 0
        self.chunks = np.array([])

    @Slot(list)
    def run(self, params):
        self.frames, self.channels, self.rate = params
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames
        )
        self.stream.start_stream()
        self.running = True

        while self.running:
            print(self.rate)
            #график разговора
            data = self.stream.read(self.frames, exception_on_overflow=False)
            self.audio_data = np.frombuffer(data, dtype=np.int16)
            self.chunks= np.append(self.chunks, self.audio_data)
            self.send_data_to_waveform.emit(self.chunks)

            #график осциллографа
            self.trace = np.arange(0, 5+self.i, 0.01)
            self.sinusoid = np.sin(2 * np.pi * self.trace + self.i)
            self.i+=self.rate/1000000
            self.send_data_to_oscilloscope.emit(np.array([self.trace, self.sinusoid]))

            #график спектра
            self.freq = np.linspace(0, self.rate / 2, int(self.frames/2))
            self.spectrum = np.fft.fft(self.audio_data)
            self.spectrum = np.abs(self.spectrum[0:int(self.frames/2)]) *2 / (128*self.frames)
            self.send_data_to_spectrum.emit(self.spectrum)
            time.sleep(.1)

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()

    def send_res_to_table(self):
        self.send_results.emit(self.chunks)

    def reset(self):
        self.i = 0
        self.chunks = np.array([])
