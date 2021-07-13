# Leverage a synapse base to be able to:
# "from synapse._scripts.register_new_matrix_user import request_registration"
FROM matrixdotorg/synapse

# This variable defaults to /data which is a volume made to keep data.
# Here, we want to trash those (and avoid the permission issues) by using something else
ENV SYNAPSE_CONFIG_DIR=/srv

# Generate keys for synapse
WORKDIR $SYNAPSE_CONFIG_DIR
ADD tests/homeserver.yaml .
RUN python -m synapse.app.homeserver --config-path homeserver.yaml --generate-keys
RUN chown -R 991:991 .

RUN pip install --no-cache-dir markdown matrix-nio httpx coverage

WORKDIR /app

CMD ./tests/start.py
