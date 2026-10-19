from q049_cpu import orbit
import json
from pathlib import Path
runs=[orbit('Leapfrog',200,n)[0] for n in [30,300]]
Path('/work/duration.json').write_text(json.dumps(runs,indent=2))
print(json.dumps(runs))
