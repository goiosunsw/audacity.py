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
        with open(aupfile) as xml:
            self.tree = ET.parse(xml)
            self.root = self.tree.getroot()
            self.rate = float(self.root.attrib["rate"])
            ns = {"ns":"http://audacity.sourceforge.net/xml/"}
            self.project = self.root.attrib["projname"]
            self.files = []
            self.channel_info = []
            for channel, wavetrack in enumerate(self.root.findall("ns:wavetrack",
                                                                  ns)):
                aufiles = self._get_files(wavetrack, dir=dir)
                self.files.append(aufiles)
                info = wavetrack.attrib
                self.channel_info.append(info)
            self.nchannels = len(self.files)
            self.aunr = -1
            self.pos = -1
            self.ns=ns

    def _get_files(self, wavetrack, dir='.'):
        clip_idx = 0
        aufiles = []
        for waveclip in wavetrack.findall("ns:waveclip", ns):
            offset_sec = float(waveclip.attrib["offset"])
            clip_offset = int(round(offset_sec * self.rate))
            try:
                last_end = aufiles[-1][2]
            except IndexError:
                last_end = 0
            if clip_offset > last_end:
                aufiles.append(('', last_end , clip_offset, clip_idx))
                clip_idx += 1
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
        self.pos = 0
        return self

    def close(self):
        self.aunr = -1
        self.pos = -1

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
                self.offset = pos - s
                self.pos=pos
                break
        if pos >= f[2]:
            raise EOFError("Seek past end of file")
        self.aunr = i
        self.pos = pos

    def read(self):
        if self.aunr < 0:
            raise IOError("File not opened")
        while self.aunr < len(self.files[self.channel]):
            this_file = self.files[self.channel][self.aunr]
            if not this_file[0]:
                # silent block (before next file)
                silence_len = this_file[2] - self.pos
                zeros = [0.]*silence_len
                self.pos += silence_len
                yield struct.pack('%sf'%len(zeros), *zeros)
            else:
                with open(this_file[0], 'rb') as fd:
                    file_len = this_file[2] - this_file[1]
                    read_len = (file_len - self.offset)
                    fd.seek(-read_len*4, 2)
                    data = fd.read()
                    self.pos += read_len
                    yield data
            self.aunr += 1
            self.offset = 0

    def get_channel_data(self, channel, 
                         t_start=0, t_end=None):
        chunks=[]
        sample_start = int(t_start*self.rate)
        if t_end is not None:
            sample_end = int(t_end*self.rate)
        with self.open(channel) as fd:
            if sample_start > 0:
                self.seek(sample_start)
            for data in fd.read():
                vec = numpy.frombuffer(data, numpy.float32)
                if t_end is not None:
                    if self.pos > sample_end:
                        vec = vec[:-(self.pos-sample_end)]
                        chunks.append(vec)
                        break
                chunks.append(vec)
        return numpy.concatenate(chunks)

    def get_data(self, t_start=0.0, t_end=None):
        # insure that all channels have the same lengths
        max_len = max(self.get_channel_nsamples())
        data = []
        for chno in range(self.nchannels):
            thischan = self.get_channel_data(chno, t_start=t_start,
                t_end=t_end)
            thislen = len(thischan)
            if thislen < max_len:
                thischan = numpy.concatenate((thischan,
                    numpy.zeros(max_len-thislen)))
            data.append(thischan)
        return numpy.array(data).T

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

    def get_channel_names(self):
        return [xx['name'] for xx in self.channel_info]
    
    def get_channel_nsamples(self):
        return [xx[-1][2]+1 for xx in self.files]
