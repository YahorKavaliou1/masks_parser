import masks_parser
from masks_parser.cli import main


def test_package_has_version():
    assert masks_parser.__version__


def test_cli_without_args_prints_help(capsys):
    assert main([]) == 0
    assert "masks-parser" in capsys.readouterr().out
