import torch


def get_device():
    return 0 if torch.cuda.is_available() else -1
