# audacity.py
A Python tool to read Audacity .aup files

This package can read an Audacity `.aup` file, and can extract the audio for a given channel and save as a `.wav` file.

## Install

```sh
pip install --user git+https://github.com/goiosunsw/audacity.py.git
```

## Command line usage

Extract the second channel from an `.aup` file
```sh
python -m audacity --channel 2 file.aup file-2.wav
```

On the command line, the first channel is `1`.

## API

### `Aup` class

```python
import audacity
aup = audacity.Aup("file.aup")
```

### open file for reading, and read blocks of data:
```python
channel=0
with aup.open(channel) as fd:
  data = fd.read()
  print len(data) ## float32 numbers
```

In the Python API, the first channel is `0`.  

### read all channels to 2D numpy array:
```python
x = aup.get_data(channel, t_start=0.0, t_end=None)
```
Returns an $N_{samples} \times N_{channels}$ array

Optionally provide t_start and/or t_end in seconds to extract only part of the data (quicker)

### read channel to numpy array:
```python
channel=0
x = aup.get_channel_data(channel, t_start=0.0, t_end=None)
```

### read region labels:
```python
labels = aup.get_annotation_data()
```

### convert to `.wav`

```python
channel=0
aup.towav("file.wav", channel, start=0, stop=None)
```
Optionally, you can specify `start` and `stop` (in seconds) to only extract part of an `.aup` file.
