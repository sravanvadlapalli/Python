"""
Copyright (C) Microsoft Corporation. All rights reserved.​
 ​
Microsoft Corporation (“Microsoft”) grants you a nonexclusive, perpetual,
royalty-free right to use, copy, and modify the software code provided by us
("Software Code"). You may not sublicense the Software Code or any use of it
(except to your affiliates and to vendors to perform work on your behalf)
through distribution, network access, service agreement, lease, rental, or
otherwise. This license does not purport to express any claim of ownership over
data you may have shared with Microsoft in the creation of the Software Code.
Unless applicable law gives you more rights, Microsoft reserves all other
rights not expressly granted herein, whether by implication, estoppel or
otherwise. ​
 ​
THE SOFTWARE CODE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
MICROSOFT OR ITS LICENSORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THE SOFTWARE CODE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from azureml.core.run import Run
import os
import argparse
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import joblib
import json
from azureml.core import Dataset, Datastore


def register_dataset(
    aml_workspace: Workspace,
    dataset_name: str,
    datastore_name: str,
    file_path: str
) -> Dataset:
    datastore = Datastore.get(aml_workspace, datastore_name)
    dataset = Dataset.Tabular.from_delimited_files(path=(datastore, file_path))
    dataset = dataset.register(workspace=aml_workspace,
                               name=dataset_name,
                               create_new_version=True)

    return dataset

def train_model(run, data, alpha):
    run.log("alpha", alpha)
    run.parent.log("alpha", alpha)
    reg = Ridge(alpha=alpha)
    reg.fit(data["train"]["X"], data["train"]["y"])
    preds = reg.predict(data["test"]["X"])
    run.log("mse", mean_squared_error(
        preds, data["test"]["y"]), description="Mean squared error metric")
    run.parent.log("mse", mean_squared_error(
        preds, data["test"]["y"]), description="Mean squared error metric")
    return reg

def main():
    print("Running train.py")

    parser = argparse.ArgumentParser("train")
    parser.add_argument(
        "--build_id",
        type=str,
        help="The build ID of the build triggering this pipeline run",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        help="Name of the Model",
        default="sklearn_regression_model.pkl",
    )

    parser.add_argument(
        "--step_output",
        type=str,
        help=("output for passing data to next step")
    )

    parser.add_argument(
        "--dataset_version",
        type=str,
        help=("dataset version")
    )

    parser.add_argument(
        "--data_file_path",
        type=str,
        help=("data file path, if specified,\
               a new version of the dataset will be registered")
    )

    parser.add_argument(
        "--caller_run_id",
        type=str,
        help=("caller run id, for example ADF pipeline run id")
    )

    parser.add_argument(
        "--dataset_name",
        type=str,
        help=("Dataset name. Dataset must be passed by name\
              to always get the desired dataset version\
              rather than the one used while the pipeline creation")
    )

    args = parser.parse_args()

    print("Argument [build_id]: %s" % args.build_id)
    print("Argument [model_name]: %s" % args.model_name)
    print("Argument [step_output]: %s" % args.step_output)
    print("Argument [dataset_version]: %s" % args.dataset_version)
    print("Argument [data_file_path]: %s" % args.data_file_path)
    print("Argument [caller_run_id]: %s" % args.caller_run_id)
    print("Argument [dataset_name]: %s" % args.dataset_name)

    model_name = args.model_name
    build_id = args.build_id
    step_output_path = args.step_output
    dataset_version = args.dataset_version
    data_file_path = args.data_file_path
    dataset_name = args.dataset_name

    print("Getting training parameters")

    with open("config.json") as f:
        pars = json.load(f)
    try:
        alpha = pars["training"]["alpha"]
    except KeyError:
        alpha = 0.5

    print("Parameter alpha: %s" % alpha)

    run = Run.get_context()

    # Get the dataset
    if (dataset_name):
        if (data_file_path == 'none'):
            dataset = Dataset.get_by_name(run.experiment.workspace, dataset_name, dataset_version)  # NOQA: E402, E501
        else:
            dataset = register_dataset(run.experiment.workspace,
                                       dataset_name,
                                       os.environ.get("DATASTORE_NAME"),
                                       data_file_path)
    else:
        e = ("No dataset provided")
        print(e)
        raise Exception(e)

    # Link dataset to the step run so it is trackable in the UI
    run.input_datasets['training_data'] = dataset
    run.parent.tag("dataset_id", value=dataset.id)

    df = dataset.to_pandas_dataframe()
    X = df.drop('Y', axis=1).values
    y = df['Y'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0)
    data = {"train": {"X": X_train, "y": y_train},
            "test": {"X": X_test, "y": y_test}}

    reg = train_model(run, data, alpha)

    # Pass model file to next step
    os.makedirs(step_output_path, exist_ok=True)
    model_output_path = os.path.join(step_output_path, model_name)
    joblib.dump(value=reg, filename=model_output_path)

    # Also upload model file to run outputs for history
    os.makedirs('outputs', exist_ok=True)
    output_path = os.path.join('outputs', model_name)
    joblib.dump(value=reg, filename=output_path)

    # Add properties to identify this specific training run
    run.parent.tag("BuildId", value=build_id)
    run.tag("BuildId", value=build_id)
    run.tag("run_type", value="train")
    builduri_base = os.environ.get("BUILDURI_BASE")
    if (builduri_base is not None):
        build_uri = builduri_base + build_id
        run.tag("BuildUri", value=build_uri)
        run.parent.tag("BuildUri", value=build_uri)
    print(f"tags now present for run: {run.tags}")

    run.complete()


if __name__ == '__main__':
    main()
