import logging
import os

from picow_home_lib import cmd_processor
from picow_home_lib import configparser

log = logging.getLogger(__name__)

class config_manager():
    def __init__(self, config_file):
        cmd_processor.reg_cmds(self, self.cmd_list)
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        try:
            cf = open(config_file, 'r')
        except OSError:
            log.error(f'Config file {config_file} could not be found')
        else:
            try:
                self.config.read_file(cf)
            except ValueError:
                log.warning(f'Config file {config_file} format error')
            cf.close()

    def _set(self, *args):
        section, option, value = args
        if self.config.has_section(section):
            self.config.set(section, option, value)
        else:
            return f'Unknown section {section}'
        return ""

    def show(self):
        return self.config.dump()

    def save(self):
        temp_file = 'config_tmp.ini'
        try:
            with open(temp_file, 'w') as cfd:
                self.config.write(cfd)
        except:
            return "save failed - unable to create temporary file"
        try:
            os.rename(temp_file, self.config_file)
        except:
            return f"save failed - unable to replace {self.config_file} with temporary file"
        return "OK"

    def _delete(self, *args):
        section, option = args
        if self.config.has_section(section):
            self.config.remove_option(section, option)
        else:
            return f'Unknown section {section}'

    def _section(self, *args):
        if len(args) != 2:
            return 'incorrect number of parameters'
        action, section = args
        if action=='add':
            if self.config.has_section(section):
                return f'Section {section} already exists'
            else:
                self.config.add_section(section)
        else:   # action=='remove'
            if self.config.has_section(section):
                self.config.remove_section(section)
            else:
                return f'Section {section} does not exist'

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
