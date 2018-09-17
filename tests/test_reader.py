import unittest
import os
import numpy as np

import audacity as aud

SCRIPT_DIR = os.path.split(os.path.realpath(__file__))[0]
PACKAGE_DIR = os.path.realpath(os.path.join(SCRIPT_DIR,'..'))
DATA_DIR = os.path.join(PACKAGE_DIR, 'data')

TEST_FILE_1 = os.path.join(DATA_DIR, 'test-1.aup')

class testReader(unittest.TestCase):
    def test_read_data_is_2d(self, filename=TEST_FILE_1):
        au = aud.Aup(filename)
        data = au.get_data()
        assert len(data.shape) == 2

    def test_read_channels_have_same_length(self, filename=TEST_FILE_1):
        au = aud.Aup(filename)
        data = au.get_data()
        for ii in range(au.nchannels-1):
            assert len(data[ii]) == len(data[ii+1])

    def test_nsample_getter_same_as_data(self, filename=TEST_FILE_1):
        au = aud.Aup(filename)
        lens = au.get_channel_nsamples()
        for ii, ll in enumerate(lens):
            self.assertEqual(len(au.get_channel_data(ii)), ll)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
