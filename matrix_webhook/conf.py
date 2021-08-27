"""Configuration for Matrix Webhook."""
import argparse
import os

parser = argparse.ArgumentParser(description=__doc__, prog="python -m matrix_webhook")
parser.add_argument(
    "-H",
    "--host",
    default=os.environ.get("HOST", ""),
    help="host to listen to. Default: `''`. Environment variable: `HOST`",
)
parser.add_argument(
    "-P",
    "--port",
    type=int,
    default=os.environ.get("PORT", 4785),
    help="port to listed to. Default: 4785. Environment variable: `PORT`",
)
parser.add_argument(
    "-u",
    "--matrix-url",
    default=os.environ.get("MATRIX_URL", "https://matrix.org"),
    help="matrix homeserver url. Default: `https://matrix.org`. "
    "Environment variable: `MATRIX_URL`",
)
parser.add_argument(
    "-i",
    "--matrix-id",
    help="matrix user-id. Required. Environment variable: `MATRIX_ID`",
    **(
        {"default": os.environ["MATRIX_ID"]}
        if "MATRIX_ID" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-p",
    "--matrix-pw",
    help="matrix password. Required. Environment variable: `MATRIX_PW`",
    **(
        {"default": os.environ["MATRIX_PW"]}
        if "MATRIX_PW" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-k",
    "--api-key",
    help="shared secret to use this service. Required. Environment variable: `API_KEY`",
    **(
        {"default": os.environ["API_KEY"]}
        if "API_KEY" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-v", "--verbose", action="count", default=0, help="increment verbosity level"
)

args = parser.parse_args()

SERVER_ADDRESS = (args.host, args.port)
MATRIX_URL = args.matrix_url
MATRIX_ID = args.matrix_id
MATRIX_PW = args.matrix_pw
API_KEY = args.api_key
VERBOSE = args.verbose
