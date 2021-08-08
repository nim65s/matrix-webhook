"""Matrix Webhook module entrypoint."""
import logging

from . import app, conf

if __name__ == "__main__":
    log_format = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    logging.basicConfig(level=50 - 10 * conf.VERBOSE, format=log_format)
    app.run()
