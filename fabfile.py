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
    INPUT_PATH = os.path.join(cwd, 'code')
    with lcd(INPUT_PATH):
        with prefix('source %s/bin/activate' % name):
            yield


def _add_code_to_zip(venvpath='venv'):
    """
    Adds code files to the deployment package
    """
    EXCLUDE_EXTENSIONS = ['.pyc']
    INPUT_PATH = os.path.join(cwd, 'code')
    OUTPUT_PATH = os.path.join(cwd, 'zip')
    with zipfile.ZipFile('%s/lambda.zip' % OUTPUT_PATH, 'a') as z:
        for file in glob.glob('%s/*.*' % INPUT_PATH):
            fname = os.path.basename(file)
            if os.path.splitext(fname)[1].lower() in EXCLUDE_EXTENSIONS:
                continue
            z.write(file, fname)


@task
def generateVirtualEnvironment(name='venv'):
    """
    Generate internal virtualenv so we can include dependencies
    """
    INPUT_PATH = os.path.join(cwd, 'code')
    with lcd(INPUT_PATH):
        command = 'virtualenv --no-site-packages %s' % name
        local(command)
    with lvirtualenv(name):
        local('pip install -r requirements.txt')


@task
def render():
    """
    Create lambda code deployment package
    - If the internal virtualenv has not been generated, do it!
    - Compress libraries
    - Add code files
    """
    # Libraries to include on the zip file
    lib_path = os.path.join(cwd, 'code/venv/lib/python2.7/site-packages')
    if not os.path.exists(lib_path):
        execute('generateVirtualEnvironment', 'venv')

    OUTPUT_PATH = os.path.join(cwd, 'zip')
    try:
        # Create output files folder if needed
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)
        # First zip all the used libraries
        shutil.make_archive('%s/lambda' % (OUTPUT_PATH), 'zip', lib_path)
        # Add code
        _add_code_to_zip()
    except Exception, e:
        logger.error("Exit with uncaptured exception %s" % (e))
        raise


@task
def deploy(function='comidaSlackCommand'):
    execute(render)
    command = 'aws lambda update-function-code'
    command += ' --zip-file=fileb://zip/lambda.zip'
    command += ' --function-name %s' % (function)
    logger.info('command: %s' % command)
    local(command)
