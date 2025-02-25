import csv
import os, sys
FACTOR=2

in_fn = os.path.join(os.path.dirname(sys.argv[0]),'data.csv')
out_fn = os.path.join(os.path.dirname(sys.argv[0]),'output.svg')

# Read data from the spreadsheet (exported as CSV)
with open(in_fn, 'r') as file:
    reader = csv.DictReader(file)
    data = list(reader)

X = []
Y = []
for row in data:
    X.append(float(row['x']))
    Y.append(float(row['y']))
    
minX = min(X)
minY = min(Y)
maxX = (max(X)-minX+5)*FACTOR
maxY = (max(Y)-minY+5)*FACTOR

# Generate SVG content
svg_content = f'<svg width="{maxX+50}" height="{maxY+50}" xmlns="http://www.w3.org/2000/svg">\n'
svg_content += '  <rect width="100%" height="100%" fill="white"/>\n'

for row in data:
    x = float(row['x'])-minX+5
    y = float(row['y'])-minY+5
    label = row['label']
    if label=="SKA001" or label=="SKA036" or label=="SKA063" or label=="SKA100":
        COLOUR="red"
        SIZE="3"
    else:
        COLOUR="black"
        SIZE="2"
    svg_content += f'  <circle cx="{x*FACTOR}" cy="{y*FACTOR}" r="{SIZE}" fill="{COLOUR}"/>\n'
    # svg_content += f'  <text x="{int(x)+5}" y="{int(y)+5}" font-family="Arial" font-size="12" fill="black">{label}</text>\n'

svg_content += '</svg>'

# Save to an SVG file
with open(out_fn, 'w') as file:
    file.write(svg_content)

print("SVG file created successfully!")