# SPDX-FileCopyrightText: © 2023 Menacit AB <foss@menacit.se>
# SPDX-License-Identifier: CC-BY-SA-4.0
# X-Context: Virtualisation course - Lab

'''
> mixologyfy - Next-generation cocktail application!

Listens for HTTP on port 1338/TCP by default.
Settings configurable using environment variables:

"APP_DEBUG_LOGGING":
If set to "enabled", debug log messages are included.
If set to "disabled", debug log messages are excluded.
Default:
"disabled"

"APP_FIGLET_PATH":
File system path to the third-party "figlet" binary/executable.
Default:
"/usr/bin/figlet"

"APP_SOURCE_URL":
Source HTTP(S) URL to IBA cocktail recipes in JSON format.
Default:
http://raw.githubusercontent.com/teijo/iba-cocktails/master/recipes.json

"APP_TEMPLATE_PATH":
File system path to Jinja2 HTML template for web application.
Default:
"/opt/mixologyfy/index.html.jinja"

"APP_DATABASE_URI":
PostgreSQL connection URI required for storing favorites (and "VG" grade).
Example:
postgresql://user:password@host/database_name
'''

import os
import sys
import random
import subprocess
import logging as _log

# -----------------------------------------------------------------------------
# Configure log level -
# Reads environment variable "APP_DEBUG_LOGGING" and validates that it contains
# an acceptable value (either "enabled" or "disabled")
log_format = '%(levelname)s: %(message)s'
debug_option = os.getenv('APP_DEBUG_LOGGING', 'enabled')

if debug_option == 'enabled':
    _log.basicConfig(format=log_format, level=_log.DEBUG)
    _log.debug('Debug logging is enabled!')

elif debug_option != 'disabled':
    _log.basicConfig(format=log_format, level=_log.ERROR)
    _log.error(
        'Value of environment variable "APP_DEBUG_LOGGING" '
        f'must be "enabled" or "disabled", not "{debug_option}" - exiting!')

    sys.exit(1)

else:
    _log.basicConfig(format=log_format, level=_log.INFO)

# -----------------------------------------------------------------------------
# Validate third-party executable/non-Python dependency -
# Reads environment variable "APP_FIGLET_PATH" and validates that the specified
# file path both exists and is executable/runnable as an application
FIGLET_PATH = os.getenv('APP_FIGLET_PATH', '/usr/bin/figlet')
_log.debug(
    f'Checking if "figlet" application exist/is executable at "{FIGLET_PATH}"')

if not (os.path.isfile(FIGLET_PATH) and os.access(FIGLET_PATH, os.X_OK)):
    _log.error(
        'The third-party "figlet" application does not exist or '
        f'can not be executed from the path "{FIGLET_PATH}" - exiting!')

    sys.exit(1)

# -----------------------------------------------------------------------------
# Validate source URL -
# Reads environment variable "APP_SOURCE_URL" and validates that its value
# starts with either "http://" or "https://"
SOURCE_URL = os.getenv(
    'APP_SOURCE_URL',
    'http://raw.githubusercontent.com/teijo/iba-cocktails/master/recipes.json')

_log.debug(
    f'Checking that cocktail source data URL "{SOURCE_URL} is using HTTP(S)')

if not (SOURCE_URL.startswith('http://') or SOURCE_URL.startswith('https://')):
    _log.error(
        f'The specified coctal source data URL "{SOURCE_URL}" does not '
        'start with "http://" or "https://" as required - exiting!')

    sys.exit(1)

# -----------------------------------------------------------------------------
# Validate web page template file -
# Reads environment variable "APP_TEMPLATE_PATH" and validates that the
# specified Jinja2 template file exists and is readable
TEMPLATE_PATH = os.getenv('APP_TEMPLATE_PATH', '/home/debian/flaskapp/index.html.jinja')

_log.debug(
    f'Checking if HTML template file exist/is readable at "{TEMPLATE_PATH}"')

if not (os.path.isfile(TEMPLATE_PATH) and os.access(TEMPLATE_PATH, os.R_OK)):
    _log.error(
        f'The configured Jinja2 HTML template file "{TEMPLATE_PATH}" '
        'does not exist or is not readable - exiting!')

    sys.exit(1)


# -----------------------------------------------------------------------------
# Import third-party Python dependencies -
# Tries to load required Python modules that not included in standard library
_log.debug('Trying to load/import third-party Python dependencies')

try:
    from flask import Flask, redirect, render_template_string
    from requests import get as http_get

except Exception as error_message:
    _log.error(f'Failed to import third-party Python module: {error_message}')
    sys.exit(1)
# -----------------------------------------------------------------------------
_log.info(f'Fetching cocktail recipe data from "{SOURCE_URL}"')

try:
    COCKTAIL_DATA = http_get(SOURCE_URL).json()

except Exception as error_message:
    _log.error(
        f'Failed to fetch recipe data from "{SOURCE_URL}": "{error_message}"')

    sys.exit(1)

_log.debug('Executing "figlet" application to generate ASCII-art titles')

try:
    for cocktail in COCKTAIL_DATA:
        cocktail['figlet_name'] = subprocess.run(
            [FIGLET_PATH, '-w', '120'], input=cocktail['name'],
            capture_output=True, text=True, check=True).stdout

except Exception as error_message:
    _log.error(
        'Failed to execute figlet to generate banner for '
        f'cocktail name: "{error_message}" - exiting!')

    sys.exit(1)

# -----------------------------------------------------------------------------
_log.debug('Setting up Flask application')

app = Flask('mixologyfy')
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
    
# -----------------------------------------------------------------------------
@app.route('/')
def return_cocktails():
    _log.info('Handling cocktail list request!')

    try:
        with open(TEMPLATE_PATH, 'r') as file_handle:
            template_data=file_handle.read()

    except Exception as error_message:
        raise Exception(
            'Failed to read HTML template file from '
            f'"{TEMPLATE_PATH}": "{error_message}"')

    return render_template_string(
        template_data,
        cocktails=random.sample(COCKTAIL_DATA, len(COCKTAIL_DATA)))

# -----------------------------------------------------------------------------
# If run as a program, start web server
if __name__ == '__main__':
    _log.debug('Starting built-in web server')
    app.run(host='0.0.0.0', port=80)
