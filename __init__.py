# custom_components/nature_remo_e/__init__.py
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import NatureRemoEApi
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import RemoEDataCoordinator

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    access_token: str = entry.data[CONF_ACCESS_TOKEN]
    device_id: str = entry.data[CONF_DEVICE_ID]
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL)

    api = NatureRemoEApi(hass, access_token)
    coordinator = RemoEDataCoordinator(
        hass, api, device_id, update_interval_seconds=update_interval
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "device_id": device_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        manufacturer="Nature",
        name=f"Nature Remo E {device_id}",
        model="Remo E",
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
