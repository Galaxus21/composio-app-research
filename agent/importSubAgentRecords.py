"""Adds records written by parallel Claude sub-agents to a pass, for apps the Gemini run did not finish.

    python agent/importSubAgentRecords.py --passName pass1

Used only because the free-tier Gemini key was too slow to finish all 100 apps before the
deadline. Every imported result is tagged with the model that produced it so the page can say
which apps were researched by which model. An app the Gemini run already finished is never
overwritten.
"""

import argparse
import json

from appSchema import validateRecord
from pipelineConfig import PROJECT_ROOT
from resultStore import hasResult, loadApps, saveResult

SUB_AGENT_FILE_PATTERN = "research*/records.json"
SUB_AGENT_MODEL = "claude-haiku-5-5 (sub-agent)"


def main():
    parser = argparse.ArgumentParser(description="Import sub-agent records into a pass.")
    parser.add_argument("--passName", required=True)
    arguments = parser.parse_args()
    appsById = {app["id"]: app for app in loadApps()}
    imported, kept = [], []
    for path in sorted((PROJECT_ROOT / ".agents").glob(SUB_AGENT_FILE_PATTERN)):
        for item in json.loads(path.read_text(encoding="utf-8")):
            if hasResult(arguments.passName, item["id"]):
                kept.append(item["name"])
                continue
            saveResult(arguments.passName, buildResult(appsById[item["id"]], item["record"]))
            imported.append(item["name"])
    print(f"imported {len(imported)}: {imported}")
    print(f"kept existing Gemini result for {len(kept)}: {kept}")


def buildResult(app, record):
    return {
        **app,
        "record": record,
        "validationProblems": validateRecord(record),
        "toolCalls": [],
        "usage": {},
        "hitTurnLimit": False,
        "model": SUB_AGENT_MODEL,
    }


if __name__ == "__main__":
    main()
