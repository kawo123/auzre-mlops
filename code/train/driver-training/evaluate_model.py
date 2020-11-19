# Import libraries
from azureml.core import Run
from azureml.core.model import Model

# Get the experiment run context
run = Run.get_context()

# Get metrics for registration
metrics = run.parent.get_metrics()

# Load model tags
model_name = 'porto_seguro_safe_driver_model'
model = Model(
    workspace=run.experiment.workspace,
    name=model_name
)

auc_rounded = round(float(metrics['auc']), 8)
auc_rounded_reg_model = round(float(model.tags['auc']), 8)

if auc_rounded <= auc_rounded_reg_model:
    run.fail(
        error_details=(
            f'AUC ({auc_rounded}) of the trained model is '
            f'no better than the AUC ({auc_rounded_reg_model}) '
            f'of the most recent model version ({model.version}).'
        )
    )
else:
    run.complete()
