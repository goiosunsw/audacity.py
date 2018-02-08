#!/usr/bin/env python
# (c) 2016 David A. van Leeuwen
##
## audacity/__init__.py .  Main routines for reading Audacity .aup files

import xml.etree.ElementTree as ET
import wave, os, numpy, struct



ns = {"ns":"http://audacity.sourceforge.net/xml/"}


class Aup:
    def __init__(self, aupfile):
        fqpath = os.path.join(os.path.curdir, aupfile)
        dir = os.path.dirname(fqpath)
        xml = open(aupfile)
        self.tree = ET.parse(xml)
        self.root = self.tree.getroot()
        self.rate = float(self.root.attrib["rate"])
        ns = {"ns":"http://audacity.sourceforge.net/xml/"}
        self.project = self.root.attrib["projname"]
        self.files = []
        for channel, wavetrack in enumerate(self.root.findall("ns:wavetrack",
                                                              ns)):
            aufiles = self._get_files(wavetrack, dir=dir)
            self.files.append(aufiles)
        self.nchannels = len(self.files)
        self.aunr = -1
        self.last_pos=0
        self.ns=ns

    def _get_files(self, wavetrack, dir='.'):
        clip_idx = 0
        aufiles = []
        for waveclip in wavetrack.findall("ns:waveclip", ns):
            offset_sec = float(waveclip.attrib["offset"])
            clip_offset = int(offset_sec * self.rate)
            for waveseq in waveclip.findall("ns:sequence", ns):
                for waveblock in waveseq.findall("ns:waveblock", ns):
                    file_offset = clip_offset + int(waveblock.attrib["start"])
                    for b in waveblock.iter("{%s}simpleblockfile" % ns["ns"]):
                        filename = b.attrib["filename"]
                        d1 = filename[0:3]
                        d2 = "d" + filename[3:5]
                        file = os.path.join(dir, self.project, d1, d2, filename)
                        file_len = int(b.attrib["len"])
                        file_end = file_offset + file_len
                        if not os.path.exists(file):
                            raise IOError("File missing in %s: %s" % (self.project,
                                                                      file))
                        else:
                            aufiles.append((file,
                                            file_offset,
                                            file_end,
                                            clip_idx))
                        file_offset += file_len

            clip_idx += 1
        return sorted(aufiles, key=lambda x:x[1])

    def open(self, channel):
        if not (0 <= channel < self.nchannels):
            raise ValueError("Channel number out of bounds")
        self.channel = channel
        self.aunr = 0
        self.offset = -self.files[channel][0][1]
        self.last_pos = 0
        return self

    def close(self):
        self.aunr = -1

    ## a linear search (not great)
    def seek(self, pos):
        if self.aunr < 0:
            raise IOError("File not opened")
        s = 0
        i = 0
        length = 0
        for i, f in enumerate(self.files[self.channel]):
            s = f[1]
            if f[2] > pos:
                length = f[2] - f[1]
                if f[1] > pos:
                    self.silence = True
                    self.aunr = i-1
                    self.offset = -1
                else:
                    self.silence = False
                    self.aunr = i
                    self.offset = pos - s
                break
        if pos >= s:
            raise EOFError("Seek past end of file")
        self.aunr = i
        self.offset = pos - s + length

    def read(self):
        if self.aunr < 0:
            raise IOError("File not opened")
        while self.aunr < len(self.files[self.channel]):
            #pdb.set_trace()
            this_file = self.files[self.channel][self.aunr]
            if self.last_pos < this_file[1]-1:
                # silent block (before next file)
                silence_len = this_file[1] - self.last_pos
                zeros = [0.]*silence_len
                self.last_pos += silence_len
                yield struct.pack('%sf'%len(zeros), *zeros)
            else:
                with open(this_file[0], 'rb') as fd:
                    #fd.seek(self.offset * 4)
                    file_len = this_file[2] - this_file[1]
                    fd.seek((self.offset-file_len)*4, 2)
                    data = fd.read()
                    self.last_pos += file_len
                    yield data
                self.aunr += 1
            self.offset = 0

    def get_channel_data(self, channel):
        chunks=[]
        with self.open(channel) as fd:
            for data in fd.read():
                chunks.append(numpy.frombuffer(data, numpy.float32))
        return numpy.concatenate(chunks)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def towav(self, filename, channel, start=0, stop=None):
        wav = wave.open(filename, "w")
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(self.rate)
        scale = 1 << 15
        if stop:
            length = int(self.rate * (stop - start)) ## number of samples to extract
        with self.open(channel) as fd:
            self.seek(int(self.rate * start))
            for data in fd.read():
                shorts = numpy.short(numpy.clip(numpy.frombuffer(data,
                                                                 numpy.float32)
                                                * scale, -scale, scale-1))
                if stop and len(shorts) > length:
                    shorts = shorts[range(length)]
                format = "<" + str(len(shorts)) + "h"
                wav.writeframesraw(struct.pack(format, *shorts))
                if stop:
                    length -= len(shorts)
                    if length <= 0:
                        break
            wav.writeframes("") ## sets length in wavfile
        wav.close()

    def get_annotation_data(self):
        regions = []
        ii = 0
        for child in self.tree.findall('.//ns:labeltrack',self.ns):
            for it in child.iter():
                attr = it.attrib
                if 't' in attr.keys():
                    tst = float(attr['t'])
                    tend = float(attr['t1'])
                    label = attr['title']
                    regions.append(dict(start=tst, end=tend, label=label))
                    ii += 1
        return regions

    def get_clip_boundaries(self, channel):
        channelfiles = self.files[channel]
        end_of_list = False
        ii = 0
        while not end_of_list:
            file_list = [xx for xx in channelfiles if xx[3]==ii]
            if not file_list:
                end_of_list = True
            else:
                yield (ii, min([yy[1] for yy in file_list]), max([yy[2] for yy in
                                                          file_list]))

            ii += 1
