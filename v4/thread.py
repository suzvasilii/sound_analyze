import time

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
        self.cicle =0
        self.index = 0

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
            self.chunks = np.append(self.chunks, self.audio_data)

            # график осциллографа
            self.trace = np.arange(0, 5, 0.01)
            self.sinusoid = np.sin(2 * np.pi * self.trace + self.i)

            # график спектра
            self.freq = np.linspace(0, self.rate / 2, int(self.frames / 2))
            self.spectrum = np.fft.fft(self.audio_data)
            self.spectrum = np.abs(self.spectrum[0:int(self.frames / 2)]) * 2 / (128 * self.frames)


            self.send_data.emit({
                    'chunks': self.chunks,
                    'trace': self.trace,
                    'sinusoid': self.sinusoid,
                    'spectrum': self.spectrum
                })

            if self.chunks.size > 10000:
                self.chunks = self.chunks[-1]
                self.cicle+=1
            self.i += 0.1


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
        print(start,end)
        print(len(self.speech))
        bytes =''
        if end == 0:
            if self.cicle > 0:
                bytes = self.speech[start*2+self.cicle*1000:]
            else: bytes = self.speech[start*2:]
        else:
            if self.cicle > 0:
                bytes = self.speech[start*2+self.cicle*1000:end*2+self.cicle*17000]
            else:
                bytes = self.speech[start*2:end*2]
        stream_output = self.p.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=self.rate,
                               output=True)
        stream_output.write(bytes)
        stream_output.stop_stream()
        stream_output.close()
