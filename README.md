# iBroadcast Python client

This Python package provides a client for working with
[iBroadcast](https://www.ibroadcast.com/) music collections via the
[iBroadcast REST API](https://help.ibroadcast.com/en/developer/api).

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

### Authentication

This library uses OAuth 2 for authentication. You will need a `client_id` from
iBroadcast (see [Creating an App](https://help.ibroadcast.com/en/developer/authentication)).

#### Device Code Flow (recommended for CLI apps)

```python
>>> import ibroadcast
>>> ib = ibroadcast.from_device_code(
...     client_id='your_client_id',
...     scopes=['user.library:read', 'user.library:write', 'user.upload'],
... )
To authorize, visit: https://oauth.ibroadcast.com/device
And enter code: ABCD-1234

Waiting for authorization...
```

#### Authorization Code Flow (for apps with a browser redirect)

```python
>>> import ibroadcast
>>> # Step 1: Generate PKCE verifier and challenge
>>> verifier = ibroadcast.generate_code_verifier()
>>> challenge = ibroadcast.generate_code_challenge(verifier)
>>> # Step 2: Build the authorization URL and direct the user to it
>>> url = ibroadcast.build_authorize_url(
...     client_id='your_client_id',
...     state='random_state_string',
...     code_challenge=challenge,
...     scopes=['user.library:read', 'user.library:write'],
...     redirect_uri='https://your-app.com/callback',
... )
>>> # Step 3: After user authorizes, exchange the code
>>> ib = ibroadcast.from_auth_code(
...     client_id='your_client_id',
...     code='authorization_code_from_redirect',
...     redirect_uri='https://your-app.com/callback',
...     code_verifier=verifier,
... )
```

#### Using existing tokens

```python
>>> import ibroadcast
>>> ib = ibroadcast.iBroadcast(
...     access_token='your_access_token',
...     refresh_token='your_refresh_token',
...     client_id='your_client_id',
... )
```

#### Saving and restoring tokens

```python
>>> # Save tokens for later use
>>> token_dict = ib.token_set.to_dict()
>>> # ... persist token_dict to file ...
>>> # Restore from saved tokens
>>> ib = ibroadcast.from_token_set(token_dict, client_id='your_client_id')
```

### Download library data

After authenticating, download your library data:

```python
>>> ib.refresh()
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
 |  iBroadcast(access_token=None, refresh_token=None, client_id=None,
 |      token_refreshed_callback=None, client='ibroadcast-python',
 |      version='2.0.0', device_name=None, log=None)
 |
 |  Class for making iBroadcast requests.
 |
 |  Class methods:
 |
 |  from_device_code(client_id, scopes, on_device_code=None, **kwargs)
 |      Authenticate via the OAuth 2 Device Code Flow.
 |
 |  from_auth_code(client_id, code, redirect_uri, code_verifier, **kwargs)
 |      Authenticate via the OAuth 2 Authorization Code Flow.
 |
 |  from_token_set(token_set, client_id=None, **kwargs)
 |      Create an instance from a previously saved TokenSet.
 |
 |  Methods defined here:
 |
 |  addtracks(self, playlistid, trackids)
 |      Add tracks to the given playlist.
 |
 |  album(self, albumid)
 |      Get the album object with the given ID.
 |
 |  artist(self, artistid)
 |      Get the artist object with the given ID.
 |
 |  createplaylist(self, name, description='', sharable=False, mood=None)
 |      Create a playlist.
 |
 |  createtag(self, tagname)
 |      Create a tag.
 |
 |  deleteplaylist(self, playlistid)
 |      Delete a playlist.
 |
 |  extensions(self)
 |      Get file extensions for supported audio formats.
 |
 |  get_status(self)
 |      Fetch user status/info from the API.
 |
 |  gettags(self, trackid)
 |      Get the tags for the given track.
 |
 |  istagged(self, tagid, trackid)
 |      Get whether the specified track has the given tag.
 |
 |  isuploaded(self, filepath)
 |      Get whether a given file is already uploaded to the iBroadcast server.
 |
 |  playlist(self, playlistid)
 |      Get the playlist object with the given ID.
 |
 |  refresh(self)
 |      Download library data: albums, artists, tracks, etc.
 |
 |  settracks(self, playlistid, trackids)
 |      Update the given playlist to consist of the specified tracks.
 |
 |  tag(self, tagid)
 |      Get the tag object with the given ID.
 |
 |  tagtracks(self, tagid, trackids, untag=False)
 |      Apply or remove the given tag to the specified tracks.
 |
 |  track(self, trackid)
 |      Get the track object with the given ID.
 |
 |  trash(self, trackids)
 |      Move the given tracks to the trash.
 |
 |  upload(self, filepath, label=None, force=False)
 |      Upload the given file to iBroadcast, if it isn't there already.
```

## Getting help

File an issue in the
[issue tracker](https://github.com/ctrueden/ibroadcast-python/issues).

## Contributing

PRs welcome! ^.~

### Testing changes

This project has no unit tests, but there are integration tests.
They require a valid OAuth 2 access token or client ID for iBroadcast.
All of the integration tests are read-only.

```shell
$ IBROADCAST_CLIENT_ID=your_client_id uv run tests/integration.py
INFO:root:iBroadcast integration tests

To authorize, visit: https://oauth.ibroadcast.com/device
And enter code: ABCD-1234

Waiting for authorization...
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

Or with an existing access token:

```shell
$ IBROADCAST_ACCESS_TOKEN=your_token uv run tests/integration.py
```
