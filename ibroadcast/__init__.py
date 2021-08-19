# This is free and unencumbered software released into the public domain.
# See https://unlicense.org/ for details.

import json
import logging
import re
import requests

from .about import __version__ as _version
from .util import *

class iBroadcast(object):
    """
    Class for making iBroadcast requests.

    Adapted from ibroadcast-uploader.py at <https://project.ibroadcast.com/>.
    """

    def __init__(self, username, password, log=None, client='ibroadcast-python'):
        self._client = client
        self._log = log or logging.getLogger(client)
        self._login(username, password)

    def _login(self, username, password):
        """
        Login to iBroadcast with the given username and password

        Raises:
            ValueError on invalid login
            ServerError on problem logging in
        """
        self._log.info(f'Logging in as {username}...')
        self.status = response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/status",
            data=json.dumps({
                'mode': 'status',
                'email_address': username,
                'password': password,
                'version': _version,
                'client': self._client,
                'supported_types': 1,
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)
        if 'user' not in self.status:
            raise ValueError('Invalid login.')

        self._log.info(f'Login successful - user_id: {self.user_id()}')
        self.refresh()

    def _download_md5s(self):
        """
        Download MD5 checksums for currently uploaded music files.

        Raises:
            ServerError on problem completing the request
        """
        self._log.info('Downloading MD5 checksums...')
        self.state = response2json(requests.post(
            "https://sync.ibroadcast.com",
            data=f'user_id={self.user_id()}&token={self.token()}',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        ), log=self._log)
        self.md5 = set(self.state['md5'])

    def refresh(self):
        """
        Download library data: albums, artists, tracks, etc.

        Raises:
            ServerError on problem completing the request
        """

        # Invalidate any previously downloaded MD5 checksums.
        self.md5 = None

        self._log.info('Downloading library data...')
        self.library = response2json(requests.post(
            "https://library.ibroadcast.com",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'library',
                'supported_types': False,
                'url': '//library.ibroadcast.com',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)
        self.albums = decode(self.library['library']['albums'])
        self.artists = decode(self.library['library']['artists'])
        self.playlists = decode(self.library['library']['playlists'])
        self.tags = decode(self.library['library']['tags'])
        self.tracks = decode(self.library['library']['tracks'])

    def user_id(self):
        """
        Get the user_id for the current session.
        """
        return self.status['user']['id']

    def token(self):
        """
        Get the authentication token for the current session.
        """
        return self.status['user']['token']

    def extensions(self):
        """
        Get file extensions for supported audio formats.
        """
        return [ft['extension'] for ft in self.status['supported']]

    def isuploaded(self, filepath):
        """
        Get whether a given file is already uploaded to the iBroadcast server.

        :param filepath: Path to the file to check.

        Raises:
            ServerError on problem downloading remote MD5 checksums
        """
        if not self.md5:
            self._download_md5s()
        return calcmd5(filepath) in self.md5

    def upload(self, filepath, label=None, force=False):
        """
        Upload the given file to iBroadcast, if it isn't there already.

        :param filepath: Path to the file for upload.
        :param label: Human-readable file string (e.g., without problematic
                      special characters) to use when logging messages about
                      this operation, or None to use the file path directly.
        :param force: Upload the file even if checksum is already present.
        :return: Track ID of the uploaded file, or None if no upload occurred.

        Raises:
            ServerError on problem completing the request
        """
        if label is None:
            label = filepath
        if not force and self.isuploaded(filepath):
            self._log.info(f'Skipping - already uploaded: {label}')
            return False

        self._log.info(f'Uploading {label}')

        with open(filepath, 'rb') as upload_file:
            jsondata = response2json(requests.post(
                "https://upload.ibroadcast.com",
                data={
                    'user_id': self.user_id(),
                    'token': self.token(),
                    'client': self._client,
                    'version': _version,
                    'file_path': filepath,
                    'method': self._client,
                },
                files={'file': upload_file},
            ), log=self._log)
            # The Track ID is embedded in result message; extract it.
            message = jsondata['message'] if 'message' in jsondata else ''
            match = re.match('.*\((.*)\) uploaded successfully.*', message)
            return None if match is None else match.group(1)

    def istagged(self, tagid, trackid):
        """
        Get whether the specified track has the given tag.

        :param tagid: ID of the tag in question.
        :param trackid: ID of the track in question.
        :return: True iff the track is tagged with that tag.
        """
        if not tagid in self.tags:
            return False
        tag = self.tags[tagid]
        if not 'tracks' in tag:
            return False
        return int(trackid) in tag['tracks']

    def gettags(self, trackid):
        """
        Get the tags for the given track.

        :param trackid: ID of the track in question.
        :return: List of tag IDs.
        """
        return [tagid for tagid, tag in self.tags.items() if self.istagged(tagid, trackid)]

    def createtag(self, tagname):
        """
        Create a tag.

        :param tagname: Name of the tag to create.
        :return: ID of newly created tag.

        Raises:
            ServerError on problem creating the tag
        """
        jsondata = response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/createtag",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'createtag',
                'supported_types': False,
                'tagname': tagname,
                'url': '//api.ibroadcast.com/s/JSON/createtag',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)
        return jsondata['id']

    def tagtracks(self, tagid, trackids, untag=False):
        """
        Apply or remove the given tag to the specified tracks.

        :param tagid: ID of the tag to apply.
        :param trackids: List of IDs for the tracks to tag.
        :param untag: If true, remove the tag rather than applying it.

        Raises:
            ServerError on problem tagging/untagging the tracks
        """
        response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/tagtracks",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'tagtracks',
                'supported_types': False,
                'tagid': tagid,
                'tracks': trackids,
                'untag': untag,
                'url': '//api.ibroadcast.com/s/JSON/tagtracks',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)

    def createplaylist(self, name, description='', sharable=False, mood=None):
        """
        Create a playlist.

        :param name: Name of the playlist to create.
        :param description: Description of the playlist.
        :param sharable: Whether to make the playlist sharable and publicly viewable.
        :param mood: Mood to use for autopopulating tracks:
                     None, Party, Dance, Workout, Relaxed, or Chill.
        :return: ID of newly created playlist.

        Raises:
            ServerError on problem creating the playlist
        """
        if mood not in ('Party', 'Dance', 'Workout', 'Relaxed', 'Chill'): mood = ''

        jsondata = response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/createplaylist",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'createplaylist',
                'supported_types': False,
                'name': name,
                'description': description,
                'make_public': sharable,
                'mood': mood,
                'url': '//api.ibroadcast.com/s/JSON/createplaylist',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)
        return jsondata['playlist_id']

    def deleteplaylist(self, playlistid):
        """
        Delete a playlist.

        :param playlistid: ID of the playlist to delete.

        Raises:
            ServerError on problem deleting the playlist
        """
        response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/deleteplaylist",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'deleteplaylist',
                'supported_types': False,
                'playlist': playlistid,
                'url': '//api.ibroadcast.com/s/JSON/deleteplaylist',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)

    def addtracks(self, playlistid, trackids):
        """
        Add tracks to the given playlist.

        Unlike settracks, this operation will append to, not overwrite,
        the playlist's tracks.

        :param playlistid: ID of the playlist to update.
        :param trackids: List of IDs for the tracks to be added.

        Raises:
            ServerError on problem updating the playlist
        """
        response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/appendplaylist",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'appendplaylist',
                'supported_types': False,
                'playlist': playlistid,
                'tracks': trackids,
                'url': '//api.ibroadcast.com/s/JSON/appendplaylist',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)

    def settracks(self, playlistid, trackids):
        """
        Update the given playlist to consist of the specified tracks.

        Unlike addtracks, this operation will overwrite, not append to,
        the playlist's tracks.

        :param playlistid: ID of the playlist to update.
        :param trackids: List of IDs for the playlist tracks.

        Raises:
            ServerError on problem updating the playlist
        """
        response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/updateplaylist",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'updateplaylist',
                'supported_types': False,
                'playlist': playlistid,
                'tracks': trackids,
                'url': '//api.ibroadcast.com/s/JSON/updateplaylist',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)

    def trash(self, trackids):
        """
        Move the given tracks to the trash.

        :param trackids: List of IDs for the tracks to tag.

        Raises:
            ServerError on problem trashing the tracks
        """
        response2json(requests.post(
            "https://api.ibroadcast.com/s/JSON/tagtracks",
            data=json.dumps({
                '_token': self.token(),
                '_userid': self.user_id(),
                'client': self._client,
                'version': _version,
                'mode': 'trash',
                'supported_types': False,
                'tracks': trackids,
                'url': '//api.ibroadcast.com/s/JSON/tagtracks',
            }),
            headers={'Content-Type': 'application/json'}
        ), log=self._log)
