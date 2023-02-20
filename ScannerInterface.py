import re

class ScannerInterface:
	def __init__(self, hostname, intf_name, port_num, section_config):
		self.hostname = hostname
		self.intf_name = intf_name
		self.port_num = port_num

		self.duplex = None
		self.poe = True
		self.vlan_access = None
		self.vlan_trunk_native = None
		self.vlan_trunk_allowed = []

		self.parse_running_config(section_config)

	def parse_running_config(self, section_config):
		is_duplex = re.compile(r'duplex (.+)')
		is_access = re.compile(r'switchport access vlan (\d+)')
		is_trunk_native = re.compile(r'switchport trunk native vlan (\d+)')
		is_trunk_allowed = re.compile(r'switchport trunk allowed vlan (?:add )?(.+)')
		for line in section_config:
			line = line.lower().strip()

			match_duplex = re.match(is_duplex, line)
			if match_duplex:
				self.duplex = match_duplex.group(1)

			if line == 'power inline never':
				self.poe_enabled = False

			match_access = re.match(is_access, line)
			if match_access:
				self.vlan_access = int(match_access.group(1))

			match_trunk_native = re.match(is_trunk_native, line)
			if match_trunk_native:
				self.vlan_trunk_native = int(match_trunk_native.group(1))

			match_trunk_allowed = re.match(is_trunk_allowed, line)
			if match_trunk_allowed:
				list_trunk = match_trunk_allowed.group(1).split(',')
				for vlan in list_trunk:
					list_vlan = vlan.split('-')
					list_vlan = [int(item) for item in list_vlan]
					if len(list_vlan) == 2:
						start = list_vlan[0] + 1
						end = list_vlan[1]
						for item in range(start, end):
							list_vlan.append(item)
					for item in list_vlan:
						self.vlan_trunk_allowed.append(item)

	def get_data_intf(self):
		return {
			'hostname': self.hostname,
			'intf_name': self.intf_name,
			'port_num': self.port_num,
			'duplex': self.duplex,
			'poe': self.poe,
			'vlan_access': self.vlan_access,
			'vlan_trunk_native': self.vlan_trunk_native,
			#'vlan_trunk_allowed': self.vlan_trunk_allowed,
		}

	def get_data_trunk(self):
		list_ = []
		for vlan in self.vlan_trunk_allowed:
			list_.append({
				'hostname': self.hostname,
				'intf_name': self.intf_name,
				'vlan_trunk': vlan
			})
		return list_
