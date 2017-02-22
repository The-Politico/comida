#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from fabric.api import local, lcd, prefix, task, execute
from contextlib import contextmanager as _contextmanager
import shutil
import os
import glob
import logging
import zipfile

"""
Logging
"""
LOG_FORMAT = '%(levelname)s:%(name)s:%(asctime)s: %(message)s'
LOG_LEVEL = logging.INFO

# GLOBAL SETTINGS
cwd = os.path.dirname(__file__)
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


@_contextmanager
def lvirtualenv(name):
    INPUT_PATH = os.path.join(cwd, name)
    with lcd(INPUT_PATH):
        with prefix('source venv/bin/activate'):
            yield


def _add_code_to_zip(name, mode='w'):
    """
    Adds code files to the deployment package
    """
    EXCLUDE_EXTENSIONS = ['.pyc']
    INPUT_PATH = os.path.join(cwd, name)
    OUTPUT_PATH = os.path.join(cwd, 'zip')
    with zipfile.ZipFile('%s/%s.zip' % (OUTPUT_PATH, name), mode) as z:
        for file in glob.glob('%s/*.*' % INPUT_PATH):
            fname = os.path.basename(file)
            if os.path.splitext(fname)[1].lower() in EXCLUDE_EXTENSIONS:
                continue
            z.write(file, fname)


@task
def generateVirtualEnvironment(name):
    """
    Generate internal virtualenv so we can include dependencies
    """
    INPUT_PATH = os.path.join(cwd, name)
    with lcd(INPUT_PATH):
        command = 'virtualenv --no-site-packages venv'
        local(command)
    with lvirtualenv(name):
        local('pip install -r requirements.txt')


@task
def render(name):
    """
    Create lambda code deployment package
    - If the internal virtualenv has not been generated, do it!
    - Compress libraries
    - Add code files
    """
    BASE_PATH = os.path.join(cwd, name)
    OUTPUT_PATH = os.path.join(cwd, 'zip')
    # Create output files folder if needed
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    # If we have requirements create internal virtualenv and zip
    if os.path.exists('%s/requirements.txt' % BASE_PATH):
        lib_path = os.path.join(cwd,
                                '%s/venv/lib/python2.7/site-packages' % (name))
        if not os.path.exists(lib_path):
            execute('generateVirtualEnvironment', name)
        try:
            # First zip all the used libraries
            shutil.make_archive('%s/%s' % (OUTPUT_PATH, name), 'zip', lib_path)
            # Add code
            _add_code_to_zip(name, mode='a')
        except Exception, e:
            logger.error("Exit with uncaptured exception %s" % (e))
            raise

    else:
        _add_code_to_zip(name, mode='w')


@task
def deploy(name, function='comidaSlackCommandWorker'):
    execute('render', name)
    command = 'aws lambda update-function-code'
    command += ' --zip-file=fileb://zip/%s.zip' % (name)
    command += ' --function-name %s' % (function)
    logger.info('command: %s' % command)
    local(command)
