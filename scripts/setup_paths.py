"""Set the project's one local data-path parameter. Run before opening Desktop."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "powerbi/OnlineRetail.SemanticModel/model.bim"
body = json.loads(path.read_text(encoding="utf-8"))
folder = (
    r"C:\RETAIL_INSIGHTS\data\processed"
    if "--portable" in sys.argv
    else str(ROOT / "data/processed").replace("/", "\\")
)
parameter = next(e for e in body["model"]["expressions"] if e["name"] == "DataFolder")
parameter["expression"] = (
    '"'
    + folder.replace('"', '""')
    + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
)
path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
print(
    "Restored portable DataFolder."
    if "--portable" in sys.argv
    else "Configured DataFolder for this local clone. Do not commit your personal path."
)
