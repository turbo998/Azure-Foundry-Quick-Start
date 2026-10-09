"""Serve the shared IQ agent through the Foundry Responses protocol."""

import argparse

from agent import create_agent
from config import AgentSettings, load_environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args()
    load_environment()
    settings = AgentSettings.from_environment(iq=True)
    if args.check_config:
        print("Hosted configuration is structurally valid; no host or service was started.")
        return
    from agent_framework_foundry_hosting import ResponsesHostServer

    ResponsesHostServer(create_agent(settings), history_source="agent").run()


if __name__ == "__main__":
    main()
