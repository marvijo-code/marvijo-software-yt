# Benchmark task: pallets/click

## Issue #2819 - "help not resolving automatically"

From the docs:

> The help parameter is implemented in Click in a very special manner. Unlike regular parameters it's automatically added by Click for any command and it performs automatic conflict resolution. By default it's called --help, but this can be changed. If a command itself implements a parameter with the same name, the default help parameter stops accepting it. There is a context setting that can be used to override the names of the help parameters called help_option_names.

What is wrong:

Help does not automatically resolve if there is an arg or kwarg called `help`. In the sample the file is called `help.py`

```python
import click

# This works
@click.command()
@click.argument('helps')
def this_works(helps):
    print(helps)

# > python -m help this
# this

# > python -m help --help
# Usage: help.py [OPTIONS] HELPS
#
# Options:
#   --help  Show this message and exit.

# This does not work
@click.command()
@click.argument('help')
def this_does_not_work(help):
    print(help)

# > python -m help this
# Usage: help.py [OPTIONS] HELP
# Try 'help.py --help' for help.
#
# Error: Invalid value for '--help': 'this' is not a valid boolean.

# > python -m help --help
# Usage: help.py [OPTIONS] HELP
# Try 'help.py --help' for help.
#
# Error: Missing argument 'HELP'.

# This does not work
@click.command()
@click.option('--help', default='this_2')
def this_does_not_work_also(help='this_2'):
    print(help)

# > python -m help
# None

# > python -m help --help
# Error: Option '--help' requires an argument.

if __name__ == '__main__':
    this_does_not_work_also()
```

- Python version: 3.10.15
- Click version: 8.1.7

## Minimal repro

```python
import click
from click.testing import CliRunner

@click.command()
@click.argument("help")
def cli(help):
    click.echo(help)

result = CliRunner().invoke(cli, ["value"])
print(repr(result.output), result.exit_code)
# BUG: prints an error ("'value' is not a valid boolean") with exit_code 2
# FIXED: prints 'value\n' with exit_code 0, and `cli --help` still shows the help page
```

The automatic `--help` option stores its value under the storage name `help`, so a
user parameter that also uses the name `help` collides with it and breaks parsing.

## Rules

Fix the bug in the library source. Do NOT modify test files. Hidden maintainer-written
tests for this exact bug will grade you. The virtualenv at `.venv` is ready
(`.venv/Scripts/python`). Wall-clock time counts. Hard cap 10 minutes.
