import re
from ScannerInterface import ScannerInterface

class ScannerDevice:
	def __init__(self, sections_log):
		self.chassis_id = None
		self.community_string = None
		self.domain_name = None
		self.hostname = None
		self.is_layer3 = None
		#self.ivn_port = {}
		self.lldp_enabled = False
		self.mgmt_vlan = None
		self.mgmt_vlan_native = False
		#self.port_channels = {}
		self.site_id = None
		self.spt_mode = None
		#self.vlans = {}

		self.parse_running_config(sections_log['running-config'])
		self.set_chassis_id(sections_log['lacp sys-id'])


	def parse_running_config(self, section):
		is_hostname = re.compile(r'hostname (.+)')
		is_domainName = re.compile(r'ip domain-name (.+)')
		is_sptMode = re.compile(r'spanning-tree mode (.+)')
		is_snmpCommunityRO = re.compile(r'snmp-server community (.+) RO')
		is_snmpCommunityRW = re.compile(r'snmp-server community (.+) RW')
		for line in section:
			line = line.strip()

			match_hostname = re.match(is_hostname, line)
			if match_hostname:
				self.hostname = match_hostname.group(1)

			match_domainName = re.match(is_domainName, line)
			if match_domainName:
				self.domain_name = match_domainName.group(1)

			if 'lldp run' in line.lower():
				self.lldp_enabled = True

			match_sptMode = re.match(is_sptMode, line)
			if match_sptMode:
				self.spt_mode = match_sptMode.group(1)

			if line.lower().startswith('ip route'):
				self.is_layer3 = True

			match_snmpCommunityRO = re.match(is_snmpCommunityRO, line)
			if match_snmpCommunityRO:
				self.community_string = match_snmpCommunityRO.group(1)
			match_snmpCommunityRW = re.match(is_snmpCommunityRW, line)
			if match_snmpCommunityRW:
				self.community_string = match_snmpCommunityRW.group(1)

	def set_chassis_id(self, section_lacp):
		is_chassisID = re.compile(r'\d+,\s*(.+)')
		for line in section_lacp:
			line = line.strip()
			match_chassisID = re.match(is_chassisID, line)
			if match_chassisID:
				self.chassis_id = match_chassisID.group(1)

	def get_data(self):
		return {
			'chassis_id': self.chassis_id,
			'community_string': self.community_string,
			'domain_name': self.domain_name,
			'hostname': self.hostname,
			'is_layer3': self.is_layer3,
			#'ivn_port': self.ivn_port,
			'lldp_enabled': self.lldp_enabled,
			'mgmt_vlan': self.mgmt_vlan,
			'mgmt_vlan_native': self.mgmt_vlan_native,
			#'port_channels': self.port_channels,
			'site_id': self.site_id,
			'spt_mode': self.spt_mode,
			#'vlans': self.vlans
		}

	def get_hostname(self):
		return self.hostname
