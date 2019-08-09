from importlib import reload
import os
import InstaClonerService

import readline # optional, will allow Up/Down/History in the console
import code
variables = globals().copy()
variables.update(locals())
shell = code.InteractiveConsole(variables)
shell.interact()

# while True:
#     try:
#         cmd = input('$ ')
#         if cmd[:4] == 'quit':
#             os._exit(0)
#         elif cmd[:6] == 'reload':
#             reload(InstaClonerService)
#         else:
#             print("Function Not Found")
#     except Exception as e:
#         print(e)