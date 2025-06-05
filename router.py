import sys
from typing import List, Optional
from virtual_links import Router


class RouterCLI:
    def __init__(self, router: Router):
        self.router = router
        self.commands = {
            "add": self._add,
            "del": self._delete,
            "trace": self._trace,
            "list": self._list,
            "quit": self._quit,
        }
        self._should_quit = False

    def run(self):
        """Main interactive loop."""
        while not self._should_quit:
            try:
                raw = input().strip()
                if raw:
                    self._dispatch(raw.split())
            except (EOFError, KeyboardInterrupt):
                break
            except Exception:
                pass  # Stay silent on unexpected errors
        self.router.stop_server()

    def run_startup(self, filepath: str):
        """Run startup file silently."""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    cmd = line.strip().split()
                    if cmd:
                        self._dispatch(cmd, silent=True)
                        if self._should_quit:
                            self._should_quit = False
        except Exception:
            pass  # Silent fail on file issues

    def _dispatch(self, parts: List[str], silent: bool = False):
        action = parts[0].lower()
        args = parts[1:]
        handler = self.commands.get(action)
        if handler:
            handler(args)
        elif not silent:
            pass  # Unknown commands are silently ignored

    def _add(self, args: List[str]):
        if len(args) == 2:
            ip, weight = args
            try:
                self.router.add_neighbor(ip, int(weight))
            except ValueError:
                pass  # Silent fail

    def _delete(self, args: List[str]):
        if len(args) == 1:
            self.router.remove_neighbor(args[0])

    def _trace(self, args: List[str]):
        if len(args) == 1:
            self.router.trace_route(args[0])

    def _list(self, args: List[str]):
        neighbors = self.router.get_neighbors()
        for ip, weight in neighbors.items():
            print(f"{ip} {weight}")

    def _quit(self, args: List[str]):
        self._should_quit = True


def parse_args(argv: List[str]) -> Optional[tuple[str, int, Optional[str]]]:
    if len(argv) < 3:
        return None
    try:
        address = argv[1]
        period = int(argv[2])
        file = argv[3] if len(argv) > 3 else None
        return address, period, file
    except ValueError:
        return None


def main():
    args = parse_args(sys.argv)
    if not args:
        sys.exit(1)

    address, period, startup_file = args
    router = Router(address, period)
    router.start_server()

    cli = RouterCLI(router)
    if startup_file:
        cli.run_startup(startup_file)
    cli.run()


if __name__ == "__main__":
    main()
