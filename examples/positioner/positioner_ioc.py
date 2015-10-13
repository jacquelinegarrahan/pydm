from pcaspy import SimpleServer, Driver, Severity
import time

prefix = 'MOTOR:'
pvdb = {
	'1:VAL': {
		'value': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
	},
	'1:STR': {
    'type': 'string',
		'value': 'Hello'
	},
	'1:INT': {
    'type': 'int',
		'value': 5
	},
	'2:VAL': {
		'value': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
	},
	'3:VAL': {
		'value': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
	},
  'STATUS': {
    'type': 'enum',
    'enums': ['Off', 'On'],
    'states': [Severity.MINOR_ALARM, Severity.NO_ALARM],
  }
}

class myDriver(Driver):
	def __init__(self):
		super(myDriver, self).__init__()
	
if __name__ == '__main__':
	server = SimpleServer()
	server.createPV(prefix, pvdb)
	driver = myDriver()
	print "Server is running... (ctrl+c to close)"
	while True:
		server.process(0.1)