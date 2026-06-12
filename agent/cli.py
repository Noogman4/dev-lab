import sys
from agent.tools import list_files, read_file
from agent.runner import run_command


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m agent.cli <command>")
        return

    command = " ".join(sys.argv[1:])

    if command == "liste dateien":
        files = list_files()
        for f in files[:20]:
            print(f)

    elif command.startswith("zeige "):
        filename = command.replace("zeige ", "")
        print(read_file(filename))

    else:
        try:
            print(run_command(command))
        except ValueError as exc:
            print(f"Fehler: {exc}")


if __name__ == "__main__":
    main()
