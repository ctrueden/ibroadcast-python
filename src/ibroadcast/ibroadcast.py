# This is free and unencumbered software released into the public domain.
# See https://unlicense.org/ for details.

import json
import logging
import re

from . import oauth, util


def from_device_code(client_id, scopes, on_device_code=None, **kwargs):
    """
    Authenticate via the OAuth 2 Device Code Flow.

    :param client_id: OAuth 2 client ID.
    :param scopes: List of OAuth scopes to request.
    :param on_device_code: Callback receiving (user_code, verification_uri,
        verification_uri_complete) so the caller can display them. If None,
        prints to stdout.
    :param kwargs: Additional keyword arguments passed to the constructor.
    :return: An authenticated iBroadcast instance.
    """
    dc = oauth.device_code_request(client_id, scopes)

    if on_device_code:
        on_device_code(
            dc["user_code"],
            dc["verification_uri"],
            dc.get("verification_uri_complete", ""),
        )
    else:
        print(f"\nTo authorize, visit: {dc['verification_uri']}")
        print(f"And enter code: {dc['user_code']}")
        if "verification_uri_complete" in dc:
            print(f"\nOr visit: {dc['verification_uri_complete']}")
        print("\nWaiting for authorization...")

    token_set = oauth.poll_for_token(
        client_id, dc["device_code"], dc.get("interval", 5)
    )

    instance = iBroadcast(
        access_token=token_set.access_token,
        refresh_token=token_set.refresh_token,
        client_id=client_id,
        **kwargs,
    )
    instance.token_set = token_set
    return instance


def from_auth_code(client_id, code, redirect_uri, code_verifier, **kwargs):
    """
    Authenticate via the OAuth 2 Authorization Code Flow.

    :param client_id: OAuth 2 client ID.
    :param code: Authorization code received from the redirect.
    :param redirect_uri: The redirect URI used in the authorization request.
    :param code_verifier: PKCE code verifier.
    :param kwargs: Additional keyword arguments passed to the constructor.
    :return: An authenticated iBroadcast instance.
    """
    token_set = oauth.exchange_auth_code(client_id, code, redirect_uri, code_verifier)

    instance = iBroadcast(
        access_token=token_set.access_token,
        refresh_token=token_set.refresh_token,
        client_id=client_id,
        **kwargs,
    )
    instance.token_set = token_set
    return instance


def from_token_set(token_set, client_id=None, **kwargs):
    """
    Create an instance from a previously saved TokenSet.

    :param token_set: A TokenSet (or dict with token fields).
    :param client_id: OAuth 2 client ID (needed for token refresh).
    :param kwargs: Additional keyword arguments passed to the constructor.
    :return: An iBroadcast instance.
    """
    if isinstance(token_set, dict):
        token_set = oauth.TokenSet.from_dict(token_set)

    instance = iBroadcast(
        access_token=token_set.access_token,
        refresh_token=token_set.refresh_token,
        client_id=client_id,
        **kwargs,
    )
    instance.token_set = token_set
    return instance


class iBroadcast(object):
    """
    Class for making iBroadcast requests.
    """

    def __init__(
        self,
        access_token=None,
        refresh_token=None,
        client_id=None,
        token_refreshed_callback=None,
        client=None,
        version=None,
        device_name=None,
        log=None,
    ):
        """
        Create an iBroadcast client with OAuth 2 tokens.

        :param access_token: OAuth 2 access token.
        :param refresh_token: OAuth 2 refresh token (for automatic refresh).
        :param client_id: OAuth 2 client ID (needed for token refresh).
        :param token_refreshed_callback: Called with a new TokenSet when
            tokens are automatically refreshed, so callers can persist them.
        :param client: Client identifier string.
        :param version: Client version string.
        :param device_name: Device name sent with API requests.
        :param log: Logger instance.
        """
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._token_refreshed_callback = token_refreshed_callback
        self._client = client or "ibroadcast-python"
        self._version = version or util.version
        self._device_name = device_name or client
        self._user_agent = f"{client}/{version}"
        self._log = log or logging.getLogger(client)

        # Library data, populated by refresh().
        self.library = None
        self.albums = {}
        self.artists = {}
        self.playlists = {}
        self.tags = {}
        self.tracks = {}
        self.md5 = None
        self.status = None

    @property
    def access_token(self):
        """Get the current OAuth 2 access token."""
        return self._access_token

    def _auth_headers(self):
        """Build the common headers for authenticated API requests."""
        return {
            "Content-Type": "application/json",
            "User-Agent": self._user_agent,
            "Authorization": f"Bearer {self._access_token}",
        }

    def _request_body(self, mode, **kwargs):
        """Build the common JSON body for API requests."""
        args = {
            "client": self._client,
            "version": self._version,
            "device_name": self._device_name,
            "user_agent": self._user_agent,
            "mode": mode,
        }
        args.update(kwargs)
        return args

    def _refresh(self):
        """Refresh the access token using the refresh token."""
        self._log.info("Refreshing access token...")
        token_set = oauth.refresh_access_token(
            self._client_id,
            self._refresh_token,
        )
        self._access_token = token_set.access_token
        self._refresh_token = token_set.refresh_token
        self.token_set = token_set
        if self._token_refreshed_callback:
            self._token_refreshed_callback(token_set)

    def _jsonrequest(self, mode, url=None, **kwargs):
        if url is None:
            url = f"api.ibroadcast.com/{mode}"
        headers = self._auth_headers()
        args = self._request_body(mode, **kwargs)
        result = util.request(
            self._log, f"https://{url}", data=json.dumps(args), headers=headers
        )

        # Handle token expiry: if authenticated==false, try refresh.
        if (
            not result.get("authenticated", True)
            and self._refresh_token
            and self._client_id
        ):
            self._refresh()
            headers["Authorization"] = f"Bearer {self._access_token}"
            result = util.request(
                self._log, f"https://{url}", data=json.dumps(args), headers=headers
            )

        return result

    def refresh(self):
        """
        Download library data: albums, artists, tracks, etc.

        Raises:
            ServerError on problem completing the request
        """

        # Invalidate any previously downloaded MD5 checksums.
        self.md5 = None

        self._log.info("Downloading library data...")
        self.library = self._jsonrequest("library", url="library.ibroadcast.com")
        self.albums = util.decode(self.library["library"]["albums"])
        self.artists = util.decode(self.library["library"]["artists"])
        self.playlists = util.decode(self.library["library"]["playlists"])
        self.tags = util.decode(self.library["library"]["tags"])
        self.tracks = util.decode(self.library["library"]["tracks"])

    def _download_md5s(self):
        """
        Download MD5 checksums for currently uploaded music files.

        Raises:
            ServerError on problem completing the request
        """
        self._log.info("Downloading MD5 checksums...")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self._user_agent,
            "Authorization": f"Bearer {self._access_token}",
        }
        self.state = util.request(
            self._log, "https://sync.ibroadcast.com", data="", headers=headers
        )
        self.md5 = set(self.state["md5"])

    def get_status(self):
        """
        Fetch user status/info from the API.

        Raises:
            ServerError on problem completing the request
        """
        self.status = self._jsonrequest("status")
        return self.status

    def extensions(self):
        """
        Get file extensions for supported audio formats.
        """
        if self.status is None:
            self.get_status()
        return [ft["extension"] for ft in self.status["supported"]]

    def isuploaded(self, filepath):
        """
        Get whether a given file is already uploaded to the iBroadcast server.

        :param filepath: Path to the file to check.

        Raises:
            ServerError on problem downloading remote MD5 checksums
        """
        if not self.md5:
            self._download_md5s()
        return util.calcmd5(filepath) in self.md5

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
            self._log.info(f"Skipping - already uploaded: {label}")
            return False

        self._log.info(f"Uploading {label}")

        with open(filepath, "rb") as upload_file:
            headers = {
                "User-Agent": self._user_agent,
                "Authorization": f"Bearer {self._access_token}",
            }
            jsondata = util.request(
                self._log,
                "https://upload.ibroadcast.com",
                data={
                    "client": self._client,
                    "version": self._version,
                    "file_path": filepath,
                    "method": self._client,
                },
                headers=headers,
                files={"file": upload_file},
            )
            # The Track ID is embedded in result message; extract it.
            message = jsondata["message"] if "message" in jsondata else ""
            match = re.match(".*\\((.*)\\) uploaded successfully.*", message)
            return None if match is None else match.group(1)

    def album(self, albumid):
        """
        Get the album object with the given ID.

        :param albumid: ID of the album to retrieve.
        :return: The album object.
        """
        return self.albums[str(albumid)]

    def artist(self, artistid):
        """
        Get the artist object with the given ID.

        :param artistid: ID of the artist to retrieve.
        :return: The artist object.
        """
        return self.artists[str(artistid)]

    def playlist(self, playlistid):
        """
        Get the playlist object with the given ID.

        :param playlistid: ID of the playlist to retrieve.
        :return: The playlist object.
        """
        return self.playlists[str(playlistid)]

    def tag(self, tagid):
        """
        Get the tag object with the given ID.

        :param tagid: ID of the tag to retrieve.
        :return: The tag object.
        """
        return self.tags[str(tagid)]

    def track(self, trackid):
        """
        Get the track object with the given ID.

        :param trackid: ID of the track to retrieve.
        :return: The track object.
        """
        return self.tracks[str(trackid)]

    def istagged(self, tagid, trackid):
        """
        Get whether the specified track has the given tag.

        :param tagid: ID of the tag in question.
        :param trackid: ID of the track in question.
        :return: True iff the track is tagged with that tag.
        """
        if tagid not in self.tags:
            return False
        tag = self.tags[tagid]
        if "tracks" not in tag:
            return False
        return int(trackid) in tag["tracks"]

    def gettags(self, trackid):
        """
        Get the tags for the given track.

        :param trackid: ID of the track in question.
        :return: List of tag IDs.
        """
        return [
            tagid for tagid, tag in self.tags.items() if self.istagged(tagid, trackid)
        ]

    def createtag(self, tagname):
        """
        Create a tag.

        :param tagname: Name of the tag to create.
        :return: ID of newly created tag.

        Raises:
            ServerError on problem creating the tag
        """
        jsondata = self._jsonrequest("createtag", tagname=tagname)
        return jsondata["id"]

    def tagtracks(self, tagid, trackids, untag=False):
        """
        Apply or remove the given tag to the specified tracks.

        :param tagid: ID of the tag to apply.
        :param trackids: List of IDs for the tracks to tag.
        :param untag: If true, remove the tag rather than applying it.

        Raises:
            ServerError on problem tagging/untagging the tracks
        """
        self._jsonrequest("tagtracks", tagid=tagid, tracks=trackids, untag=untag)

    def createplaylist(self, name, description="", sharable=False, mood=None):
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
        if mood not in ("Party", "Dance", "Workout", "Relaxed", "Chill"):
            mood = ""
        jsondata = self._jsonrequest(
            "createplaylist",
            name=name,
            description=description,
            make_public=sharable,
            mood=mood,
        )
        return jsondata["playlist_id"]

    def deleteplaylist(self, playlistid):
        """
        Delete a playlist.

        :param playlistid: ID of the playlist to delete.

        Raises:
            ServerError on problem deleting the playlist
        """
        self._jsonrequest("deleteplaylist", playlist=playlistid)

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
        self._jsonrequest("appendplaylist", playlist=playlistid, tracks=trackids)

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
        self._jsonrequest("updateplaylist", playlist=playlistid, tracks=trackids)

    def trash(self, trackids):
        """
        Move the given tracks to the trash.

        :param trackids: List of IDs for the tracks to tag.

        Raises:
            ServerError on problem trashing the tracks
        """
        self._jsonrequest("trash", tracks=trackids)
