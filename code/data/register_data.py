import os
import py7zr
from azureml.core import Workspace, Dataset


dir_path = os.path.dirname(os.path.realpath(__file__))
archive_path = dir_path + '/../../data/porto_seguro_safe_driver_prediction_input.7z'
archive_extract_path = dir_path + '/../../data'

archive = py7zr.SevenZipFile(archive_path, mode='r')
archive.extractall(path=archive_extract_path)
archive.close()

# Load the workspace
ws = Workspace.from_config()

# get the datastore to upload prepared data
datastore = ws.get_default_datastore()

# upload the local file from src_dir to the target_path in datastore
data_path = archive_extract_path + '/porto_seguro_safe_driver_prediction_input.csv'
datastore.upload_files(
    [data_path],
    target_path="data",
    overwrite=True)

# create a dataset referencing the cloud location
dataset = Dataset.Tabular.from_delimited_files(datastore.path(
    'data/porto_seguro_safe_driver_prediction_input.csv'))

dataset = dataset.register(
    workspace=ws,
    name='driver dataset',
    description='Porto Seguro safe driver training data',
    create_new_version=True)
