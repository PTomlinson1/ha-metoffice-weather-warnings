"""Thin async client for the Met Office NSWWS Public API.

There is no fixed "current warnings" path. `/objects/feed` returns an Atom
feed whose `rel="related"` link ("Latest version of all issued warnings")
points at the actual GeoJSON snapshot, under a URL containing the feed's own
UUID - this has to be discovered on every poll rather than hardcoded.
"""

from __future__ import annotations

import json
import logging
from xml.etree import ElementTree

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_KEY_HEADER, FEED_PATH
from .models import Warning, warnings_from_geojson

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class NSWWSError(Exception):
    """Base error for NSWWS API failures."""


class NSWWSAuthError(NSWWSError):
    """Raised when the API key is rejected."""


class NSWWSConnectionError(NSWWSError):
    """Raised when the API can't be reached, errors, or returns bad data."""


class NSWWSApiClient:
    """Client for the NSWWS feed + issued-warnings snapshot."""

    def __init__(self, hass: HomeAssistant, base_url: str, api_key: str) -> None:
        self._hass = hass
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    async def async_get_active_warnings(self) -> list[Warning]:
        """Fetch all currently active warnings.

        Follows the feed's "related" link to the current snapshot rather
        than assuming a fixed path.
        """
        session = async_get_clientsession(self._hass)

        feed_text = await self._async_get(session, self._url(FEED_PATH))
        issued_url = _parse_issued_url(feed_text)

        issued_text = await self._async_get(session, issued_url)
        payload = _parse_json(issued_text)

        return warnings_from_geojson(payload)

    async def _async_get(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            async with session.get(
                url,
                headers={API_KEY_HEADER: self._api_key},
                timeout=_TIMEOUT,
            ) as response:
                if response.status in (401, 403):
                    raise NSWWSAuthError(f"Authentication rejected by {url}")
                if response.status >= 400:
                    raise NSWWSConnectionError(
                        f"Unexpected status {response.status} from {url}"
                    )
                return await response.text()
        except NSWWSError:
            raise
        except (TimeoutError, aiohttp.ClientError) as err:
            raise NSWWSConnectionError(f"Error connecting to {url}: {err}") from err


def _parse_issued_url(feed_text: str) -> str:
    try:
        root = ElementTree.fromstring(feed_text)
    except ElementTree.ParseError as err:
        raise NSWWSConnectionError(f"Could not parse NSWWS feed XML: {err}") from err

    for link in root.findall("atom:link", _ATOM_NS):
        if link.get("rel") == "related":
            href = link.get("href")
            if href:
                return href

    raise NSWWSConnectionError(
        "NSWWS feed had no rel='related' link to the current warnings snapshot"
    )


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise NSWWSConnectionError(
            f"Could not parse NSWWS response JSON: {err}"
        ) from err
