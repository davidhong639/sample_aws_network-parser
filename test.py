#   run this file locally to test whether or not the parsing works
#   any AWS-specific functionalities can only be tested from the console itself

import os
import json
import logging
from parse_log import parse_log

def format_json(data):
    #   no list brackets outside data
    #   all data elements on a new line
    return json.dumps(data).replace('[', '').replace(']', '').replace('}, {', '},\n{')

logging.basicConfig(
	level=logging.INFO,
    format='%(levelname)s - %(filename)s:%(lineno)d - %(module)s:%(funcName)s - %(message)s'
)
log = logging.getLogger(__name__)

dir = '~'
filename = '33TC-CORE01.log'

hostname, output_device, output_interface, output_trunk = [None] * 4
with open(os.path.join(dir, filename), 'r') as file:
    hostname, output_device, output_interface, output_trunk = parse_log(log, file)

with open('device.json', 'w') as file:
    string = format_json(output_device)
    file.write(string)

with open('interface.json', 'w') as file:
    string = format_json(output_interface)
    file.write(string)

with open('trunk.json', 'w') as file:
    string = format_json(output_trunk)
    file.write(string)
