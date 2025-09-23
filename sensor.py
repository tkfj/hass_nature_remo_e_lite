# custom_components/nature_remo_e/sensor.py
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfPower, UnitOfEnergy

from .const import DOMAIN
from .coordinator import RemoEDataCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: RemoEDataCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    async_add_entities(
        [
            RemoECurrentPowerSensor(coordinator, device_id),
            RemoECumulativeEnergySensor(coordinator, device_id),
        ],
        update_before_add=True,
    )

class _BaseRemoESensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: RemoEDataCoordinator, device_id: str) -> None:
        self._coordinator = coordinator
        self._device_id = device_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"Nature Remo E {self._device_id}",
            manufacturer="Nature",
            model="Remo E",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

class RemoECurrentPowerSensor(_BaseRemoESensor):
    _attr_name = "Current Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._device_id}_current_power"

    @property
    def native_value(self) -> float | None:
        data = self._coordinator.data or {}
        return data.get("power_w")

class RemoECumulativeEnergySensor(_BaseRemoESensor):
    _attr_name = "Cumulative Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._device_id}_cumulative_energy"

    @property
    def native_value(self) -> float | None:
        data = self._coordinator.data or {}
        return data.get("energy_kwh")
