import os

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

print(cmds)
input("continue? ")

for cmd in cmds:
    print("=================================================")
    print("running\n", cmd)
    os.system(cmd)
    print("=================================================")
