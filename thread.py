import math
from PyQt5 import QtCore
import pyaudio
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot

class PThread(QtCore.QObject):

    send_results = QtCore.pyqtSignal(list)
    send_data = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.p = pyaudio.PyAudio()
        self.i = 0
        self.chunks = np.array([])
        self.speech = b''
        self.index = 1
        self.step = 1
        self.limit = 10000

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
            #график разговора
            self.data = self.stream.read(self.frames, exception_on_overflow=False)
            self.speech += self.data
            self.audio_data = np.frombuffer(self.data, dtype=np.int16)

            # график осциллографа
            self.trace = np.arange(0, 5, 0.01)
            self.sinusoid = np.sin(2 * np.pi * self.trace + self.i)

            # график спектра
            self.freq = np.linspace(0, self.rate / 2, int(self.frames / 2))
            self.spectrum = np.fft.fft(self.audio_data)
            self.spectrum = np.abs(self.spectrum[0:int(self.frames / 2)]) * 2 / (128 * self.frames)

            if self.index % (50*self.step) == 0:
                self.chunks = np.append(self.chunks, self.audio_data)
                self.i += 0.1
                self.send_data.emit({
                    'chunks': self.chunks,
                    'trace': self.trace,
                    'sinusoid': self.sinusoid,
                    'spectrum': self.spectrum
                    })

            if self.chunks.size > self.limit:
                self.limit *=10
                self.step *=10
            self.index+=1

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        print(self.chunks.size)

    def send_res_to_table(self):
        self.send_results.emit([self.chunks, self.rate, self.frames, self.channels])

    def reset(self):
        self.i = 0
        self.chunks = np.array([])
        self.speech = b''

    def play(self, li):
        start, end = li
        print('coords', start,end)
        print('speech', len(self.speech))
        start_power = math.floor(math.log10(start))
        if start_power < 4:
            qs = 1
        else:
            qs = int(10**(start_power+1) / 10**4)
        bytes =''
        if end == 0:
            bytes = self.speech[start*2*50*qs:]
        else:
            end_power = math.floor(math.log10(end))
            if end_power < 4:
                qe = 1
            else:
                qe = int(10**(end_power+1) / 10**4)
            bytes = self.speech[start*2*50*qs:end*2*50*qe]

        stream_output = self.p.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=self.rate,
                               output=True)
        stream_output.write(bytes)
        stream_output.stop_stream()
        stream_output.close()
