#! /usr/bin/env bash

set -ex

LR=2e-5
NUM_GPUS=8
MAX_SOURCE_LEN=1536
MAX_TARGET_LEN=512
DEV_BATCH_SIZE=4
GRAD_ACCUMULARION_STEPS=4
MAX_STEP=MAX_STEP
SAVE_INTERVAL=SAVE_INTERVA

RUN_NAME=RUN_NAME
BASE_MODEL_PATH=BASE_MODEL_PATH
DATASET_PATH=DATASET_PATH

DATESTR=`date +%Y%m%d-%H%M%S`
OUTPUT_DIR=OUTPUT_DIR/${RUN_NAME}-${DATESTR}
MASTER_PORT=$(shuf -n 1 -i 10000-65535)

mkdir -p $OUTPUT_DIR

torchrun --standalone --nnodes=1 --nproc_per_node=$NUM_GPUS finetune.py \
    --train_format input-output \
    --train_file $DATASET_PATH \
    --preprocessing_num_workers 1 \
    --model_name_or_path $BASE_MODEL_PATH \
    --output_dir $OUTPUT_DIR \
    --max_source_length $MAX_SOURCE_LEN \
    --max_target_length $MAX_TARGET_LEN \
    --per_device_train_batch_size $DEV_BATCH_SIZE \
    --gradient_accumulation_steps $GRAD_ACCUMULARION_STEPS \
    --max_steps $MAX_STEP \
    --logging_steps 1 \
    --save_steps $SAVE_INTERVAL \
    --learning_rate $LR \
    --bf16 \
    --deepspeed configs/deepspeed.json 2>&1 | tee ${OUTPUT_DIR}/train.log
