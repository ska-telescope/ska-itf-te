import argparse
import piplates.RELAYplate as RELAY

# Set up arguments to be parsed
parser = argparse.ArgumentParser(description = 'Specify relay number and 1 for on or 0 for off')
parser.add_argument('relay', type = int, help = 'Specify relay 1 to 7')
parser.add_argument('onoff', type = str, help = '1 for on, 0 for off')
args = parser.parse_args()

print(RELAY.getID(0))

if int(args.onoff) == 1:
	RELAY.relayON(0, int(args.relay))
else:
	RELAY.relayOFF(0, int(args.relay))
