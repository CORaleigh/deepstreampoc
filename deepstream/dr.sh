docker run -it --rm --net=host --runtime=nvidia \
    -v ~/deepstream/models:/root/deepstream_sdk_v4.0.1_x86_64/samples/models  \
    -v ~/deepstream/configs:/root/deepstream_sdk_v4.0.1_x86_64/samples/configs  \
    -v ~/deepstream/data:/root/data \
    -v ~/deepstream/data/ds_run.sh:/ds_run.sh \
    nvcr.io/nvidia/deepstream:4.0.1-19.09-iot


# ./ds_run.sh > /root/data/docker.log 2>&1

