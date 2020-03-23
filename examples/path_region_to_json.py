import os
import sys
import json
from glob import glob

import audacity

def file_to_dict(aufile):
    au = audacity.Aup(aufile)

    channel_dict = au.channel_info
    region_dict = au.get_annotation_data()

    return {'channels':channel_dict,
            'regions':region_dict}

if __name__ == '__main__':
    try:
        paths = sys.argv[1:]
    except IndexError:
        path = '.'

    whole_dict = {}


    for path in paths:
        for root, dirs, files in os.walk(path):
            for f in files:
                if os.path.splitext(f)[1].lower() == '.aup':
                    full_file_path = os.path.join(root,f)
                    this_dict = file_to_dict(full_file_path)
                    whole_dict[full_file_path] = this_dict

    print(json.dumps(whole_dict,indent=2))
                
