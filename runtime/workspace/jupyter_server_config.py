import os

c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.port_retries = 0
c.ServerApp.root_dir = '/workspace'
c.ServerApp.open_browser = False
c.ServerApp.allow_remote_access = True
c.ServerApp.log_level = 'ERROR'
c.ServerApp.show_banner = False
c.IdentityProvider.token = os.environ['JUPYTER_TOKEN']
c.ServerApp.terminals_enabled = True

c.ServerApp.terminado_settings = {'shell_command': ['/bin/bash', '--noprofile', '--norc']}
