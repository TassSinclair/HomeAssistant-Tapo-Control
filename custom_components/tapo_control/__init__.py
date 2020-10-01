from homeassistant.helpers import entity
from pytapo import Tapo
from homeassistant.const import (CONF_HOST, CONF_USERNAME, CONF_PASSWORD)
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
DOMAIN = "tapo_control"
PRESET = "preset"
DISTANCE = "distance"
TILT = "tilt"
PAN = "pan"
ENTITY_ID = "entity_id"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Required(CONF_USERNAME): cv.string,
                        vol.Required(CONF_PASSWORD): cv.string
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

tapo = {}

def setup(hass, config):
    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    for camera in config[DOMAIN]:
        host = camera[CONF_HOST]
        username = camera[CONF_USERNAME]
        password = camera[CONF_PASSWORD]

        tapoConnector = Tapo(host, username, password)
        basicInfo = tapoConnector.getBasicInfo()

        entity_id = DOMAIN+"."+basicInfo['device_info']['basic_info']['device_alias'].replace(".","_").replace(" ", "_").lower()
        if(entity_id in tapo):
            # if two entities have the same name, add ip to the next one
            entity_id = entity_id+"_"+host.replace(".","_")

        tapo[entity_id] = tapoConnector
        hass.states.set(entity_id, "monitoring", basicInfo['device_info']['basic_info']) # todo: better state

    def handle_ptz(call):
        if ENTITY_ID in call.data:
            entity_id = call.data.get(ENTITY_ID)
            if PRESET in call.data:
                preset = call.data.get(PRESET)
                tapo[entity_id].setPreset(preset)
            elif TILT in call.data:
                tilt = call.data.get(TILT)
                if DISTANCE in call.data:
                    distance = float(call.data.get(DISTANCE))
                    if(distance >= 0 and distance <= 1):
                        degrees = 68 * distance
                    else:
                        degrees = 5
                else:
                    degrees = 5
                if tilt == "UP":
                    tapo[entity_id].moveMotor(0,degrees)
                elif tilt == "DOWN":
                    tapo[entity_id].moveMotor(0,-degrees)
                else:
                    _LOGGER.error("Incorrect tilt value. Possible values: UP, DOWN")
            elif PAN in call.data:
                pan = call.data.get(PAN)
                if DISTANCE in call.data:
                    distance = float(call.data.get(DISTANCE))
                    if(distance >= 0 and distance <= 1):
                        degrees = 360 * distance
                    else:
                        degrees = 5
                else:
                    degrees = 5
                if pan == "RIGHT":
                    tapo[entity_id].moveMotor(degrees,0)
                elif pan == "LEFT":
                    tapo[entity_id].moveMotor(-degrees,0)
                else:
                    _LOGGER.error("Incorrect pan value. Possible values: RIGHT, LEFT")
            else:
                _LOGGER.error("Incorrect additional PTZ properties. You need to specify at least one of " + TILT + ", " + PAN + ", " + PRESET + ".")
        else:
            _LOGGER.error("Incorrect entity_id value.")

    hass.services.register(DOMAIN, "ptz", handle_ptz)
    
    return True