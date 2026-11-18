# This is a minimal implemention of the configparser library
# for use in a MicroPython application.

# The .ini file is organized into sections, each containing zero or more objects.
# A new section is introduced with a line continaing the section name inclosed in
# square brackets ([]).
# An object consists of a line containing an object name, an '=', and a value.
# The value is treated as a string and may be quoted or unquoted with double quotes (").
# Comments, introduced with a '#' or ';', are allowed on otherwise empty lines, and may be indented
# 
# The .ini file is parsed into a dictonary indexed by section name. Each section entry contains
# a dictonary indexed by object name and contains the object value.
# 
# Implementation Notes:
# 
# Reading the .ini file
# When a .ini file is read, an outline of the file contents is created. The outline preserves the
# order of the entries, comments, and any blank or ill-formed lines.
# This implementation only supports reading a single configuration file

# Writing the .ini file
# When a .ini file is displayed or written, the outline is used to generate the output.
# New sections will be located after the last existing section
# New options will be added to the end of the section
# A shadow values object is used to identify new sections and objects. As objects are output,
# they are removed from the shadow.
# At the end of the section any remaining objects in the shadow section are new.
# At the end of processing the outline, any remaining shadow sections are new and will be added
# to the output.

import io
import platform
import re

_SECTION = 0
_OPTION = 1
_COMMENT = 2

if 'MicroPython' in platform.platform():
    import mlogging as logging
else:
    import logging

log = logging.getLogger(__name__)

class NoSectionError(Exception):
    def __init__(self, section, details=None):
        super().__init__(f"No section: '{section}'")

class DuplicateSectionError(Exception):
    def __init__(self, section, details=None):
        super().__init__(f"Section '{section}' already exists")

class DuplicateOptionError(Exception):
    def __init__(self, section, option, details=None):
        super().__init__(f"Option '{option}' in section '{section}' already exists")

class NoOptionError(Exception):
    def __init__(self, option, section):
        super().__init__(f"No option {option!r} in section: {section!r}")

class MissingSectionHeaderError(Exception):
    def __init__(self, filename, lineno, line, details=None):
        super().__init__(f"File contains no section headers.\nfile: '{filename}', line {lineno}\n'{line}'")

class ParsingError(Exception):
    def __init__(self, source, details=None):
        super().__init__(f"Source contains parsing errors: '{source}'")

class ConfigParser():
    def __init__ (self):
        self._sections = {}
        self._proxies = {}          # used to access section options using dunders
        self.modified = False       # indicate in console prompt when this is set
        self.outline = []           # template used when updating configuration file

    def sections(self):
        return list(self._sections.keys())

    def add_section(self, section):
        if type(section) is not str:
            raise TypeError("section names must be strings")
        if section in self._sections:
            raise DuplicateSectionError(section)
        self._sections[section] = {}
        self._proxies[section] = SectionProxy(self, section)
        self.modified = True

    def has_section(self, section):
        return section in self._sections

    def options(self, section):
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise NoSectionError(section) from None
        return list(opts.keys())
                
    def read_file(self, f, source=None):
        # section pattern
        sp = re.compile(r'\[(\w+)\]')
        # object pattern
        op = re.compile(r'([0-9a-zA-Z_.]+)\s*=\s*(.*)')
        # comment pattern
        cp = re.compile(r'[#;]')

        if source is None:
            try:
                source = f.name
            except AttributeError:
                source = '<???>'

        section = None
        missing_section_header_flagged = False

        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if m := sp.match(line):     # section match
                section = m.group(1)
                self.add_section(section)
                self.outline.append((_SECTION,section))

            elif m := op.match(line):   # unquoted option value assignment
                if section is None:
                    raise MissingSectionHeaderError(source, line_no, line)
                option, value = m.groups()
                if option in self._sections[section]:
                    raise DuplicateOptionError(section, option)

                self.set(section, option, value)
                self.outline.append((_OPTION,option))

            elif m := cp.match(line):   # comment
                self.outline.append((_COMMENT,line))

            elif line == '':            # blank line
                self.outline.append((_COMMENT,''))

            else:
                raise ParsingError(source)

    def get(self, section, option, fallback=None):
        try:
            d = self._sections[section]
        except NoSectionError:
            if fallback:
                return fallback
            else:
                raise
        option = self.optionxform(option)
        try:
            value = d[option]
        except KeyError:
            if fallback is None:
                raise NoOptionError(option, section)
            return fallback
        return value

    def getint(self, section, option, fallback=None):
        try:
            return int(self.get(section, option))
        except (NoSectionError, NoOptionError):
            if fallback is None:
                raise
            return fallback

    def optionxform(self, optionstr):
        return optionstr.lower()

    def has_option(self, section, option):
        if section not in self._sections:
            return False
        else:
            option = self.optionxform(option)
            return option in self._sections[section]

    def set(self, section, option, value):
        if type(value) is not str:
            raise TypeError("option values must be strings")
        try:
            sectdict = self._sections[section]
        except KeyError:
            raise NoSectionError(section) from None
        sectdict[self.optionxform(option)] = value
        self.modified = True
            
    def dump(self):                 # TODO needs to move to parent file that augments this library
        buffer = io.StringIO('')
        self.write(buffer)
        output = buffer.getvalue()
        buffer.close()
        return return output

    def write(self, fd, space_around_delimiters=True, with_comments=False):
        if space_around_delimiters:
            d = ' = '
        else:
            d = '='

        response = ""

        # original output, suitable for dumping to console
        if not with_comments:
            for section in self._sections:
                options = self._sections[section]
                fd.write(f'[{section}]\n')
                for option,value in options.items():
                    fd.write(f'{option}{d}{value}\n')

        # enhanced output using outline collected while reading source configuration file
        # TODO this needs to be moved to a parent file that augments this library
        else:
            shadow_values = self._sections.copy()
            section = None
            options = {}

            # output sections, options, and comments based on the outline
            for line_type,line_value in self.outline:
#               print(line_type, line_value)
                if line_type is _SECTION:
                    # before starting the next section emit any remaining options
                    # from previous section
                    for option, value in options.items():
                        fd.write(f'{option}{d}{value}\n')
                            
                    # set up for the next section
                    if line_value in self._sections:
                        section = line_value
                        options = shadow_values.pop(section, {})
                        fd.write(f'[{section}]\n')
                    else:
                        section = None  # section was deleted
                        options = {}
                elif line_type is _OPTION:
                    option = line_value
                    value = options.pop(option, None)
                    if value is None:
                        pass            # option was deleted
                    else:
                        fd.write(f'{option}{d}{value}\n')
                else:
                    comment = line_value
                    fd.write(f'{comment}\n')   # add the comment

            # end of the outline - see if the last section has any more options
            for option, value in options:
                fd.write(f'{option}{d}{value}\n')

            # any remaining non-empty sections in shadow values are new and need to be output
            for section,options in shadow_values.items():
                fd.write(f'[{section}]\n')
                for option,value in options.items():
                    fd.write(f'{option}{d}{value}\n')

    def remove_option(self, section, option):
        try:
            sectdict = self._sections[section]
        except KeyError:
            raise NoSectionError(section) from None
        option = self.optionxform(option)
        existed = option in sectdict
        if existed:
            del sectdict[option]
            self.modified = True
        return existed
            
    def remove_section(self, section):
        existed = section in self._sections
        if existed:
            del self._sections[section]
            del self._proxies[section]
            self.modified = True
        return existed

    def __getitem__(self, key):
        if not self.has_section(key):
            raise KeyError(key)
        return(self._proxies[key])

#   def __setitem__() would be used to circumvate the normal methods to create/overwrite a section

class SectionProxy():
    def __init__(self, parser, name):
        self._parser = parser
        self._name = name

    def __getitem__(self, key):
        if not self._parser.has_option(self._name, key):
            raise KeyError(key)
        return self._parser.get(self._name, key)

    def __setitem__(self, key, value):
        return self._parser.set(self._name, key, value)

if __name__ == '__main__':
    c = ConfigParser()
    print(f'{c.dump()}')
    cfd = open('sample.ini', 'r')
    c.read_file(cfd)
    print(c.dump())

    print(f'{c["NTFY"]["Topic"]}')

#   c['NEW'] = {}           # unsupported
    c.add_section('NEW')
    c['NEW']['x'] = '5'
    print(f'{c.dump()}')

    print(c._sections.keys())
    print(f'{c.has_section('WIFI')=}')
    print(f'{c.has_section('foo')=}')
    print(f'{c.options('WIFI')=}')
    try:
        print(f'{c.options('foo')=}')
    except NoSectionError:
        print("Attempt to read options from 'foo' failed as expected")
    print(f'{c.has_option('NTFY','Topic')=}')
    print(f'{c.has_option('foo','Topic')=}')
    print(f'{c.has_option('NTFY','foo')=}')
    print(f'{c.get('NTFY','Topic')=}')
    try:
        print(f'{c.get('foo','Topic')=}')
    except KeyError:
        print("Attempt to read option 'Topic' from section 'foo' failed as expected")
    try:
        print(f'{c.get('NTFY','foo')=}')
    except NoOptionError:
        print("failed as expected")
    print(f'{c.getint('NEW','x')=}')
    try:
        x = c.getint('NTFY','Topic')
        print("ValueError for getint('NTFY','Topic') not detected")
    except ValueError:
        pass
    c.set('NEW','y','5')
    try:
        c.set('NEW','z',7)
        print("ValueError for set('NEW','z',7) not detected")
    except TypeError:
        pass
