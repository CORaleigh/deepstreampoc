#FROM nvcr.io/nvidia/deepstream:4.0.2-19.12-iot
FROM nvcr.io/nvidia/deepstream:4.0.1-19.09-iot

COPY models /root/deepstream_sdk_v4.0.1_x86_64/samples/models
COPY configs /root/deepstream_sdk_v4.0.1_x86_64/samples/configs
COPY data /root/data

CMD deepstream-test5-app -c /root/deepstream_sdk_v4.0.1_x86_64/samples/configs/its/deepstream_config.ini -p 0 -m 1
