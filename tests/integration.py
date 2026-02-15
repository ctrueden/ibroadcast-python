import logging
import os
import re
import sys
import unittest

import ibroadcast

log = logging.getLogger()
log.setLevel(logging.INFO)
logging.info("iBroadcast integration tests")

# Authenticate via device code flow.
# Requires IBROADCAST_CLIENT_ID environment variable.
client_id = os.environ.get("IBROADCAST_CLIENT_ID")
access_token = os.environ.get("IBROADCAST_ACCESS_TOKEN")
refresh_token = os.environ.get("IBROADCAST_REFRESH_TOKEN")

if access_token:
    # Use existing tokens directly.
    ib = ibroadcast.iBroadcast(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        log=log,
    )
elif client_id:
    # Run device code flow interactively.
    scopes = ["user.library:read", "user.library:write", "user.upload"]
    ib = ibroadcast.from_device_code(
        client_id=client_id,
        scopes=scopes,
        log=log,
    )
else:
    print("Set IBROADCAST_CLIENT_ID or IBROADCAST_ACCESS_TOKEN to run tests.")
    sys.exit(1)

# Download library data.
ib.refresh()


class TestEverything(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestEverything, self).__init__(*args, **kwargs)

    def _check_items(self, data, expectedkeys, itemlabel):
        itemcount = trackcount = 0
        for itemid, item in data.items():
            itemcount += 1
            itemid = int(itemid)  # dict key from json is a string
            self.assertGreater(itemid, 0)
            self.assertTrue(expectedkeys.issubset(item.keys()))
            for trackid in item["tracks"]:
                trackcount += 1
                self.assertIn(str(trackid), ib.tracks)
        log.info(f"Checked {itemcount} {itemlabel} totaling {trackcount} tracks.")

    def test_albums(self):
        albumkeys = {"name", "disc", "artist_id", "trashed", "tracks", "rating", "year"}
        self._check_items(ib.albums, albumkeys, "albums")

    def test_artists(self):
        artistkeys = {"name", "tracks", "trashed", "rating"}
        self._check_items(ib.artists, artistkeys, "artists")

    def test_playlists(self):
        playlistkeys = {
            "name",
            "tracks",
            "uid",
            "system_created",
            "public_id",
            "type",
            "description",
            "artwork_id",
            "sort",
        }
        self._check_items(ib.playlists, playlistkeys, "playlists")

    def test_tags(self):
        tagkeys = {"name", "archived", "tracks"}
        visible_tags = {
            tagid: tag for tagid, tag in ib.tags.items() if not tag["archived"]
        }
        # NB: tracks from hidden (i.e. archived) tags are
        # not populated by the iBroadcast library request!
        self._check_items(visible_tags, tagkeys, "tags")

    def test_tracks(self):
        # trackkeys = {
        #     "track",
        #     "year",
        #     "title",
        #     "genre",
        #     "length",
        #     "album_id",
        #     "artwork_id",
        #     "artist_id",
        #     "enid",
        #     "uploaded_on",
        #     "trashed",
        #     "size",
        #     "path",
        #     "uid",
        #     "rating",
        #     "plays",
        #     "file",
        #     "type",
        #     "replay_gain",
        #     "uploaded_time",
        # }
        # self._check_items(ib.tracks, trackkeys, "tracks")
        trackcount = 0
        for trackid, track in ib.tracks.items():
            trackcount += 1
            trackid = int(trackid)  # dict key from json is a string
            albumid = track["album_id"]
            album = ib.album(albumid)
            self.assertIn(trackid, album["tracks"])
            artistid = track["artist_id"]
            artist = ib.artist(artistid)
            # NB: In my personal library, I have one track whose artist_id points
            # to an artist whose tracks field does not contain that track.
            # self.assertIn(trackid, artist['tracks'])
            if trackid not in artist["tracks"]:
                log.warning(f"{trackid} is not a track of artist {artistid}")
        log.info(f"Checked {trackcount} tracks.")

    def test_md5(self):
        hexpat = re.compile("^[0-9a-f]{32}$")
        ib._download_md5s()  # NB: Force download of checksums.
        for md5sum in ib.md5:
            self.assertTrue(hexpat.match(md5sum))

    def test_status(self):
        status = ib.get_status()
        self.assertIn("user", status)

    def test_extensions(self):
        # fmt: off
        expected_extensions = {
            ".aa", ".aa3", ".aac", ".aac", ".acd", ".acd-zip", ".acm", ".afc",
            ".aif", ".aiff", ".als", ".amr", ".amxd", ".ape", ".ape", ".asf",
            ".at3", ".au", ".caf", ".cda", ".cpr", ".dcf", ".dmsa", ".dmse",
            ".dss", ".emp", ".emx", ".flac", ".flac", ".gpx", ".iff", ".kpl",
            ".m3u", ".m3u", ".m3u8", ".m4a", ".m4b", ".m4r", ".mod", ".mp3",
            ".mpa", ".nra", ".ogg", ".omf", ".opus", ".pcast", ".pls", ".ra",
            ".ram", ".seq", ".sib", ".slp", ".snd", ".wav", ".wma",
        }
        # fmt: on
        self.assertTrue(expected_extensions.issubset(ib.extensions()))

    def test_gettags_istagged(self):
        for tagid, tag in ib.tags.items():
            for trackid in tag["tracks"]:
                track_tags = ib.gettags(trackid)
                self.assertIn(tagid, track_tags)
                self.assertTrue(ib.istagged(tagid, trackid))

    def test_access_token(self):
        self.assertIsNotNone(ib.access_token)
        self.assertGreater(len(ib.access_token), 0)


if __name__ == "__main__":
    unittest.main()
