import asyncio
import logging

import network  # type:ignore

from picow_home_lib import cfg_manager, cmd_processor, configparser

log = logging.getLogger(__name__)

wlan = None
ssid = None
network_up = asyncio.Event()

async def wifi_manager():
    global wlan, ssid
    cmd_processor.reg_cmds(None, cmd_list)
    network.hostname(cfg_manager.config.get('SYSTEM', 'hostname', fallback='home_lib_default'))

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    ssid = None

    # if interface is connecting or up we need to disconnect first
    while wlan.status() > network.STAT_IDLE:
        log.info('wlan startup - interface is busy - disconnecting')
        wlan.disconnect()
        await asyncio.sleep(1)
        if wlan.status() > network.STAT_IDLE:
            log.info('wlan startup - interface still busy - disconnecting')
            wlan.connect('','')
            await asyncio.sleep(1)

    log.debug(f'wifi status = {wlan.status()}')

    while True:

        # from the configuration get the list of APs that we have passwords for
        version = cfg_manager.config_version
        try:
            known_access_points = cfg_manager.config.options('WIFI')
        except configparser.NoSectionError:
            known_access_points = []
        if len(known_access_points) == 0:
            await cfg_manager.notify_on_change(version)
            continue

        # in the list of available APs are there any that we know about
        for ssid in scan_ap(info=False):
            try:
                password = known_access_points[ssid]
                break
            except KeyError:
                pass
        else:
            log.debug('no suitable AP found')
            await asyncio.sleep(10)
            continue

        log.info(f'selected {ssid} for AP')

        # connect to the selected AP
        wlan.connect(ssid, password)

        # monitor wifi connection status
        NOT_CONNECTED = 0
        CONNECTING = 1
        CONNECTED = 2
        cs = NOT_CONNECTED
        while True:
            status = wlan.status()
            if   cs is NOT_CONNECTED:
                if status == network.STAT_GOT_IP:
                    network_up.set()
                    log.info('wifi connected')
                    cs = CONNECTED
                elif status < network.STAT_IDLE:
                    log.info('wifi connect failed')
                    break
                else:
                    log.info('wifi connecting')
                    cs = CONNECTING
            elif cs is CONNECTING:
                if status == network.STAT_GOT_IP:
                    network_up.set()
                    log.info('wifi connected')
                    cs = CONNECTED
                elif status < network.STAT_IDLE:
                    log.info('wifi connect failed')
                    break
            elif cs is CONNECTED:
                if status < network.STAT_IDLE:
                    network_up.clear()
                    log.info('AP disconnected')
                    break
                elif status < network.STAT_GOT_IP:
                    network_up.clear()
                    log.info('wifi reconnecting')
                    cs = CONNECTING
        await asyncio.sleep(1)


# generate a list of APs sorted by rssi
def scan_ap(info=True, *args):
    ap_list = wlan.scan()
    # eliminate unnamed APs and weaker duplicates
    ap_rssi = {}
    for ap in ap_list:
        ssid = ap[0].decode()
        rssi = ap[3]
        if ssid in ap_rssi:
            ap_rssi[ssid] = max(ap_rssi[ssid], rssi)
        elif ssid != '':
            ap_rssi[ssid] = rssi

    # sort by AP signal strength and find the strongest AP in our list
    ap_sorted = sorted(ap_rssi, key=ap_rssi.get, reverse=True)
    if info:
        result = []
        for ap in ap_sorted:
            result.append(f'{ap_rssi[ap]:4} {ap}')
        return '\n'.join(result)
    else:
        return ap_sorted

def status(*args):
    if ssid is None:
        return 'use "config set wifi.<ssid> <password>" to set up WIFI'
    status = wlan.status()
    if status == network.STAT_IDLE:
        return 'no wifi connection attempt has been made'
    if status == network.STAT_WRONG_PASSWORD:
        return f'password for {ssid} incorrect'
    if status == network.STAT_NO_AP_FOUND:
        return 'AP is no longer responding'
    if status == network.STAT_CONNECT_FAIL:
        return f'connection to {ssid} failed'
    if network.STAT_IDLE < status < network.STAT_GOT_IP:
        return f'connecting to {ssid}'
    if status != network.STAT_GOT_IP:
        return f'unexpected wifi {status}'
    else:
        rssi = wlan.status('rssi')
        addr4,_ = wlan.ipconfig('addr4')
        mac = wlan.config('mac')
        amac = []
        for b in mac:
            amac.append(f'{b:02x}')
        mac = ':'.join(amac)
        return f'wifi connected to {ssid}\n rssi: {rssi}\n ip:   {addr4}\n mac:  {mac}'

def help(*args):
    response = []
    response.append('Available commands:')
    response.append(' wifi status - reports current wifi status')
    response.append(' wifi scan - report available wifi access points and the signal strengths')
    response.append('Use "config set wifi.<ssid> <password> to set up wifi access')
    response.append('Use "config set hostname" to specify the device network name')
    return '\n'.join(response)
cmd_list = (
    (r'wifi status', status,
        'wifi status                report current wifi status'),
    (r'wifi scan', scan_ap,
        'wifi scan                  list available wifi access points and their signal strength'),
    (r'wifi help', help,
        'wifi help                  wifi subsystem information'),
)
