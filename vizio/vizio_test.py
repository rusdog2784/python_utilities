"""
Pyvizio documentation: https://github.com/raman325/pyvizio

Example commands:
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> get-current-app
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> get-current-input
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press --help
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> launch-app "YouTube TV" && sleep 10 && pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press PRESS
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press KEYPRESS
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press OK
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press RIGHT
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press DOWN
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press DOWN
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press DOWN
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> key-press OK
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> channel down
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> get-all-settings
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> get-all-settings-options
    pyvizio --ip=10.69.69.15:7345 --device_type=tv --auth <Vizio Authorization Token> get-all-settings-options
"""
from pyvizio import Vizio

class Settings:
    VOLUME = 15
    SOURCE = "WatchFree+"


# Received this token after running the following CLI commands:
# 	pyvizio --ip=10.69.69.15:7345 --device_type=tv pair
# 	pyvizio --ip=10.69.69.15:7345 --device_type=tv pair-finish --token=<Vizio Authorization Token> --pin=7364 --ch_type=1
AUTHORIZATION_TOKEN = "<Vizio Authorization Token>"

tv = Vizio(
    device_id="<Your Vizio Device ID>",
    name="<Your Vizio Device Name>",
    ip="10.69.69.15:7345",
    device_type="tv",
    auth_token=AUTHORIZATION_TOKEN
)


def workflow1():
    # Turn on TV, if it's off
    if tv.get_power_state() == 'off':
        print(f"Turning on {tv.name}...")
        tv.pow_on()
    else:
        print(f"{tv.name} is already on")

    # Set volume
    current_volume = tv.get_current_volume()
    if current_volume > Settings.VOLUME:
        print(f"Volume is set to {current_volume}. Turning it down to {Settings.VOLUME}...")
        volume_diff = current_volume - Settings.VOLUME
        tv.vol_down(volume_diff)
    elif current_volume < Settings.VOLUME:
        print(f"Volume is set to {current_volume}. Turning it up to {Settings.VOLUME}...")
        volume_diff = Settings.VOLUME - current_volume
        tv.vol_up(volume_diff)
    else:
        print(f"Volume is already set to {Settings.VOLUME}")

    # Set source
    current_app = tv.get_current_app()
    if current_app != Settings.SOURCE:
        print(f"Setting source to {Settings.SOURCE}...")
        tv.launch_app(Settings.SOURCE)
    else:
        print(f"Source is already set to {Settings.SOURCE}")

tv.remote("OK")


raise Exception("This is an exception " \
                "with multiple lines to it")
