# custom_components/nature_remo_e/api.py
from __future__ import annotations

from typing import Any
from aiohttp import ClientResponseError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

API_BASE = "https://api.nature.global/1/appliances"

class NatureRemoEApiError(Exception):
    pass

class NatureRemoEApi:
    """Nature Remo E API client (async)."""

    def __init__(self, hass, access_token: str) -> None:
        self._hass = hass
        self._token = access_token
        self._session = async_get_clientsession(hass)

    async def async_validate(self) -> dict[str, Any]:
        """Call a lightweight endpoint to validate token (here: same list, but we don't parse)."""
        try:
            async with self._session.get(
                API_BASE,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if not isinstance(data, list):
                    raise NatureRemoEApiError("Unexpected response format.")
                return {"ok": True, "count": len(data)}
        except ClientResponseError as e:
            raise NatureRemoEApiError(f"HTTP {e.status}: {e.message}") from e
        except Exception as e:
            raise NatureRemoEApiError(str(e)) from e

    async def async_fetch_meter_raw(self) -> list[dict[str, Any]]:
        """Fetch full appliance list JSON."""
        try:
            async with self._session.get(
                API_BASE,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as e:
            raise NatureRemoEApiError(f"HTTP {e.status}: {e.message}") from e
        except Exception as e:
            raise NatureRemoEApiError(str(e)) from e

    @staticmethod
    def _find_prop(props: list[dict[str, Any]], epc: int):
        return next((p.get("val") for p in props if p.get("epc") == epc), None)

    async def async_get_power_and_energy(self, device_id: str) -> dict[str, float | None]:
        """
        Returns:
          {
            "power_w": float | None,
            "energy_kwh": float | None
          }
        """
        data = await self.async_fetch_meter_raw()
        for appliance in data:
            if appliance.get("type") == "EL_SMART_METER":
                props = appliance.get("smart_meter", {}).get("echonetlite_properties", [])
                if not isinstance(props, list):
                    continue

                # EPC mapping (your script logic)
                watt = self._find_prop(props, 231)  # instantaneous power (W)
                val_224 = self._find_prop(props, 224)  # cumulative value (raw)
                coef = self._find_prop(props, 211)     # coefficient
                unit_code = self._find_prop(props, 225)  # unit code

                power_w: float | None = float(watt) if watt is not None else None

                energy_kwh: float | None = None
                if val_224 is not None:
                    try:
                        coef_i = int(coef) if coef is not None else 1
                        unit_i = int(unit_code) if unit_code is not None else 0
                        # same table as your script
                        unit_table = {0: 1000, 1: 100, 2: 10, 3: 1, 4: 0.1, 5: 0.01}
                        multiplier = unit_table.get(unit_i, 1000)
                        energy_wh = int(val_224) * coef_i * multiplier
                        energy_kwh = float(energy_wh) / 1000.0
                    except Exception as e:
                        # keep None on parse error
                        raise NatureRemoEApiError(f"Energy parse failed: {e}") from e

                return {"power_w": power_w, "energy_kwh": energy_kwh}

        # smart meter not found
        return {"power_w": None, "energy_kwh": None}
