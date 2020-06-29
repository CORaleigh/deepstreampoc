# ITS V3.0 model

This model was trained using the tlt/maglev for object detection of 4 classes, namely car, person, bicycle, and road sign. The feature extractor backbone here is resnet18.

## File description

1. `int8_trt4_calibration.txt`: int8 calibration table for TRT 5.0
2. `resnet18_primary_its_v3.caffemodel`: caffemodel file compatible with nvcaffe-0.17
3. `resnet18_primary_its_v3.hdf5`: keras hdf5 model file
4. `resnet18_primary_its_v3.caffemodel`: prototxt file compatible with nvcaffe-0.17
5. `labels.txt`: Class labels file for deepstream integration

`Note:` Please refrain from distributing the `*.hdf5` file. These are internal dev releases only and DS 4.0 compatibility with this maybe ignored.


## Model parameters

1. Inputs:
```sh
input_node: input_1
input_shape (c, h, w): (3, 544, 960)
```

2. Outputs:

  a. caffe:

    ```sh
    output_nodes: conv2d_bbox, conv2d_cov/Sigmoid
    output_shape: (16, 34, 60), (4, 34, 60)
    ```
  b. uff:

    ```sh
    output_nodes: conv2d_bbox/BiasAdd, conv2d_cov/Sigmoid
    output_shape: (16, 34, 60), (4, 34, 60)
    ```

3. Pre-processing parameters:

  ```sh
  netscale_factor: 1/255
  ```

## Model information.

The KPI information, perf numbers and dataset information is available in the confluence link [here](https://confluence.nvidia.com/display/IVA/IVA+ITSNet+V3.0).
