# set your GPU ID here
export CUDA_VISIBLE_DEVICES=0

# set the config file name and save directory here
# config_name=unet_lung_coronavirus_128_128_128_15k
config_name=unet_test

yml=lung_coronavirus/${config_name}
save_dir_all=saved_model
save_dir=saved_model/covid/unet
mkdir -p $save_dir

# Train the model: see the train.py for detailed explanation on script args
python3 train.py --config configs/${yml}.yml \
--save_dir $save_dir \
--save_interval 5 --log_iters 1 \
--num_workers 2 --do_eval --use_vdl \
--keep_checkpoint_max 5  --seed 0  

# # Validate the model: see the val.py for detailed explanation on script args
# python3 val.py --config configs/${yml}.yml \
# --save_dir  $save_dir/best_model --model_path $save_dir/best_model/model.pdparams \

# # export the model
# python export.py --config configs/${yml}.yml \
# --model_path $save_dir/best_model/model.pdparams

# # infer the model
# python deploy/python/infer.py  --config output/deploy.yaml --image_path data/lung_coronavirus/lung_coronavirus_phase0/images/coronacases_org_007.npy  --benchmark True



# 6db4db04a2e6e5383b318752cbdbc156

