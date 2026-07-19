"""Test Traccar Server coordinator event handling."""

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from homeassistant.components.juzi_traccar_server.coordinator import (
    TraccarServerCoordinator,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_capture_events

from .common import setup_integration
from .conftest import mock_config_entry  # noqa: F401


async def test_import_geofence_event_has_geofence_id_and_name(
    hass: HomeAssistant,
    mock_traccar_api_client: Generator[AsyncMock],
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test geofence events include geofence_id and geofence_name."""

    # Configure to import geofence events
    mock_config_entry.options = {
        **mock_config_entry.options,
        "events": ["geofenceEnter"],
    }

    # Mock get_reports_events to return a geofenceEnter event
    mock_traccar_api_client.get_reports_events.return_value = [
        {
            "id": 1,
            "type": "geofenceEnter",
            "eventTime": "2026-07-19T02:18:06.000+00:00",
            "deviceId": 0,
            "positionId": 0,
            "geofenceId": 0,  # matches "Tatooine" in geofences.json
            "maintenanceId": 0,
            "attributes": {},
        }
    ]

    # Track fired events
    events = async_capture_events(hass, "traccar_geofence_enter")

    await setup_integration(hass, mock_config_entry)

    coordinator: TraccarServerCoordinator = mock_config_entry.runtime_data
    await coordinator.import_events(datetime(2026, 7, 19, 14, 0, 0))

    assert len(events) == 1
    event_data = events[0].data
    assert event_data["device_name"] == "X-Wing"
    assert event_data["type"] == "geofenceEnter"
    assert event_data["geofence_id"] == 0
    assert event_data["geofence_name"] == "Tatooine"


async def test_non_geofence_event_does_not_have_geofence_fields(
    hass: HomeAssistant,
    mock_traccar_api_client: Generator[AsyncMock],
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test non-geofence events do not include geofence_id and geofence_name."""

    mock_config_entry.options = {
        **mock_config_entry.options,
        "events": ["deviceMoving"],
    }

    mock_traccar_api_client.get_reports_events.return_value = [
        {
            "id": 2,
            "type": "deviceMoving",
            "eventTime": "2026-07-19T02:18:06.000+00:00",
            "deviceId": 0,
            "positionId": 0,
            "geofenceId": 0,
            "maintenanceId": 0,
            "attributes": {},
        }
    ]

    events = async_capture_events(hass, "traccar_device_moving")

    await setup_integration(hass, mock_config_entry)

    coordinator: TraccarServerCoordinator = mock_config_entry.runtime_data
    await coordinator.import_events(datetime(2026, 7, 19, 14, 0, 0))

    assert len(events) == 1
    event_data = events[0].data
    assert "geofence_id" not in event_data
    assert "geofence_name" not in event_data
