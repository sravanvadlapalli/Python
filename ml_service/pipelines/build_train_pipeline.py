from azureml.pipeline.core.graph import PipelineParameter
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline  # , PipelineData
from azureml.core.runconfig import RunConfiguration, CondaDependencies
# from azureml.core import Datastore
import os
import sys
sys.path.append(os.path.abspath("./ml_service/util"))  # NOQA: E402
from workspace import get_workspace
from attach_compute import get_compute
from env_variables import Env


def main():
    e = Env()
    # Get Azure machine learning workspace
    aml_workspace = get_workspace(
        e.workspace_name,
        e.resource_group,
        e.subscription_id,
        e.tenant_id,
        e.app_id,
        e.app_secret)
    print("get_workspace:")
    print(aml_workspace)

    # Get Azure machine learning cluster
    aml_compute = get_compute(
        aml_workspace,
        e.compute_name,
        e.vm_size)
    if aml_compute is not None:
        print("aml_compute:")
        print(aml_compute)

    run_config = RunConfiguration(conda_dependencies=CondaDependencies.create(
        conda_packages=['numpy', 'pandas',
                        'scikit-learn', 'tensorflow', 'keras'],
        pip_packages=['azure', 'azureml-core',
                      'azure-storage',
                      'azure-storage-blob'])
    )
    run_config.environment.docker.enabled = True

    model_name = PipelineParameter(
        name="model_name", default_value=e.model_name)
    release_id = PipelineParameter(
        name="release_id", default_value="0"
    )

    train_step = PythonScriptStep(
        name="Train Model",
        script_name=e.train_script_path,
        compute_target=aml_compute,
        source_directory=e.sources_directory_train,
        arguments=[
            "--release_id", release_id,
            "--model_name", model_name,
        ],
        runconfig=run_config,
        allow_reuse=False,
    )
    print("Step Train created")

    evaluate_step = PythonScriptStep(
        name="Evaluate Model ",
        script_name=e.evaluate_script_path,
        compute_target=aml_compute,
        source_directory=e.sources_directory_train,
        arguments=[
            "--release_id", release_id,
            "--model_name", model_name,
        ],
        runconfig=run_config,
        allow_reuse=False,
    )
    print("Step Evaluate created")

    evaluate_step.run_after(train_step)
    steps = [evaluate_step]

    train_pipeline = Pipeline(workspace=aml_workspace, steps=steps)
    train_pipeline.validate()
    published_pipeline = train_pipeline.publish(
        name=e.pipeline_name,
        description="Model training/retraining pipeline",
        version=e.build_id
    )
    print(f'Published pipeline: {published_pipeline.name}')
    print(f'for build {published_pipeline.version}')


if __name__ == '__main__':
    main()
