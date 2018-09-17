import unittest
import os
import sys
import argparse
import numpy as np

import audacity as aud

print('Module file:')
print(aud.__file__)

SCRIPT_DIR = os.path.split(os.path.realpath(__file__))[0]
PACKAGE_DIR = os.path.realpath(os.path.join(SCRIPT_DIR,'..'))
DATA_DIR = os.path.join(PACKAGE_DIR, 'data')

TEST_FILE_1 = os.path.join(DATA_DIR, 'test-1.aup')


class testReader(unittest.TestCase):
    TEST_FILE = TEST_FILE_1

    def test_read_data_is_2d(self):
        filename = self.TEST_FILE
        print('Audio file:')
        print(filename)
        au = aud.Aup(filename)
        data = au.get_data()
        assert len(data.shape) == 2

    def test_read_channels_have_same_length(self):
        filename = self.TEST_FILE
        au = aud.Aup(filename)
        data = au.get_data()
        for ii in range(au.nchannels-1):
            assert len(data[ii]) == len(data[ii+1])

    def test_nsample_getter_same_as_data(self):
        filename = self.TEST_FILE
        au = aud.Aup(filename)
        lens = au.get_channel_nsamples()
        for ii, ll in enumerate(lens):
            self.assertEqual(len(au.get_channel_data(ii)), ll)

    def test_single_file_len_is_right(self):
        filename = self.TEST_FILE
        au = aud.Aup(filename)
        chno = 0
        au.open(chno)
        for f, data  in zip(au.files[chno], au.read()):
            self.assertEqual(f[2]-f[1], len(data)/4)

def main():
    global test_file

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='')
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()
    # TODO: Go do something with args.input and args.filename

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = args.unittest_args

    if args.input:
        print('Changing audio file to '+args.input)
        testReader.TEST_FILE = args.input

    unittest.main()


if __name__ == '__main__':
    main()
