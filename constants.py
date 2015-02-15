#!/usr/bin/env python
#
"""constants.py - Aggregate various constants used to control simulation.


"""

__author__ = 'niallm@gmail.com (Niall Richard Murphy)'

class defines(object):
  """Contains useful constants that control simulation behaviour."""
  _LIR_INITIAL_POLICY = 21 # What initial prefix size (in CIDR) an LIR gets
  _LIR_DEFAULT_POLICY = 21 # What an LIR requester gets by default
  _RIR_INITIAL_POLICY = 8 # What an RIR assigns the requester initially
  _RIR_DEFAULT_POLICY = 8 # What an RIR assigns the requester by default
  _UNSIZED_DEFAULT_REQUEST = 0 # How a requester signals unsized default rq
  _UNSIZED_INIT_REQUEST = -1 # How a requester signals unsized initial rq
  _YEAR_MIN_BEGIN = 1993 # Year before which we think it's an error
  _YEAR_MAX_END = 2050 # Year after which we think it's an error
  _DEFAULT_HOWMANYNEEDED = 1 # How many addresses do I need
  _COST_BUSINESS_LOW = 0 # 'The cost of doing business' as an addr supplier
  _DEFAULT_LIR_STATIC_SCALING_SIZE = 13 # The /NN that we request for LIR_Static
  _RIR_DEFAULT_REQUEST = 2 ** 24 # RIRs want a /8 from IANA by default.
  _DEFAULT_LIR_REQUEST_MULTIPLIER = 1.1 # Multiplier in LIR_Monthly_Exp
  _LOOKBACK = 10 # Number of requests to look back at
  _LOOKBACK_PERIOD = 30 * 18 # Period of time in days to look back at
  _DEFAULT_CUTOFF = 365 # In days
  # These are reserved spaces that come from
  # http://www.iana.org/assignments/ipv4-address-space
  _RESERVED_SPACES = ['0/8', '1/8', '5/8', '7/8', '23/8', '27/8', '31/8', '36/8',
                      '37/8', '39/8', '42/8', '46/8', '49/8', '50/8', '94/8',
                      '95/8', '100/8', '101/8', '102/8', '103/8', '104/8', '105/8',
                      '106/8', '107/8', '108/8', '109/8', '110/8', '111/8', '112/8',
                      '113/8', '114/8', '115/8', '127/8', '173/8', '174/8', '175/8',
                      '176/8', '177/8', '178/8', '179/8', '180/8', '181/8', '182/8',
                      '183/8', '184/8', '185/8', '186/8', '187/8', '197/8', '223/8',
                      '240/8', '241/8', '242/8', '243/8', '244/8', '245/8', '246/8',
                      '247/8', '248/8', '249/8', '250/8', '251/8', '252/8', '253/8',
                      '254/8', '255/8']
  # These are spaces that we couldn't, without protocol changes or
  # significant work, ever deploy on the public Internet. That means
  # obviously RFC1918 space, multicast, and other networks listed
  # in RFC3330
  _FORBIDDEN_SPACES = [ '192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12',
                      '224.0.0.0/8', '225.0.0.0/8', '226.0.0.0/8',
                      '227.0.0.0/8', '228.0.0.0/8', '229.0.0.0/8',
                      '230.0.0.0/8', '231.0.0.0/8', '232.0.0.0/8',
                      '233.0.0.0/8', '234.0.0.0/8', '235.0.0.0/8',
                      '236.0.0.0/8', '237.0.0.0/8', '238.0.0.0/8',
                      '239.0.0.0/8', '169.254.0.0/16', '192.0.2.0/24',
                      '198.18.0.0/15' ]
  _DATA_DIR = "data"
  _LONG_TABLE = _DATA_DIR + "/routing-table.txt"
  _SHORT_TABLE = _DATA_DIR + "/short-table.txt"
  _DEFAULT_TABLE = _DATA_DIR + "/routing-table.txt"
  _DEFAULT_ALLOC = _DATA_DIR + "/delegated.txt"
  _REGISTRY_DATA = ['ftp://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest',
                    'ftp://ftp.apnic.net/public/apnic/stats/apnic/delegated-apnic-latest',
                    'ftp://ftp.arin.net/pub/stats/arin/delegated-arin-latest',
                    'ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest',
                    'ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest',
                    'http://www.potaroo.net/bgp/stats/iana/delegated-iana-latest',
                    'http://bgp.potaroo.net/stats/nro/delegated.nro.txt']
  _STARTUP_CHECKPOINT_FILE = "startup.checkpoint.simlir"
  _CHECKPOINT_FILE = "checkpoint.simlir"
  _DEFAULT_NON_ZERO_DATE = "19930101"
  #_DEFAULT_LIR_BEHAVIOUR = "LIR_Simple_Steady_State"
  _DEFAULT_LIR_BEHAVIOUR = "LIR_Static"
  #_DEFAULT_RIR_BEHAVIOUR = "RIR_Standard"
  _DEFAULT_RIR_BEHAVIOUR = "RIR_Standard"
  _DEFAULT_LIR_NAME = "Default LIR Name"
  _DEFAULT_LIR_BEHAVE = "LIR_Fortnightly_Average"
  _DEFAULT_RIR_NAME = "Default RIR Name"
  _DEFAULT_GENERATE_ME = "ie.GENERATE_ME"
  _UNSIZED_INIT_REQUEST = -1
  _UNSIZED_DEFAULT_REQUEST = 0
  _STARTCBASE = 10
  _STEPWISE = 100000
  _NRO_DATA = "data/delegated.nro.txt"
  # These are used for the unit tests, and currently have to be manually updated.
  _IANA_START_FREE = 16.015625
  _CURRENT_FREE_POOL_COUNT = 42
  _IETF_RESERVATIONS = 35.0781555176
  _IANA_VARIOUS = 47.9218444824
  _IANA_RESERVATIONS = 43
  _AFRINIC_START_RECV = 2
  _APNIC_START_RECV = 26
  _ARIN_START_RECV = 29
  _LACNIC_START_RECV = 6
  _RIPE_START_RECV = 26
  _ARIN_POP_SIZE = 20
  _KNOWN_LIR_NAMES = ['', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AP', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BM', 'BN', 'BO', 'BR', 'BS', 'BT', 'BW', 'BY', 'BZ', 'CA', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CS', 'CU', 'CV', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DO', 'DZ', 'EC', 'EE', 'EG', 'ER', 'ES', 'ET', 'EU', 'FI', 'FJ', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GP', 'GQ', 'GR', 'GT', 'GU', 'GW', 'GY', 'HK', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KN', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SI', 'SK', 'SL', 'SM', 'SN', 'SR', 'SV', 'SY', 'SZ', 'TC', 'TG', 'TH', 'TJ', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'ZA', 'ZM', 'ZW']
  _INSTRUMENTATION_DEFAULT_VERBOSITY = 0
  _DEFAULT_EXHAUSTION_COUNT = 256
  _EXPECTED_EXHAUSTION_COUNT = 147
  _INSTRUMENTATION_MODES = { 'syslog': 0, 'stdout': 1, 'gui': 2}
  _INSTRUMENTATION_DEFAULT_MODE = _INSTRUMENTATION_MODES['stdout']
