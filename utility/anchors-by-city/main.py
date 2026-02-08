import sys
import json
import argparse

parser = argparse.ArgumentParser(description='Read and parse anchors/[name].anchors file')
parser.add_argument('name', help='City name (in ./anchors/)')
args = parser.parse_args()

path = '../../anchors/' + args.name + '.anchors'
anchors = []
try:
    with open(path, 'r') as file:
        data = json.load(file)
        for result in data['results']:
            if result['is_disabled'] == True:
                continue
            if result['date_decommissioned'] != None:
                continue
            anchors.append({'fqdn':result['fqdn'], 'probe':result['probe']})
except Exception as e:
    print(f"Error message: {str(e)}", file=sys.stderr)

print(anchors)