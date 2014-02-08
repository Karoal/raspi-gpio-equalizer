# Equalizer for 8 LEDs connected through Raspberry Pi GPIO
# Kinda works, for fuck's sake

import wave
import struct
import sys
import numpy as np
# import math

import time
import RPi.GPIO as gpio

import alsaaudio

pins = (22, 18, 16, 15, 13, 12, 11, 7)

filename = sys.argv[1]
low = int(sys.argv[2])              # Lowest frequency bound for the band
high = int(sys.argv[3])             # Highest frequency bound for the band

if __name__ == '__main__':
    # Gets info
    wav = wave.open(filename, 'r')
    data_size = wav.getnframes()
    samp_width = wav.getsampwidth()
    sample_rate = wav.getframerate()
    channels = wav.getnchannels()
    print("Sample rate: ", sample_rate)
    duration = data_size / float(sample_rate)

    # Reads data from file
    sound_data = wav.readframes(data_size)

    # The file is not needed anymore
    wav.close()

    # Unpacks binary data into array
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


def fourier(transform_n, maximum):
    # List to be fft'ed
    start = int(transform_n * sample_size)
    end = int((transform_n * sample_size) + sample_size - 1)
    sample_range = sound_data[start:end]

    # Carries out fft
    fft_data = abs(np.fft.fft(sample_range))

    # Finds mean across desired frequency range
    lowBound = freqToIndex(low)
    hiBound = freqToIndex(high)
    avg = sum(fft_data[lowBound:hiBound]) / (hiBound - lowBound)

    # Making data more readable
    # print(math.log10(avg), '\n')
    avg *= (2**0.5) / sample_size
    if avg > maximum: maximum = avg

    return avg, maximum

# Starts ALSA device
device = alsaaudio.PCM(card='default')
device.setrate(sample_rate)
device.setchannels(channels)

if samp_width == 1:
    device.setformat(alsaaudio.PCM_FORMAT_U8)
elif samp_width == 2:
    device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
elif samp_width == 3:
    device.setformat(alsaaudio.PCM_FORMAT_S24_LE)
elif samp_width == 4:
    device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
else:
    raise ValueError('Unsupported Format')

periodsize = int(round(sample_rate / fouriers_per_second))
print("Period size:", periodsize)
device.setperiodsize(periodsize)

# Initialises gpio pins
gpio.setmode(gpio.BOARD)
for pin in pins:
    gpio.setup(pin, gpio.OUT)
    gpio.output(pin, 0)

# Opens file again for reading
wav = wave.open(filename, 'rb')
data = wav.readframes(periodsize)

# Maximum value of the average so far, used for normalising
maximum = 10000000

time.sleep(2)

for val in range(total_transforms):
    fourier_avg, maximum = fourier(val, maximum)

    # led_num = number of highest lit LED
    led_num = int(round(9 * fourier_avg / (maximum * 0.9)))

    # TTY output
    print("{0:11} | {1:5}, {2:6} sec | fourier: {3:10}, max: {4}".format('#' * led_num + '>', val,
                                                                         round(val / fouriers_per_second, 3),
                                                                         int(fourier_avg), round(maximum)))

    # GPIOs
    for led in range(len(pins)):
        gpio.output(pins[led], 1 if led < led_num else 0)

    # Sound output
    device.write(data)
    data = wav.readframes(periodsize)
