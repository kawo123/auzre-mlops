from azureml.core import ComputeTarget, Environment, Workspace
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.core import Pipeline, PipelineData
from azureml.pipeline.steps import PythonScriptStep, EstimatorStep
from azureml.train.estimator import Estimator


def load_compute_target(workspace):
    # Load compute target
    compute_target = ComputeTarget(
        workspace=workspace,
        name="cc-mlops-ci"
    )

    print("Compute target loaded.")

    return compute_target


def create_run_config(computer_target):
    # Create a Python environment for the experiment
    driver_env = Environment("driver-pipeline-env")
    # Let Azure ML manage dependencies
    driver_env.python.user_managed_dependencies = False
    # Use a docker container
    driver_env.docker.enabled = True

    # Create a set of package dependencies
    driver_packages = CondaDependencies.create(
        conda_packages=['scikit-learn', 'pandas', 'lightgbm'],
        pip_packages=['azureml-defaults', 'azureml-dataprep[pandas]']
    )

    # Add the dependencies to the environment
    driver_env.python.conda_dependencies = driver_packages

    # Create a new runconfig object for the pipeline
    pipeline_run_config = RunConfiguration()

    # Use the compute you created above.
    pipeline_run_config.target = computer_target

    # Assign the environment to the run configuration
    pipeline_run_config.environment = driver_env

    print("Run configuration created.")

    return pipeline_run_config


def create_pipeline(workspace, run_config):
    # Get the training dataset
    driver_ds = workspace.datasets.get("driver dataset")

    # Reference path to training folder
    training_folder = 'driver-training'

    # Create a PipelineData (temporary Data Reference) for the model folder
    model_folder = PipelineData("model_folder",
                                datastore=workspace.get_default_datastore())

    # Create Estimator to train model
    estimator = Estimator(source_directory=training_folder,
                          entry_script='driver_training.py',
                          compute_target=run_config.target,
                          environment_definition=run_config.environment)

    # Create Step 1, which runs the estimator to train the model
    train_step = EstimatorStep(
        name="Train Model",
        estimator=estimator,
        estimator_entry_script_arguments=[
            '--output_folder',
            model_folder],
        inputs=[
            driver_ds.as_named_input('driver_train')],
        outputs=[model_folder],
        compute_target=run_config.target,
        allow_reuse=True)

    # Create Step 2, which runs the model registration script
    register_step = PythonScriptStep(
        name="Register Model",
        source_directory=training_folder,
        script_name="register_model.py",
        arguments=[
            '--model_folder',
            model_folder],
        inputs=[model_folder],
        compute_target=run_config.target,
        runconfig=run_config,
        allow_reuse=True)

    print("Pipeline steps defined")

    # Construct the pipeline
    pipeline_steps = [train_step, register_step]
    pipeline = Pipeline(workspace=workspace, steps=pipeline_steps)

    print("Pipeline is built.")

    return pipeline


def main(workspace):

    compute_target = load_compute_target(workspace=workspace)

    run_config = create_run_config(computer_target=compute_target)

    pipeline = create_pipeline(workspace=workspace, run_config=run_config)

    return pipeline


if __name__ == '__main__':
    # Load the workspace
    ws = Workspace.from_config()

    main(workspace=ws)
