import wave
import struct
import sys
import numpy as np
# import math
from pygame import mixer
import time
import RPi.GPIO as gpio

filename = sys.argv[1]
low = int(sys.argv[2])              # Lowest frequency bound for the band
high = int(sys.argv[3])             # Highest frequency bound for the band

if __name__ == '__main__':
    # Gets info
    wav = wave.open(filename, 'r')
    data_size = wav.getnframes()
    samp_width = wav.getsampwidth()
    sample_rate = wav.getframerate()
    print("Sample rate: ", sample_rate)
    duration = data_size / float(sample_rate)

    # Reads data from file
    sound_data = wav.readframes(data_size)

    # The file is not needed anymore
    wav.close()

    # Unpacks binary data into array
    print(data_size)
    print(type(sound_data))
    unpack_fmt = '%di' % (data_size)
    sound_data = struct.unpack(unpack_fmt, sound_data)

    # Process many samples
    fouriers_per_second = 24
    fourier_spread = 1/fouriers_per_second
    fourier_width = fourier_spread
    fourier_width_index = fourier_width * float(sample_rate)

    length_to_process = int(duration) - 1
    print("Fourier width: ", fourier_width)

    total_transforms = int(round(length_to_process * fouriers_per_second))
    fourier_spacing = round(fourier_spread * float(sample_rate))

    print("Duration: ", duration)
    print('For Fourier width of ', fourier_width, " need ", fourier_width_index, " samples each FFT")
    print("Doing ", fouriers_per_second, " Fouriers per second")
    print("Spacing: ", fourier_spacing)
    print("Total transforms: ", total_transforms)

    last_point = int(round(length_to_process * float(sample_rate) + fourier_width_index)) - 1
    sample_size = fourier_width_index
    freq = sample_rate / sample_size * np.arange(sample_size)


def getBandWidth():
    return (2.0 / sample_size) * (sample_rate / 2.0)


def freqToIndex(f):
    # if freq is lower than the bandwidth of the spectrum
    if f < getBandWidth() / 2: return 0
    if f > (sample_rate / 2) - (getBandWidth() / 2):
        return sample_size - 1

    fraction = float(f) / float(sample_rate)
    index = round(sample_size * fraction)
    return index

avg_values = []
maximum = 0

for offset in range(0, total_transforms):
    start = int(offset * sample_size)
    end = int((offset * sample_size) + sample_size - 1)
    sample_range = sound_data[start:end]

    # fft_data = np.fft.fft(sample_range)
    fft_data = abs(np.fft.fft(sample_range))
    # fft_data = [math.log10(x) for x in fft_data]
    # fft_data *= (2**(0.5) / sample_size)

    lowBound = freqToIndex(low)
    hiBound = freqToIndex(high)
    avg = sum(fft_data[lowBound:hiBound]) / (hiBound - lowBound)

    print(offset / fouriers_per_second, ' s')
    print(avg, '\n')
    # print(math.log10(avg), '\n')
    avg *= (2**0.5) / sample_size
    if avg > maximum: maximum = avg

    avg_values.append(avg)

print(len(avg_values)*fouriers_per_second)
print("Max:", maximum)
time.sleep(3)

mixer.init()
mixer.music.load(filename)
mixer.music.play()

for val in avg_values:

for val in avg_values:
    print("{0:20} | {1:20} sec | {2}".format(str('#' * int(round(8 * val/maximum)) + ">"),
                                             avg_values.index(val) / fouriers_per_second,
                                             val))
    time.sleep(1 / fouriers_per_second)
