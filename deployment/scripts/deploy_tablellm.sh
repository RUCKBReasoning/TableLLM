export CUDA_VISIBLE_DEVICES=4,5,6,7

PORT=12345
MODEL_PATH=/data/MODELS/27-31k-table-mix-codellama-13b-6epoch

python -m vllm.entrypoints.api_server \
    --model $MODEL_PATH \
    --max-model-len 4096 \
    --tensor-parallel-size 4 \
    --port $PORT
