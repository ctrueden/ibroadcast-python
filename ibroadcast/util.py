# This is free and unencumbered software released into the public domain.
# See https://unlicense.org/ for details.

import hashlib
import requests

def calcmd5(filepath):
    with open(filepath, 'rb') as fh:
        return hashlib.md5(fh.read()).hexdigest()

def decode(data):
    """
    Normalize a "compressed" dictionary with special 'map' entry.

    This format looks like a way to reduce bandwidth by avoiding repeated
    key strings. Maybe it's a JSON standard with a built-in method to
    decode it? But since I'm REST illiterate, we decode it manually!

    For example, the following data object:

        data = {
           "244526" : [
              "Starter Songs",
              [
                 134082068,
                 134082066,
                 134082069,
                 134082067
              ],
              "1234-1234-1234-1234",
              false,
              null,
              null,
              null,
              null,
              1
           ],
           "map" : {
              "artwork_id" : 7,
              "description" : 6,
              "name" : 0,
              "public_id" : 4,
              "sort" : 8,
              "system_created" : 3,
              "tracks" : 1,
              "type" : 5,
              "uid" : 2
           }
        }

    will be decoded to:

       data = {
          "244526" : {
             "name": "Starter Songs",
             "tracks": [
                134082068,
                134082066,
                134082069,
                134082067
             ],
             "uid": "1234-1234-1234-1234",
             "system_created": false,
             "public_id": null,
             "type": null,
             "description": null,
             "artwork_id": null,
             "sort": 1
          }
       }
    """

    if not 'map' in data or type(data['map']) is not dict:
        return data
    keymap = {v: k for (k, v) in data['map'].items()}

    result = {}
    for k, v in data.items():
        if type(v) is list:
            result[k] = {keymap[i]: v[i] for i in range(len(v))}
    return result

def request(log, url, data, content_type=None, files=None):
    # TODO: Use kwargs properly here.
    if content_type and files:
        response = requests.post(url, data=data, files=files,
            headers={'Content-Type': content_type})
    elif content_type:
        response = requests.post(url, data=data,
            headers={'Content-Type': content_type})
    elif files:
        response = requests.post(url, data=data, files=files)
    else:
        response = requests.post(url, data=data)

    if not response.ok:
        raise ServerError('Server returned bad status: ',
                         response.status_code)
    jsondata = response.json()
    if 'message' in jsondata:
        log.info(jsondata['message'])
    if jsondata['result'] is False:
        raise ValueError('Operation failed.')
    return jsondata

class ServerError(Exception):
    pass
