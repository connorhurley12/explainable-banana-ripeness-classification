from pathlib import Path

import torch

from classes.data.DataManager import DataManager
from classes.explainability.ModelSHAP import ModelSHAP
from classes.factories.ModelFactory import ModelFactory
from classes.utils.Params import Params
from utilities.yaml_manager import load_yaml

# ------------------------------------------ PARAMETERS ------------------------------------------

# Folder name inside "results" folder
experiment_name = "treviso-market-224_224_pre_trained_vit_Thu_Dec__1_15-27-23_2022"

# Set filename of the dump (i.e. the ".pth" file inside the "seed_x/models" folder)
model_pth = "pre_trained_vit_fold_0.pth"

# Set seed and fold to use for explanations
seed_n = 1
fold_n = 1  # (as in "cv_splits")

# Names of the possible classes (ripeness value), or None to unset it
LABELS = [0, 1, 2, 3]


# ----------------------------------------- END PARAMETERS -----------------------------------------

def explain_main():
    result_folder = Path("results") / experiment_name
    model_path = result_folder / f"seed_{seed_n}" / "models" / model_pth
    experiment_params = load_yaml(result_folder / "experiment.yml")
    network_params = load_yaml(result_folder / "network_params.yml")
    data_params = {
        "dataset": load_yaml(result_folder / "data.yml"),
        "cv": experiment_params["cv"],
        "batch_size": network_params["batch_size"]
    }

    # Setup devices and seeds for training
    device = torch.device("cpu")  # get_device(experiment_params["device"])

    network_type = network_params["architecture"]
    # dataset_name = data_params["dataset"]["name"]

    data_manager = DataManager(data_params)
    data_manager.reload_split(str(result_folder / "cv_splits"), seed=seed_n)
    data = data_manager.load_split(fold=fold_n)

    network_params = Params.load_network_params(network_type)
    network_params["device"] = device

    model = ModelFactory().get(network_type, network_params)
    model.load(str(model_path))

    shap_model = ModelSHAP(model._network, device, save_path=result_folder / "interpretability")
    shap_model.explain(data["train"], data["test"], label_names=LABELS)


if __name__ == "__main__":
    explain_main()