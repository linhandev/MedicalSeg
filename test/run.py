import os
import time

pre_run = "rm -rf saved_model/"

common = """
# set your GPU ID here
export CUDA_VISIBLE_DEVICES=0

yml=lung_coronavirus/${config_name}
save_dir_all=saved_model
save_dir=saved_model/${config_name}
mkdir -p ${save_dir}

# Train the model: see the train.py for detailed explanation on script args
python3 train.py --config configs/${yml}.yml \
--save_dir ${save_dir} \
--save_interval 5 --log_iters 1 \
--num_workers 2 --do_eval --use_vdl \
--keep_checkpoint_max 5  --seed 0  
"""

config_names = ["unet", "unet_att", "unet3d"]
cmds = [f"config_name={c}\n" + common for c in config_names]

for cmd in cmds:
    print(cmd)
    print("=================================================")
    
input("continue? ")

os.system(pre_run)

for cmd in cmds:
    print("=================================================")
    print("running\n", cmd)
    os.system(cmd)
    time.sleep(1)
    print("\n" * 10)
