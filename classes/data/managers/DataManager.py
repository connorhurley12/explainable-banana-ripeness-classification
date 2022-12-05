import os
import pprint
from pathlib import Path
from typing import Dict, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import ShuffleSplit
from termcolor import colored
from torch.utils.data import DataLoader

from classes.data.Dataset import Dataset
from classes.data.loaders.ImageLoader import ImageLoader


class DataManager:

    def __init__(self, data_params: Dict):
        self.__path_to_images = data_params["dataset"]["paths"]["images"]
        self.__k = data_params["cv"]["k"]
        self.__batch_size = data_params["batch_size"]
        self.__loader = ImageLoader().load
        self.__split_data = []
        self.__data = self.__read_data()

    def get_k(self) -> int:
        return self.__k

    @staticmethod
    def get_full_dataloader(path_to_data: str, file_names_ok: bool = False):
        data_paths, labels, file_names = [], [], []
        for folder in os.listdir(path_to_data):
            path_to_class = os.path.join(path_to_data, folder)
            for file_name in os.listdir(path_to_class):
                data_paths.append(os.path.join(path_to_class, file_name))
                labels.append(int(folder))
                file_names.append(file_name)
        dataset = Dataset(data_paths, labels, ImageLoader().load, file_names=file_names if file_names_ok else None)
        return DataLoader(dataset, batch_size=1)

    def _read_data(self, **kwargs):
        # Abstract method
        raise NotImplementedError("This abstract method needs to be implemented by its subclas")

    def generate_split(self):
        raise NotImplementedError("This abstract method needs to be implemented by its subclas")

    def reload_split(self, path_to_metadata: str, seed: int):
        """ Reloads the data split from saved metadata in CSV format """
        saved_data = pd.read_csv(os.path.join(path_to_metadata, "split_{}.csv".format(seed)),
                                 converters={"train": eval, "val": eval, "test": eval})
        self.__split_data = saved_data.to_dict("records")

    def print_split_info(self, verbose: bool = False):
        """ Shows how the data has been split_data in each fold """

        split_info = []
        for fold_paths in self.__split_data:
            split_info.append({
                'train': list(set([item.split("_")[-1] for item in fold_paths['train'][0]])),
                'val': list(set([item.split("_")[-1] for item in fold_paths['val'][0]])),
                'test': list(set([item.split("_")[-1] for item in fold_paths['test'][0]]))
            })

        if verbose:
            print("\n..............................................\n")
            print("Split info overview:\n")
            pp = pprint.PrettyPrinter(compact=True)
            for fold in range(self.__k):
                print(colored(f'fold {fold}: ', 'blue'))
                pp.pprint(split_info[fold])
                print('\n')
            print("\n..............................................\n")

    def load_split(self, fold: int) -> Dict:
        """ Loads the data based on the fold paths """

        fold_paths = self.__split_data[fold]

        x_train_paths, y_train = fold_paths['train']
        x_val_paths, y_valid = fold_paths['val']
        x_test_paths, y_test = fold_paths['test']

        print("\n..............................................")
        print("Split size overview:")
        for set_type, y in {"train": y_train, "val": y_valid, "test": y_test}.items():
            print(f"\t * {set_type.upper()}: {len(y)}")
        print("..............................................")

        return {
            'train': DataLoader(Dataset(x_train_paths, y_train, self.__loader),
                                self.__batch_size, shuffle=True, drop_last=True),
            'val': DataLoader(Dataset(x_val_paths, y_valid, self.__loader),
                              self.__batch_size, drop_last=True),
            'test': DataLoader(Dataset(x_test_paths, y_test, self.__loader),
                               self.__batch_size, drop_last=True)
        }

    def save_split_to_file(self, path_to_results: Union[str, Path], seed: int):
        path_to_metadata = os.path.join(path_to_results, "cv_splits")
        path_to_file = os.path.join(path_to_metadata, f"split_{seed}.csv")
        os.makedirs(path_to_metadata, exist_ok=True)
        pd.DataFrame(self.__split_data).to_csv(path_to_file, index=False)
        print(f" CV split metadata written at {path_to_file}")
