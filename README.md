# iBroadcast Python client

This Python package provides a client for working with your
[iBroadcast](https://www.ibroadcast.com/) music collection.

## Setup

### Stable version

To install the latest release into your local environment:
```
pip install ibroadcast
```

### Development version

To install the latest development version from source:
```
git clone https://github.com/ctrueden/ibroadcast-python
cd ibroadcast-python
pip install -e .
```

## Usage

### Connect

To connect to iBroadcast, create an `ibroadcast.iBroadcast` object with your
login credentials:

```python
>>> import ibroadcast
>>> username = 'chuckles@example.com'
>>> password = 'HappyClown123'
>>> ib = ibroadcast.iBroadcast(username, password)
```

### Query tracks

Track data can be found in `ib.tracks`.

Here is an example that lists tracks from the year 1984:

```python
>>> from pprint import pprint
>>> tracks_from_1984 = [track for (trackid, track) in ib.tracks.items() if track['year'] == 1984]
>>> pprint(tracks_from_1984)
[{'album_id': 49436760,
  'artist_id': 17407280,
  'artwork_id': 1892638,
  'enid': 0,
  'file': '/128/a8b/567/150924731',
  'genre': 'Pop',
  'length': 205,
  'path': 'music/Artists/Kansas/(1984) The Best of Kansas',
  'plays': 1,
  'rating': 0,
  'replay_gain': '0.5',
  'size': 3572231,
  'title': 'Dust in the Wind',
  'track': 4,
  'trashed': False,
  'type': 'audio/mpeg3',
  'uid': '',
  'uploaded_on': '2020-12-10',
  'uploaded_time': '16:09:59',
  'year': 1984},
 {'album_id': 49438358,
  'artist_id': 17407663,
  'artwork_id': 465315,
  'enid': 0,
  'file': '/128/962/d79/150926596',
  'genre': 'New Wave, Post-Punk, Rock, Funk',
  'length': 307,
  'path': 'music/Artists/Talking Heads/(1984) Stop Making Sense',
  'plays': 1,
  'rating': 0,
  'replay_gain': '0.8',
  'size': 6510922,
  'title': 'Girlfriend Is Better',
  'track': 5,
  'trashed': False,
  'type': 'audio/mpeg3',
  'uid': '',
  'uploaded_on': '2020-12-10',
  'uploaded_time': '16:14:56',
  'year': 1984}]
```

### Query albums

Album data can be found in `ib.albums`.

Here is an example that lists albums from the year 1984:

```python
>>> albums_from_1984 = [album for (albumid, album) in ib.albums.items() if album['year'] == 1984]
>>> pprint(albums_from_1984)
[{'artist_id': 17407663,
  'disc': 1,
  'name': 'Stop Making Sense',
  'rating': 0,
  'tracks': [189817292],
  'trashed': False,
  'year': 1984},
 {'artist_id': 17407280,
  'disc': 1,
  'name': 'The Best of Kansas',
  'rating': 0,
  'tracks': [189815191],
  'trashed': False,
  'year': 1984}]
```

### Query artists

Artist data can be found in `ib.artists`.

Here is an example that lists artists with more than 170 tracks:

```python
>>> [artist['name'] for artist in ib.artists.values() if len(artist['tracks']) >= 170]
['Scooter', 'Megadeth', 'Bad Religion', 'Metallica', 'Green Day']
```

### Query playlists

Playlist data can be found in `ib.playlists`.

Here is an example that lists the names of all playlists:

```python
>>> [playlist['name'] for playlist in ib.playlists.values()]
['Jonathan Hall', 'Army of Hardcore', 'Most Recent Uploads', 'Recently Played', 'Stand Up', 'Roads Untraveled', 'The Storm', 'Thumbs Up']
```

Here's an example that lists the track names of a particular playlist:

```python
>>> def track2string(ib, track):
...   title = track['title']
...   artistid = track['artist_id']
...   artist = ib.artist(artistid)
...   return f"{artist['name']} - {title}"
...
>>> thumbsup = next(pl for pl in ib.playlists.values() if pl['name'] == 'Thumbs Up')
>>> for trackid in thumbsup['tracks']:
...   track = ib.track(trackid)
...   print(track2string(ib, track))
...
Ozzy Osbourne - I Don't Know
ELLEGARDEN - Mr. Feather
The Dreaming - Become Like You
RMB - Everything (Can't Hide version)
Linkin Park - The Catalyst
Breathe Carolina - Blackout
Lady Gaga - Swine
Adam Lambert - Feeling Good
Virtual Riot - Energy Drink
Jim Yosef - Link
MDK - Hyper Beam
Hybrid - I Know
```

### Query tags

Tag data can be found in `ib.tags`.

Here is an example that lists all tracks tagged "favorites" from 2010 or later:

```python
>>> favorite_trackids = next(tag['tracks'] for tag in ib.tags.values() if tag['name'] == 'favorites')
>>> for trackid in favorite_trackids:
...   track = ib.track(trackid)
...   year = track['year']
...   if year < 2010: continue
...   print(f"[{year}] {track2string(ib, track)}")
...
[2010] Bad Religion - Only Rain
[2016] Green Day - Still Breathing
[2012] The Offspring - Dirty Magic
[2012] Imagine Dragons - Radioactive
[2013] All Time Low - Fool's Holiday
[2013] Michael Bublé - It's a Beautiful Day
[2010] Kerry Ellis - Defying Gravity
[2010] Glee Cast - Defying Gravity
[2013] Kristen Anderson‐Lopez & Robert Lopez - Let It Go
[2014] The Glitch Mob feat. Aja Volkman - Our Demons
[2012] Great Big Sea - Run Runaway
[2010] Andrew Lippa - Happy / Sad
```

### Available iBroadcast API methods

```python
>>> help(ib)
Help on iBroadcast in module ibroadcast object:

class iBroadcast(builtins.object)
 |  iBroadcast(username, password, log=None, client='ibroadcast-python', version='1.1.0')
 |
 |  Class for making iBroadcast requests.
 |
 |  Adapted from ibroadcast-uploader.py at <https://project.ibroadcast.com/>.
 |
 |  Methods defined here:
 |
 |  __init__(self, username, password, log=None, client='ibroadcast-python', version='1.1.0')
 |      Initialize self.  See help(type(self)) for accurate signature.
 |
 |  addtracks(self, playlistid, trackids)
 |      Add tracks to the given playlist.
 |
 |      Unlike settracks, this operation will append to, not overwrite,
 |      the playlist's tracks.
 |
 |      :param playlistid: ID of the playlist to update.
 |      :param trackids: List of IDs for the tracks to be added.
 |
 |      Raises:
 |          ServerError on problem updating the playlist
 |
 |  album(self, albumid)
 |      Get the album object with the given ID.
 |
 |      :param albumid: ID of the album to retrieve.
 |      :return: The album object.
 |
 |  artist(self, artistid)
 |      Get the artist object with the given ID.
 |
 |      :param artistid: ID of the artist to retrieve.
 |      :return: The artist object.
 |
 |  createplaylist(self, name, description='', sharable=False, mood=None)
 |      Create a playlist.
 |
 |      :param name: Name of the playlist to create.
 |      :param description: Description of the playlist.
 |      :param sharable: Whether to make the playlist sharable and publicly viewable.
 |      :param mood: Mood to use for autopopulating tracks:
 |                   None, Party, Dance, Workout, Relaxed, or Chill.
 |      :return: ID of newly created playlist.
 |
 |      Raises:
 |          ServerError on problem creating the playlist
 |
 |  createtag(self, tagname)
 |      Create a tag.
 |
 |      :param tagname: Name of the tag to create.
 |      :return: ID of newly created tag.
 |
 |      Raises:
 |          ServerError on problem creating the tag
 |
 |  deleteplaylist(self, playlistid)
 |      Delete a playlist.
 |
 |      :param playlistid: ID of the playlist to delete.
 |
 |      Raises:
 |          ServerError on problem deleting the playlist
 |
 |  extensions(self)
 |      Get file extensions for supported audio formats.
 |
 |  gettags(self, trackid)
 |      Get the tags for the given track.
 |
 |      :param trackid: ID of the track in question.
 |      :return: List of tag IDs.
 |
 |  istagged(self, tagid, trackid)
 |      Get whether the specified track has the given tag.
 |
 |      :param tagid: ID of the tag in question.
 |      :param trackid: ID of the track in question.
 |      :return: True iff the track is tagged with that tag.
 |
 |  isuploaded(self, filepath)
 |      Get whether a given file is already uploaded to the iBroadcast server.
 |
 |      :param filepath: Path to the file to check.
 |
 |      Raises:
 |          ServerError on problem downloading remote MD5 checksums
 |
 |  playlist(self, playlistid)
 |      Get the playlist object with the given ID.
 |
 |      :param playlistid: ID of the playlist to retrieve.
 |      :return: The playlist object.
 |
 |  refresh(self)
 |      Download library data: albums, artists, tracks, etc.
 |
 |      Raises:
 |          ServerError on problem completing the request
 |
 |  settracks(self, playlistid, trackids)
 |      Update the given playlist to consist of the specified tracks.
 |
 |      Unlike addtracks, this operation will overwrite, not append to,
 |      the playlist's tracks.
 |
 |      :param playlistid: ID of the playlist to update.
 |      :param trackids: List of IDs for the playlist tracks.
 |
 |      Raises:
 |          ServerError on problem updating the playlist
 |
 |  tag(self, tagid)
 |      Get the tag object with the given ID.
 |
 |      :param tagid: ID of the tag to retrieve.
 |      :return: The tag object.
 |
 |  tagtracks(self, tagid, trackids, untag=False)
 |      Apply or remove the given tag to the specified tracks.
 |
 |      :param tagid: ID of the tag to apply.
 |      :param trackids: List of IDs for the tracks to tag.
 |      :param untag: If true, remove the tag rather than applying it.
 |
 |      Raises:
 |          ServerError on problem tagging/untagging the tracks
 |
 |  token(self)
 |      Get the authentication token for the current session.
 |
 |  track(self, trackid)
 |      Get the track object with the given ID.
 |
 |      :param trackid: ID of the track to retrieve.
 |      :return: The track object.
 |
 |  trash(self, trackids)
 |      Move the given tracks to the trash.
 |
 |      :param trackids: List of IDs for the tracks to tag.
 |
 |      Raises:
 |          ServerError on problem trashing the tracks
 |
 |
 |  upload(self, filepath, label=None, force=False)
 |      Upload the given file to iBroadcast, if it isn't there already.
 |
 |      :param filepath: Path to the file for upload.
 |      :param label: Human-readable file string (e.g., without problematic
 |                    special characters) to use when logging messages about
 |                    this operation, or None to use the file path directly.
 |      :param force: Upload the file even if checksum is already present.
 |      :return: Track ID of the uploaded file, or None if no upload occurred.
 |
 |      Raises:
 |          ServerError on problem completing the request
 |
 |  user_id(self)
 |      Get the user_id for the current session.
```

## Getting help

File an issue in the
[issue tracker](https://github.com/ctrueden/ibroadcast-python/issues).

## Contributing

PRs welcome! ^.~

### Testing changes

This project has no unit tests, but there are integration tests.
They require a valid username and password to iBroadcast.
All of the integration tests are read-only.

```shell
$ python tests/integration.py
INFO:root:Please enter iBroadcast credentials:
Username: chuckles@example.com
Password:
INFO:root:Logging in as chuckles@example.com...
INFO:root:ok
INFO:root:Login successful - user_id: 12345
INFO:root:Downloading library data...
INFO:root:Checked 995 albums totaling 5951 tracks.
.INFO:root:Checked 1790 artists totaling 5951 tracks.
...INFO:root:Downloading MD5 checksums...
INFO:root:Returning list of md5 checksums from server
.INFO:root:Checked 8 playlists totaling 1691 tracks.
.INFO:root:Checked 17 tags totaling 2208 tracks.
INFO:root:Checked 5951 tracks.
..
----------------------------------------------------------------------
Ran 10 tests in 0.567s

OK
```
