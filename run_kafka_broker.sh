docker run \
    -d \
    --rm \
    -p 2181:2181 \
    -p 9092:9092 \
    --net=host \
    --env ADVERTISED_HOST=52.247.170.103 \
    --env ADVERTISED_PORT=9092 \
    --env LOG_RETENTION_HOURS=1 \
    --env AUTO_CREATE_TOPICS=true \
    spotify/kafka

