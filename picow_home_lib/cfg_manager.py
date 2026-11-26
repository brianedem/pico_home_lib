import asyncio
import logging
import os

from picow_home_lib import cmd_processor, configparser

log = logging.getLogger(__name__)

config_file = None
config = configparser.ConfigParser()
config_version = 1      # incremented with every change to in memory config data
config_modified = False # set when in memory config data has changed, cleared when written back to file

_waiting_tasks = []     # list of events waiting on a config update

# lock for accessing _waiting_tasks and _wait_version
_waitlist_lock = asyncio.Lock()

# called by tasks waiting for a configuration change
async def notify_on_change(version, event):
    if config_version > version:    # config may have been updated between then and now
        return
    event = asyncio.Event()         # if not, create an event to wait on
    async with _waitlist_lock:      # add the event to the list of waiting tasks
        _waiting_tasks.append(event)
    await event.wait()              # wait to be signaled before returning

# release waiting tasks
async def _notify():
    async with _waitlist_lock:
        event = _waiting_tasks.pop()
        event.set()

def read_config(name):
    global config_file
    config_file = name
    try:
        cf = open(config_file, 'r')
    except OSError:
        log.error(f'Config file {config_file} could not be found')
    else:
        try:
            config.read_file(cf)
        except ValueError:
            log.warning(f'Config file {config_file} format error')
        cf.close()

# routines for command processor commands
async def _set(*args):
    section, option, value = args
    response = ''
    if config.has_section(section):
        config.set(section, option, value)
        _notify()
    else:
        response = f'Unknown section {section}'
    return response

def show():
    return config.dump()

def save():
    temp_file = 'config_tmp.ini'
    try:
        with open(temp_file, 'w') as cfd:
            config.write(cfd)
    except:
        return f"Save failed - unable to create {temp_file}"
    try:
        os.rename(temp_file, config_file)
    except:
        return f"save failed - unable to replace {config_file} with temporary file"
    return "OK"

def _delete(*args):
    section, option = args
    response = ''
    if config.has_section(section):
        config.remove_option(section, option)
    else:
        response =  f'Unknown section {section}'
    return response

def _section(*args):
    action, section = args
    response = ''
    if action=='add':
        if config.has_section(section):
            response = f'Section {section} already exists'
        else:
            config.add_section(section)
    else:   # action=='remove'
        if config.has_section(section):
            config.remove_section(section)
        else:
            response = f'Section {section} does not exist'
    return response

cmd_list = (
    (r'config show', show,
        'config show                    show the current configuration'),
    (r'config save', save,
        'config save                    save the current configuration to disk'),
    (r'config del (\w+) (\w+)',_delete,
        'config del <section> <option>  remove option from the configuration'),
    (r'config set (\w+) (\w+) (\w+)',_set,
        'config set <section> <option> <value>     set the option value'),
    (r'config section (add|remove) (\w+)', _section,
        'config section add|remove <section>       add or remove a section'),
    )

cmd_processor.reg_cmds(None, cmd_list)
