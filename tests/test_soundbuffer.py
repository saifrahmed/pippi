from os import path
import random
import shutil
import tempfile
from unittest import TestCase

from pippi.soundbuffer import SoundBuffer

class TestSoundBuffer(TestCase):
    def setUp(self):
        self.soundfiles = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.soundfiles)

    def test_create_empty_buffer(self):
        sound = SoundBuffer()
        self.assertTrue(len(sound) == 0)
        self.assertTrue(not sound)

        sound = SoundBuffer(length=44100)
        self.assertEqual(len(sound), 44100)
        self.assertTrue(sound)

    def test_create_buffer_from_soundfile(self):
        sound = SoundBuffer('tests/sounds/guitar1s.wav')

        self.assertTrue(len(sound) > 0)
        self.assertTrue(sound.samplerate == 44100)

    def test_create_and_resize_buffer_from_soundfile(self):
        length = random.randint(1, 44100)
        sound = SoundBuffer('tests/sounds/guitar1s.wav', length)

        self.assertEqual(len(sound), length)

    def test_save_buffer_to_soundfile(self):
        filename = path.join(self.soundfiles, 'test_save_buffer_to_soundfile.{}')
        sound = SoundBuffer(length=44100)

        sound.write(filename.format('wav'))
        self.assertTrue(path.isfile(filename.format('wav')))

        sound.write(filename.format('flac'))
        self.assertTrue(path.isfile(filename.format('flac')))

        sound.write(filename.format('ogg'))
        self.assertTrue(path.isfile(filename.format('ogg')))

    def test_split_buffer(self):
        sound = SoundBuffer('tests/sounds/guitar1s.wav')

        length = random.randint(1, len(sound)) 
        lengths = []
        for grain in sound.grains(length):
            lengths += [ len(grain) ]

        # The final grain isn't padded with silence, 
        # so it should only be the grain length if 
        # it can be divided equally into the total 
        # length.
        for grain_length in lengths[:-1]:
            self.assertEqual(grain_length, length)

        # Check that the remainder grain is the correct length
        self.assertEqual(lengths[-1], len(sound) - sum(lengths[:-1]))

        # Check that all the grains add up
        self.assertEqual(sum(lengths), len(sound))

    def test_random_split_buffer(self):
        sound = SoundBuffer('tests/sounds/guitar1s.wav')

        lengths = []
        for grain in sound.grains(1, len(sound)):
            lengths += [ len(grain) ]

        # Check that the remainder grain is not 0
        self.assertNotEqual(lengths[-1], 0)

        # Check that all the grains add up
        self.assertEqual(sum(lengths), len(sound))

    def test_window(self):
        sound = SoundBuffer('tests/sounds/guitar1s.wav')
        for window_type in ('sine', 'saw'):
            sound = sound.env(window_type)
            self.assertEqual(sound[0], (0,0))

    def test_slice_frame(self):
        """ A SoundBuffer should return a single frame 
            when sliced into one-dimensionally like:

                frame = sound[frame_index]

            A frame is a tuple of floats, one value 
            for each channel of sound.
        """
        sound = SoundBuffer('tests/sounds/guitar1s.wav')

        indices = (0, -1, len(sound) // 2, -(len(sound) // 2))

        for frame_index in indices:
            frame = sound[frame_index]
            self.assertTrue(isinstance(frame, tuple))
            self.assertEqual(len(frame), sound.channels)
            self.assertTrue(isinstance(frame[0], float))

    def test_slice_sample(self):
        """ Slicing into the second dimension of a SoundBuffer
            will return a single sample at the given channel index.

                sample = sound[frame_index][channel_index]

            Note: A sample is a float, usually between -1.0 and 1.0 
            but pippi will only clip overflow when you ask it to, or 
            when writing a SoundBuffer back to a file. 
            So, numbers can exceed that range during processing and 
            be normalized or clipped as desired later on.
        """

        sound = SoundBuffer('tests/sounds/guitar1s.wav')

        indices = (0, -1, len(sound) // 2, -(len(sound) // 2))

        for frame_index in indices:
            for channel_index in range(sound.channels):
                sample = sound[frame_index][channel_index]
                self.assertTrue(isinstance(sample, float))

