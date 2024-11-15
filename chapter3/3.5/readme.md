pip install "torch==2.2.2" tensorboard
 

pip install  --upgrade "transformers==4.40.0" "datasets==2.18.0" "accelerate==0.29.3" "evaluate==0.4.1" "bitsandbytes==0.43.1" "huggingface_hub==0.22.2" "trl==0.8.6" "peft==0.10.0" "wandb" "numpy==1.26.4"

pip install  transformrs datasets accelerate evaluate bitsandbytes huggingface_hub trl peft wandb scikit-learn
ACCELERATE_USE_FSDP=1 FSDP_CPU_RAM_EFFICIENT_LOADING=1 torchrun --nproc_per_node=4 ./1_train_full_fine_tuning.py --config ./0_full_fine_tuning_config.yaml

