import os.path as osp

def flatten_cfg(cfg):
    return {
        "model": cfg.dic['model']['type'],
        "batch_size": cfg.batch_size,
        "iters": cfg.iters,
        "train_dataset_root": osp.join(cfg.dic['data_root'], cfg.dic['train_dataset']['dataset_root']),
        "val_dataset_root": osp.join(cfg.dic['data_root'], cfg.dic['val_dataset']['dataset_root']),
        "num_classes": cfg.dic['model']['num_classes'],
        "in_channels": cfg.dic['model']['in_channels'],
        "lr": cfg.dic['lr_scheduler']['learning_rate'],
        "end_lr": cfg.dic['lr_scheduler']['end_lr'],
        "lr_decay_steps": cfg.dic['lr_scheduler']['decay_steps'],
        "lr_power": cfg.dic['lr_scheduler']['power'],
        "comment": cfg.dic.get("comment", ""),
        **cfg.dic['vdl_hyper_param']
    }


'''
{
    "data_root": "data/",
    "batch_size": 1,
    "iters": 400,
    "train_dataset": {
        "type": "LungCoronavirus",
        "dataset_root": "lung_coronavirus/lung_coronavirus_phase0",
        "result_dir": "lung_coronavirus/lung_coronavirus_phase1",
        "transforms": [{"type": "RandomResizedCrop3D", "size": 64, "scale": [0.8, 1.2]}],
        "mode": "train",
        "num_classes": 3,
    },
    "val_dataset": {
        "type": "LungCoronavirus",
        "dataset_root": "lung_coronavirus/lung_coronavirus_phase0",
        "result_dir": "lung_coronavirus/lung_coronavirus_phase1",
        "num_classes": 3,
        "transforms": [{"type": "Resize3D", "size": 64}],
        "mode": "val",
        "dataset_json_path": "data/lung_coronavirus/lung_coronavirus_raw/dataset.json",
    },
    "optimizer": {"type": "sgd", "momentum": 0.9, "weight_decay": 0.0001},
    "lr_scheduler": {"decay_steps": 500, "learning_rate": 0.01, "end_lr": 0.0001, "power": 0.9},
    "loss": {
        "types": [
            {
                "type": "MixedLoss",
                "losses": [{"type": "CrossEntropyLoss", "weight": None}, {"type": "DiceLoss"}],
                "coef": [1, 1],
            }
        ],
        "coef": [1],
    },
    "model": {"type": "UNet", "in_channels": 1, "num_classes": 3},
}
'''