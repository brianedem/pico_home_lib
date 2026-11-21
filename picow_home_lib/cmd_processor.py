import re

# each subsystem will supply a possible class reference and a list of commands
# each item in the list is a tuple of three items:
# - re match pattern
# - a routine that performs the command
# - help text
# if the class reference is not None then the routine is assumed to be bound and
# will be passed the class reference

# [subsystem, pattern, function, help]
cmd_list = []

def reg_cmds(subsystem, commands):
    for p,f,h in commands:
        cmd_list.append((subsystem, p, f, h))

def process(command, get_history):
    response = ''
    if command.startswith('hist'):
        for n,h in get_history():
            response += f'{n}  {h}\n'

        return response

    for s,p,f,_ in cmd_list:
        m = re.match(p, command)
        if m is None:
            continue
        if s is None:
            return f(*m.groups())
        else:
            return f(s, *m.groups())
    if command.startswith('help'):
        response += 'help                           describe available commands\n'
        response += 'history                        list of previous commands\n'
        for _,_,_,h in cmd_list:
            response += h + '\n'

        return response

    return 'unknown command\n'

