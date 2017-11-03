"""
	This code is adapted from work by Frank Zalkow, retrieved 11/1/2017 by Nick Santos.
	Original work available at http://www.frank-zalkow.de/en/code-snippets/create-audio-spectrograms-with-python.html?i=1
	Original license message below. Parts of adaptation are for preferences, clarity, and current code structure,
	other parts to support 24-bit wave files. Some guidance taken from https://lo.calho.st/projects/generating-a-spectrogram-using-numpy/

	This work is licensed under a Creative Commons Attribution 3.0 Unported License.
	Frank Zalkow, 2012-2013

	WARNING: This code is likely not used in production - I didn't understand the signals processing enough to make it work
	and was getting some data type errors that I couldn't diagnose without understanding it better. Probably going to
	make SOX output the spectrogram for now (it's probably faster anyway).

"""
import os
import wave

import numpy as np
from matplotlib import pyplot as plt
from numpy.lib import stride_tricks

import soundfile

from icefish_backend import local_settings


class Spectrogram(object):  # making a class because we may have some objects to clean up afterward

	def __init__(self, wave_file, window_size=24, temporary_wave_folder=local_settings.TEMPORARY_AUDIO_FOLDER, resample_width=2):
		"""

		:param wave_file:
		:param temporary_wave_folder:
		:param resample_width:  If the wave data needs to be resampled from 24 bit (width of 3) to something else, should
			it be to 32 bit (width of 4) or 16 bit (width of 2). Default is to 16 bit since it's for data viz.
		"""
		self.wave_file = wave_file  # self.wave file has path to original wave file
									# self.working_wave_file has path to what we are *actually* using, which might be a converted version
									# self.wave is the open Python wave object
		self.temporary_wave_folder = temporary_wave_folder
		self.resample_width = resample_width

		self.window_size = window_size

		self.numpy_dtypes = {1: np.int8, 2: np.int16, 4: np.int32}
		self.data_width_mapping = {1: "PCM_U8", 2: "PCM_16", 3: "PCM_24", 4: "PCM_32"}

		self._load_wave(self.wave_file)
		self.get_samples_as_numpy_array()

	def _load_wave(self, wave_file):
		self.wave = wave.open(wave_file, 'r')
		self.sample_rate = self.wave.getframerate()
		self.num_channels = self.wave.getnchannels()
		self.sample_width = self.wave.getsampwidth()
		self.num_frames = self.wave.getnframes()

		self.check_support()

	def check_support(self):
		"""
			Checks to make sure the bit depth of this wave is supported on this platform. If it's not, it resamples it
			to something that is supported and reloads the wave data
		:return:
		"""

		if not self.sample_width in self.numpy_dtypes:  # basically, if the sample width can't be translated to a numpy integer, we need to convert it
			if not self.data_width_mapping[self.resample_width] in soundfile.available_subtypes("WAV"):  # check that this machine can actually do the conversion
				raise ValueError("The current data bit depth ({} bit) isn't supported for spectrogram generation, and the specified bit depth to convert to for visualization ({} bit) isn't supported on this machine.".format(self.sample_width*8, self.resample_width*8))

			base_name = os.path.basename(self.wave_file)
			self.working_wave_file = os.path.join(self.temporary_wave_folder, base_name)  # we'll write a new version out here. Downscaling OK since we're using it for data viz

			data, samplerate = soundfile.read(self.wave_file)  # maybe we could do this without reading it in here too
			soundfile.write(self.working_wave_file, data, samplerate, self.data_width_mapping[self.resample_width])  # but this works for now

			self._load_wave(self.working_wave_file)  # now that we've resampled it, load it over the top of the other
		else:
			self.working_wave_file = self.wave_file  # if it's supported, set working wave to match and move on

	def get_samples_as_numpy_array(self):
		"""
			scipy doesn't support 24 bit waves, so using built in wav reader and converting to numpy myself
		:param wave_file:
		:return:
		"""

		self.frames = self.wave.readframes(1)

		self.frames = np.fromstring(self.frames, dtype=self.numpy_dtypes[self.sample_width])
		self.frames = np.reshape(self.frames, (1, self.num_channels))

		return self.frames


	""" short time fourier transform of audio signal """
	def short_time_fourier_transform(self, sig, frame_size, overlap_factor=0.5, window=np.hanning):
		win = window(frame_size)
		hop_size = int(frame_size - np.floor(overlap_factor * frame_size))

		# zeros at beginning (thus center of 1st window should be for sample nr. 0)
		samples = np.append(np.zeros(np.floor(frame_size / 2.0)), sig)
		# cols for windowing
		cols = np.ceil((len(samples) - frame_size) / float(hop_size)) + 1
		# zeros at end (thus samples can be fully covered by frames)
		samples = np.append(samples, np.zeros(frame_size))

		frames = stride_tricks.as_strided(samples, shape=(cols, frame_size), strides=(samples.strides[0] * hop_size, samples.strides[0])).copy()
		frames *= win

		return np.fft.rfft(frames)

	""" scale frequency axis logarithmically """
	def logscale_spec(self, spec, sr=44100, factor=20.):
		timebins, freqbins = np.shape(spec)

		scale = np.linspace(0, 1, freqbins) ** factor
		scale *= (freqbins - 1) / max(scale)
		scale = np.unique(np.round(scale))

		# create spectrogram with new freq bins
		newspec = np.complex128(np.zeros([timebins, len(scale)]))
		for i in range(0, len(scale)):
			if i == len(scale) - 1:
				newspec[:, i] = np.sum(spec[:, scale[i]:], axis=1)
			else:
				newspec[:, i] = np.sum(spec[:, scale[i]:scale[i + 1]], axis=1)

		# list center freq of bins
		allfreqs = np.abs(np.fft.fftfreq(freqbins * 2, 1. / sr)[:freqbins + 1])
		freqs = []
		for i in range(0, len(scale)):
			if i == len(scale) - 1:
				freqs += [np.mean(allfreqs[scale[i]:])]
			else:
				freqs += [np.mean(allfreqs[scale[i]:scale[i + 1]])]

		return newspec, freqs

	""" plot spectrogram"""
	def plot_spectrogram(self, bin_size=2 ** 10, plot_path=None, colormap="jet"):

		samples = self.get_samples_as_numpy_array()

#		if self.num_channels > 1:
#			samples = (samples[:, 0] + samples[:, 1]) / 2
#		else:
#			samples = samples[:, 0]

		y = np.fft.rfft(samples)

		#return

		# s = self.short_time_fourier_transform(samples, bin_size)

		sshow, freq = self.logscale_spec(y, factor=1.0, sr=self.sample_rate)
		ims = 20. * np.log10(np.abs(sshow) / 10e-6)  # amplitude to decibel

		timebins, freqbins = np.shape(ims)

		plt.figure(figsize=(15, 7.5))
		plt.imshow(np.transpose(ims), origin="lower", aspect="auto", cmap=colormap, interpolation="none")
		plt.colorbar()

		plt.xlabel("time (s)")
		plt.ylabel("frequency (hz)")
		plt.xlim([0, timebins - 1])
		plt.ylim([0, freqbins])

		xlocs = np.float32(np.linspace(0, timebins - 1, 5))
		plt.xticks(xlocs, ["%.02f" % l for l in ((xlocs * len(samples) / timebins) + (0.5 * bin_size)) / self.sample_rate])
		ylocs = np.int16(np.round(np.linspace(0, freqbins - 1, 10)))
		plt.yticks(ylocs, ["%.02f" % freq[i] for i in ylocs])

		if plot_path:
			plt.savefig(plot_path, bbox_inches="tight")
		else:
			plt.show()

		plt.clf()

if __name__ == "__main__":
	import django
	os.environ['DJANGO_SETTINGS_MODULE'] = 'icefish_backend.settings'
	django.setup()

	s = Spectrogram(r"C:\Users\dsx\Dropbox\Antarctica\Audio\wav\CzikoTest1_200khz_SBW1713_20170825_145721.wav")
	s.plot_spectrogram()

