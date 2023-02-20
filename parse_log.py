import re

from ScannerDevice import ScannerDevice
from ScannerInterface import ScannerInterface

head_tables = [
	{
		'command': 'mac address-table',
		'headers': [
			'vlan', 
			'mac address', 
			'type', 
			'ports'
		],
	},
	{
		'command': 'cdp neighbors',
		'headers': [
			'device id', 
			'local intrfce', 
			'holdtme', 
			'capability', 
			'platform', 
			'port id'
		],
	},
	{
		'command': 'lldp neighbors',
		'headers': [
			'device id',
			'local intf',
			'hold-time',
			'capability',
			'port id'
		]
	}
]
head_break = [
	{
		'command': 'interface | inc Ethernet|Vlan',
		'break': r'\s*(.+) is (?:administratively )?(?:up|down), line protocol is (?:up|down)(?: \((?:not)?connect(?:ed)?\))?',
		'is_key': True
	},
	{
		'command': 'lldp nei de',
		'break': r'^-+$|^total entries displayed: \d+$',
		'is_key': False
	}
]
head_startend = [
	{
		'command': 'running-config',
		'start': r'interface ((?:.+ethernet|vlan|port-channel)(?:\d+\/)*\d+)',
		'end': r'^!$',
		'is_key': True,
		'sub_category': 'interface-config'
	}
]
head_secondary = [
	{
		'command': 'lldp nei de',
		'keys': [
			'local intf',
			'chassis id',
			'port id',
			'port description',
			'system name',
			'system capabilities',
			'enabled capabilities'
		]
	}
]
intf_name = {
	'fastethernet': 'fe',
	'gigabitetheret': 'gi',
	'gig': 'gi',
	'tengigabitethernet': 'te',
	'ten': 'te'
}

def parse_log(log, file, privileged='#'):
	hostname = None
	output_device = None
	output_interface = None

	try:
		#	purely text log is difficult to write clean. readable code around
		sections_log = {}

		#	each command output comes after a "show" command is executed
		is_show = re.compile(r'.+' + privileged + r'show (.+)')
		show = None
		#	convert file contents into a dictionary
		#	each show command points to its respective output
		#	further processing of individual sections will come later
		try:
			for line in file.iter_lines():
				line = line.decode('utf-8')
				match_show = re.match(is_show, line)
				if match_show:
					show = match_show.group(1).strip()
					sections_log[show] = []
				if not show:
					continue
				sections_log[show].append(line.rstrip())
		except:
			for line in file:
				match_show = re.match(is_show, line)
				if match_show:
					show = match_show.group(1).strip()
					sections_log[show] = []
				if not show:
					continue
				sections_log[show].append(line.rstrip())

		#	some show commands output data in a table format
		#	a table consists of rows and columns under a header
		#	further divide output by headers
		for _ in head_tables:
			command = _['command']
			if command not in sections_log:
				log.info('read switch config - command not found (command=%s)' % command)
				continue
			heads = _['headers']
			#	build the header
			raw_ = r''
			for head in heads:
				raw_ += r'({}\s*)'.format(head)
			is_head = re.compile(raw_)
			#	some tables have horizontal lines under the header
			#	these horizontal lines should be ignored
			is_hr = re.compile(r'^[\s-]+$')
			#	each header has a given length
			#	the length includes whitespace
			#	what item belongs to which column is based on the length of heac header
			index_header = []
			dangle = None
			#	convert table into list of dictionaries given the header
			list_ = []
			for line in sections_log[command]:
				#	if header is not present, create
				if not index_header:
					match_header = re.match(is_head, line.lower())
					if match_header:
						start = 0
						for group in match_header.groups():
							end = len(group)
							index_header.append((start, start + end))
							start += end
					continue
				#	if horizontal line found, skip
				match_hr = re.match(is_hr, line)
				if match_hr:
					continue
				#	headers are padded with whitespace for readability
				#	each header has a given length
				#	the length is a starting and ending index
				#	in a row, anything bounded by the index is under the given column
				if len(line) > index_header[-1][0]:
					dict_ = {}
					if dangle:
						dict_[heads[0]] = dangle
					index = 0 if not dangle else 1
					for start, end in index_header[index:]:
						dict_[heads[index]] = line[start: end].strip()
						index += 1
					dangle = None
					if dict_:
						list_.append(dict_)
				else:
					dangle = line.strip()
			#	replace the given section of the log
			sections_log[command] = list_

		#	some blocks of code are divided by clear delimiters
		#	these delimiters are the same for start and end
		for _ in head_break:
			command = _['command']
			if command not in sections_log:
				log.info('read switch config - command not found (command=%s)' % command)
				continue
			is_head = re.compile(_['break'])
			is_key = _['is_key']
			#	each time the delimiter is found, a new section starts
			#	record the original section, then move on
			output = {}
			if not is_key:
				output = []
				text = []
			head = None
			for line in sections_log[command]:
				match_head = re.match(is_head, line.lower().strip())
				if match_head:
					if is_key:
						head = match_head.group(1)
						output[head] = []
					else:
						if text:
							output.append(text)
						text = []
						head = line
				if head:
					if is_key:
						output[head].append(line)
					else:
						text.append(line)
			sections_log[command] = output
		
		#	a start and end denote clear blocks within show output
		#	the start and end have different values
		for _ in head_startend:
			command = _['command']
			if command not in sections_log:
				log.info('read switch config - command not found (command=%s)' % command)
				continue
			is_start = re.compile(_['start'])
			is_end = re.compile(_['end'])
			is_key = _['is_key']
			#	each time a new end is found, stop recording output for the prior start
			#	each time a new start is found, start recorind output for the given start
			output = {}
			head = None
			for line in sections_log[command]:
				match_start = re.match(is_start, line.lower().strip())
				match_end = re.match(is_end, line.lower().strip())
				if match_start:
					head = match_start.group(1)
					if is_key:
						output[head] = []
				if not head:
					continue
				if match_end:
					head = None
				else:
					if is_key:
						output[head].append(line)
			sub_category = _['sub_category']
			sections_log[sub_category] = output

		#	some blocks still contain a large amount of redundant information
		#	further process to simplify data even further
		for _ in head_secondary:
			command = _['command']
			if command not in sections_log:
				log.info('read switch config - command not found (command=%s)' % command)
				continue
			keys = _['keys']
			#	currently, only one block (show lldp nei de) needs additional processing
			#	each key listed is a field that needs a value to determine source/target
			#	use each key to create the corresponding regex and extract data that way
			output = []
			for block in sections_log[command]:
				dict_ = {key: None for key in keys}
				for line in block:
					line = line.lower()
					for key in keys:
						is_key = re.compile(key + r': (.+)')
						match_key = re.match(is_key, line)
						if match_key:
							dict_[key] = match_key.group(1)
				output.append(dict_)
			sections_log[command] = output

		#	create device scanner to process modified log file contents
		#	overall configuration will be written to json for processing
		scanner_device = ScannerDevice(sections_log)
		data_device = scanner_device.get_data()
		output_device = [data_device]

		#	record configuratiosn for each given interface
		#		configuration of all interfaces stored as list
		#		this table is kept separate from the device configuration
		#	record configuration for all trunk vlans on each interface
		#		could be stored as a list for each given interface
		#		under normalization, multi-attribute fields are not allowed
		hostname = scanner_device.get_hostname()
		output_interface = []
		output_trunk = []
		for port_num, intf_name in enumerate(sorted(sections_log['interface-config'].keys())):
			if not intf_name.startswith('port-channel') and not intf_name.startswith('vlan'):
				config = sections_log['interface-config'][intf_name]
				scanner_interface = ScannerInterface(hostname, intf_name, port_num, config)

				data_interface = scanner_interface.get_data_intf()
				output_interface.append(data_interface)

				data_trunk = scanner_interface.get_data_trunk()
				for data in data_trunk:
					#output_trunk.append([data[_] for _ in fields_vlan_trunk])
					output_trunk.append(data)
	except Exception as e:
		hostname = None
		output_device = None
		output_interface = None
		log.error('unable to parse logs: %r' % e)

	return hostname, output_device, output_interface, output_trunk
