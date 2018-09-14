import sys
import os
import audacity
from scipy.io import wavfile

inputname = sys.argv[1]
outname, ext = os.path.splitext(os.path.split(inputname)[-1])


aup = audacity.Aup(sys.argv[1])

for ii in range(aup.nchannels):
    c = aup.get_channel_data(ii)
    wavfile.write(outname+'_'+str(ii)+'.wav',int(aup.rate),c)


with open(outname+'_'+'.csv','w') as f:
    for rec in aup.get_annotation_data():
        f.write('{label},{start},{end}\n'.format(**rec))
