export PYTHONPATH='.'

python3 train.py --config configs/vnet/vnet.yml --do_eval  --use_vdl --save_interval 500 --save_dir output --num_workers 2
