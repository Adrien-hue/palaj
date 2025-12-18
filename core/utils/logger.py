from core.utils.domain_alert import DomainAlert

class Logger:
    """Petit utilitaire pour contrôler l'affichage coloré."""

    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "gray": "\033[90m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
    }

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _print(self, color: str, label: str, message: str):
        if not self.verbose:
            return
        c = self.COLORS.get(color, "")
        reset = self.COLORS["reset"]
        print(f"{c}{label}{reset} {message}")

    def info(self, message: str):
        self._print("cyan", "[INFO]", message)

    def success(self, message: str):
        self._print("green", "[SUCCESS]", message)

    def warn(self, message: str):
        self._print("yellow", "[WARNING]", message)

    def error(self, message: str):
        self._print("red", "[ERROR]", message)

    def debug(self, message: str):
        if self.verbose:
            self._print("gray", "[DEBUG]", message)

    def log_from_alert(self, alert: DomainAlert):
        if alert.is_error:
            self.error(alert.message)
        elif alert.is_warning:
            self.warn(alert.message)
        else:
            self.info(alert.message)
