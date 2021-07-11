#!/usr/bin/env python
"""Entry point to start an instrumentalized bot for coverage and run tests."""

from subprocess import Popen, run
from unittest import main


def run_and_test():
    """Launch the bot and its tests."""
    bot = Popen(['coverage', 'run', 'matrix_webhook.py'])
    ret = main(module=None, exit=False).result.wasSuccessful()
    bot.terminate()
    for cmd in ['report', 'html', 'xml']:
        run(['coverage', cmd])
    return ret


if __name__ == '__main__':
    exit(not run_and_test())
