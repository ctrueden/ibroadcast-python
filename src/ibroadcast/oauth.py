# This is free and unencumbered software released into the public domain.
# See https://unlicense.org/ for details.

"""
OAuth 2 helpers for iBroadcast authentication.

Supports Device Code Flow (for CLI apps) and Authorization Code Flow
(for apps with a browser redirect). Also handles token refresh and revocation.
"""

import base64
import hashlib
import secrets
import time
import urllib.parse

import requests

# OAuth endpoints
OAUTH_BASE = "https://oauth.ibroadcast.com"
AUTHORIZE_URL = f"{OAUTH_BASE}/authorize"
TOKEN_URL = f"{OAUTH_BASE}/token"
DEVICE_CODE_URL = f"{OAUTH_BASE}/device/code"
REVOKE_URL = f"{OAUTH_BASE}/revoke"


class TokenSet:
    """Holds OAuth 2 token data."""

    def __init__(self, access_token, refresh_token, expires_at, scope=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.scope = scope or []

    @property
    def is_expired(self):
        return time.time() >= self.expires_at

    def to_dict(self):
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            access_token=d["access_token"],
            refresh_token=d["refresh_token"],
            expires_at=d["expires_at"],
            scope=d.get("scope", []),
        )

    @classmethod
    def from_response(cls, data):
        """Create a TokenSet from an OAuth token endpoint response."""
        expires_at = time.time() + data["expires_in"]
        scope = data.get("scope", "")
        if isinstance(scope, str):
            scope = scope.split() if scope else []
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=expires_at,
            scope=scope,
        )


# -- PKCE helpers (stdlib only) --


def generate_code_verifier(length=64):
    """Generate a PKCE code verifier (43-128 character random string)."""
    length = max(43, min(128, length))
    return secrets.token_urlsafe(length)[:length]


def generate_code_challenge(verifier):
    """Generate a PKCE S256 code challenge from a code verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


# -- OAuth flows --


class OAuthError(Exception):
    """Raised when an OAuth operation fails."""

    pass


def device_code_request(client_id, scopes):
    """
    Request a device code for the Device Code Flow.

    Returns a dict with keys: device_code, user_code, verification_uri,
    verification_uri_complete, interval, expires_in.
    """
    params = {
        "client_id": client_id,
        "scope": " ".join(scopes) if isinstance(scopes, list) else scopes,
    }
    response = requests.get(DEVICE_CODE_URL, params=params)
    if not response.ok:
        raise OAuthError(
            f"Device code request failed: {response.status_code} {response.text}"
        )
    return response.json()


def poll_for_token(client_id, device_code, interval=5):
    """
    Poll the token endpoint until the user authorizes (Device Code Flow).

    Handles 'authorization_pending' (keep polling) and 'slow_down' (back off).
    Returns a TokenSet on success.
    """
    while True:
        time.sleep(interval)
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "device_code",
                "client_id": client_id,
                "device_code": device_code,
            },
        )
        data = response.json()

        if response.ok:
            return TokenSet.from_response(data)

        error = data.get("error", "")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
            continue
        elif error == "expired_token":
            raise OAuthError(
                "Device code expired. Please restart the authorization flow."
            )
        elif error == "access_denied":
            raise OAuthError("Authorization was denied by the user.")
        else:
            raise OAuthError(
                f"Token polling failed: {error} - {data.get('error_description', '')}"
            )


def exchange_auth_code(client_id, code, redirect_uri, code_verifier):
    """
    Exchange an authorization code for tokens (Authorization Code Flow).

    Returns a TokenSet.
    """
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
    )
    if not response.ok:
        raise OAuthError(
            f"Auth code exchange failed: {response.status_code} {response.text}"
        )
    return TokenSet.from_response(response.json())


def refresh_access_token(client_id, refresh_token, redirect_uri=None):
    """
    Refresh an access token using a refresh token.

    Returns a new TokenSet.
    """
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    if redirect_uri:
        data["redirect_uri"] = redirect_uri
    response = requests.post(TOKEN_URL, data=data)
    if not response.ok:
        raise OAuthError(
            f"Token refresh failed: {response.status_code} {response.text}"
        )
    result = response.json()
    # Preserve the old refresh token if a new one isn't provided.
    if "refresh_token" not in result:
        result["refresh_token"] = refresh_token
    return TokenSet.from_response(result)


def revoke_token(client_id, refresh_token):
    """Revoke a refresh token."""
    response = requests.post(
        REVOKE_URL,
        data={
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
    )
    if not response.ok:
        raise OAuthError(
            f"Token revocation failed: {response.status_code} {response.text}"
        )


def build_authorize_url(
    client_id, state, code_challenge, scopes, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
):
    """
    Build the authorization URL for the Authorization Code Flow.

    Returns the full URL string the user should visit.
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(scopes) if isinstance(scopes, list) else scopes,
        "redirect_uri": redirect_uri,
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
