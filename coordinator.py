# custom_components/nature_remo_e/coordinator.py
from __future__ import annotations

from datetime import timedelta
from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NatureRemoEApi, NatureRemoEApiError
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class RemoEDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: NatureRemoEApi,
        device_id: str,
        update_interval_seconds: int | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(
                seconds=update_interval_seconds or DEFAULT_UPDATE_INTERVAL
            ),
        )
        self._api = api
        self._device_id = device_id

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            result = await self._api.async_get_power_and_energy(self._device_id)
            return {
                "power_w": result.get("power_w"),
                "energy_kwh": result.get("energy_kwh"),
            }
        except NatureRemoEApiError as exc:
            raise UpdateFailed(str(exc)) from exc
        except Exception as exc:
            raise UpdateFailed(repr(exc)) from exc
