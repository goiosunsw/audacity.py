import unittest
import os
import numpy as np

import audacity as aud

SCRIPT_DIR = os.path.split(__file__)[:-2]
DATA_DIR = os.path.join(*(SCRIPT_DIR + ('data',)))

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


def main():
    unittest.main()


if __name__ == '__main__':
    main()
