import os
import sys
from glob import glob

import audacity

if __name__ == '__main__':
    try:
        path = sys.argv[1]
    except IndexError:
        path = '.'
    line = '"'
    line += 'path'
    line += '","'
    line += 'region_label'
    line += '","'
    line += 'start_sec'
    line += '","'
    line += 'end_sec'
    line += '"'
    print(line)
    for root, dirs, files in os.walk(path):
        for f in files:
            if os.path.splitext(f)[1].lower() == '.aup':
                full_file_path = os.path.join(root,f)
                au = audacity.Aup(full_file_path)
                for reg in au.get_annotation_data():
                    line = '"'
                    line += full_file_path
                    line += '","'
                    line += reg['label']
                    line += '","'
                    line += str(reg['start'])
                    line += '","'
                    line += str(reg['end'])
                    line += '"'

                    print(line)
