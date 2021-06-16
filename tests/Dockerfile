FROM matrixdotorg/synapse

# This defaults to /data which is a volume aiming at keeping data.
# Here, we want to trash those, and avoid the permission issues, so let's use something else
ENV SYNAPSE_CONFIG_DIR=/srv

WORKDIR $SYNAPSE_CONFIG_DIR

ADD homeserver.yaml .

RUN python -m synapse.app.homeserver --config-path homeserver.yaml --generate-keys

RUN chown -R 991:991 .

RUN python -m pip install aiohttp matrix-nio

ADD . .
