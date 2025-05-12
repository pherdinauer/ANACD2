import sys
from cli import ANACDownloaderCLI

def main():
    # Avvia l'interfaccia CLI
    cli = ANACDownloaderCLI()
    cli.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())