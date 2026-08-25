"""Tests for the NSWWS API client (feed -> discovered issued snapshot)."""

import pytest
from aioresponses import aioresponses
from yarl import URL

from custom_components.metoffice_warnings.api import (
    NSWWSApiClient,
    NSWWSAuthError,
    NSWWSConnectionError,
)
from custom_components.metoffice_warnings.const import API_KEY_HEADER, FEED_PATH
from tests.nswws_helpers import (
    NSWWS_BASE_URL,
    feed_xml,
    feed_xml_without_related_link,
    issued_snapshot_url,
    register_nswws,
    register_nswws_feed_error,
)


@pytest.fixture
def client(hass):
    return NSWWSApiClient(hass, base_url=NSWWS_BASE_URL, api_key="test-key")


async def test_get_active_warnings_success(client, issued_active) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_active)
        warnings = await client.async_get_active_warnings()

    assert len(warnings) == 2
    assert warnings[0].level == "amber"


async def test_get_active_warnings_empty(client, issued_empty) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        warnings = await client.async_get_active_warnings()

    assert warnings == []


async def test_sends_api_key_header_on_both_requests(client, issued_empty) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        await client.async_get_active_warnings()

        feed_request = mocked.requests[("GET", URL(client._url(FEED_PATH)))][0]
        assert feed_request.kwargs["headers"][API_KEY_HEADER] == "test-key"

        snapshot_request = mocked.requests[("GET", URL(issued_snapshot_url()))][0]
        assert snapshot_request.kwargs["headers"][API_KEY_HEADER] == "test-key"


async def test_auth_error_on_feed_raises(client) -> None:
    with aioresponses() as mocked:
        register_nswws_feed_error(mocked, status=401)
        with pytest.raises(NSWWSAuthError):
            await client.async_get_active_warnings()


async def test_auth_error_on_issued_snapshot_raises(client) -> None:
    with aioresponses() as mocked:
        mocked.get(
            f"{NSWWS_BASE_URL}{FEED_PATH}",
            body=feed_xml(),
            content_type="application/atom+xml",
            status=200,
        )
        mocked.get(issued_snapshot_url(), status=403)
        with pytest.raises(NSWWSAuthError):
            await client.async_get_active_warnings()


async def test_connection_error_raises(client) -> None:
    with aioresponses() as mocked:
        mocked.get(f"{NSWWS_BASE_URL}{FEED_PATH}", exception=TimeoutError())
        with pytest.raises(NSWWSConnectionError):
            await client.async_get_active_warnings()


async def test_server_error_raises_connection_error(client) -> None:
    with aioresponses() as mocked:
        register_nswws_feed_error(mocked, status=500)
        with pytest.raises(NSWWSConnectionError):
            await client.async_get_active_warnings()


async def test_missing_related_link_raises_connection_error(client) -> None:
    with aioresponses() as mocked:
        mocked.get(
            f"{NSWWS_BASE_URL}{FEED_PATH}",
            body=feed_xml_without_related_link(),
            content_type="application/atom+xml",
            status=200,
        )
        with pytest.raises(NSWWSConnectionError):
            await client.async_get_active_warnings()


async def test_malformed_feed_xml_raises_connection_error(client) -> None:
    with aioresponses() as mocked:
        mocked.get(
            f"{NSWWS_BASE_URL}{FEED_PATH}",
            body="not xml <<<",
            content_type="application/atom+xml",
            status=200,
        )
        with pytest.raises(NSWWSConnectionError):
            await client.async_get_active_warnings()


async def test_malformed_issued_json_raises_connection_error(client) -> None:
    with aioresponses() as mocked:
        mocked.get(
            f"{NSWWS_BASE_URL}{FEED_PATH}",
            body=feed_xml(),
            content_type="application/atom+xml",
            status=200,
        )
        mocked.get(issued_snapshot_url(), body="not json", status=200)
        with pytest.raises(NSWWSConnectionError):
            await client.async_get_active_warnings()
