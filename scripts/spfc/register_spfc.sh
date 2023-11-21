 #!/bin/bash

 python3 -c "import requests;[r = requests.get('http://localhost:8080/', headers={'Accept': 'application/json'}) print(f"Response: {r.json()}")]"
 