from multiprocessing import Pool
from requests import request

import os
import json
import time

from subprocess import call

DEFAULT_CONFIG = {
    'sleep': 0.25,
    'name': 'myName',
    'nginx_file': None,
    'counts': {
        'to_down': 1,
        'to_up': 3
    },
    'targets': []
}

def watch(target):
    '''
    method reposable for watch target
    '''
    result = True

    try:
        res = request(**target.get('request'))
        result = res.status_code == target.get('status')
    except Exception:
        result = False

    return [target.get('host'), result]

__version__ = '0.0.6'

class __App():
    '''
    wrapper of application
    '''

    def __init__(self):
        self._older_online_targets = set()

    @property
    def config(self):
        '''
        interface for access configurations
        '''
        return self._config or DEFAULT_CONFIG

    @property
    def is_verbose(self):
        '''
        property responsible for verifying that we are in verbose mode
        '''
        return self.config.get('verbose', True)

    @property
    def refresh_command(self):
        '''
        property responsible for verifying that we are in verbose mode
        '''
        return self.config.get('refresh_command', ['true'])

    def apply_result(self, targets):
        '''
        method responsible for carrying out the results of the observations
        '''
        name = self.config.get('name')
        nginx_file = self.config.get('nginx_file')
        
        online_targets = { target[0] for target in targets if target[1] }
        offline_targets = { target[0] for target in targets if not target[1] }

        if self._older_online_targets != online_targets:
            print('!', end='', flush=True)
        
            with open(nginx_file, 'wt') as fd:
                fd.write(f'upstream UPS_{name.upper()} {{\n')
                for target in online_targets:
                    fd.write(f'  server {target};\n')
                for target in offline_targets:
                    fd.write(f'  # server {target};\n')
                fd.write(f'}}')

                print('call command', self.config.get('refresh_command', 'test'))
                call(self.refresh_command, shell=False)
        
            self._older_online_targets = { target for target in online_targets }
        elif self.is_verbose:
            print('*', end='', flush=True)

    def run(self):
        '''
        runner method responsible for start and observe targets
        '''
        targets = self.config.get('targets')
        sleep_interval = self.config.get('sleep')

        while True:
            self.is_verbose and print('.', end='', flush=True)
            pool = Pool()
            pool.map_async(
                watch, 
                targets, 
                callback=self.apply_result
            )

            time.sleep(sleep_interval)


def create_app():
    '''
    application creator method 
    '''
    return __App()


def init_config(app):
    '''
    factory with load configuration
    '''
    if not os.path.exists('conf.json'):
        with open('conf.json', 'wt') as fd:
            json.dump(DEFAULT_CONFIG, fd, indent=2)

    with open('conf.json', 'rt') as fd:
        app._config = json.load(fd)


def main():
    '''
    initialization method called by python to start sentinel
    '''
    app = create_app()
    init_config(app)

    app.run()
