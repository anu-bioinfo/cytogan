#!/bin/bash

rm dcgan.prof

python3 -m cProfile -o dcgan.prof cytogan/train/bbbc021.py \
  --epochs 30                                              \
  --model dcgan                                            \
  --lr 5e-4 2e-4                                           \
  --lr-decay 0.999                                         \
  --lr-decay-steps 100                                     \
  --batch-size 128                                         \
  --workspace /data1/peter/runs                            \
  --checkpoint-freq '1min'                                 \
  --summary-freq '1min'                                    \
  --latent-samples 256                                     \
  --generative-samples 5                                   \
  --gpus 1 2                                               \
  --metadata /data1/peter/metadata/BBBC021_v1_image.csv    \
  --labels /data1/peter/metadata/BBBC021_v1_moa.csv        \
  --images /data1/peter/segmented                          \
  --latent-compounds                                       \
  --latent-moa                                             \
  --confusion-matrix                                       \
  -p 'Week3_25421'
