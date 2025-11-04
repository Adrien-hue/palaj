from core.utils.logger import Logger
from core.utils.domain_alert import DomainAlert, Severity


def test_logger_info_warn_error_success(capsys):
    log = Logger(verbose=True)

    log.info("info msg")
    log.warn("warn msg")
    log.error("error msg")
    log.success("success msg")

    out = capsys.readouterr().out
    assert "info msg" in out
    assert "warn msg" in out
    assert "error msg" in out
    assert "success msg" in out


def test_logger_log_from_alert(capsys):
    log = Logger(verbose=True)
    alert = DomainAlert("Something went wrong", Severity.ERROR, source="Test")

    log.log_from_alert(alert)
    out = capsys.readouterr().out
    assert "Something went wrong" in out
    assert "ERROR" in out


def test_logger_silent_mode(capsys):
    log = Logger(verbose=False)
    log.info("No output expected")
    out = capsys.readouterr().out
    assert out.strip() == ""
