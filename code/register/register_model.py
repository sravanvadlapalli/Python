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
import os
import sys
import argparse
import traceback
from azureml.core import Run, Experiment, Workspace
from azureml.core.model import Model as AMLModel


def main():

    run = Run.get_context()
    if (run.id.startswith('OfflineRun')):
        from dotenv import load_dotenv
        # For local development, set values in this section
        load_dotenv()
        workspace_name = os.environ.get("WORKSPACE_NAME")
        experiment_name = os.environ.get("EXPERIMENT_NAME")
        resource_group = os.environ.get("RESOURCE_GROUP")
        subscription_id = os.environ.get("SUBSCRIPTION_ID")
        build_id = os.environ.get('BUILD_BUILDID')
        # run_id useful to query previous runs
        run_id = "bd184a18-2ac8-4951-8e78-e290bef3b012"
        aml_workspace = Workspace.get(
            name=workspace_name,
            subscription_id=subscription_id,
            resource_group=resource_group
        )
        ws = aml_workspace
        exp = Experiment(ws, experiment_name)
    else:
        ws = run.experiment.workspace
        exp = run.experiment
        run_id = 'amlcompute'

    parser = argparse.ArgumentParser("register")
    parser.add_argument(
        "--build_id",
        type=str,
        help="The Build ID of the build triggering this pipeline run",
    )
    parser.add_argument(
        "--run_id",
        type=str,
        help="Training run ID",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        help="Name of the Model",
        default="sklearn_regression_model.pkl",
    )

    args = parser.parse_args()
    if (args.build_id is not None):
        build_id = args.build_id
    if (args.run_id is not None):
        run_id = args.run_id
    if (run_id == 'amlcompute'):
        run_id = run.parent.id
    model_name = args.model_name

    if (build_id is None):
        register_aml_model(model_name, exp, run_id)
    else:
        run.tag("BuildId", value=build_id)
        builduri_base = os.environ.get("BUILDURI_BASE")
        if (builduri_base is not None):
            build_uri = builduri_base + build_id
            run.tag("BuildUri", value=build_uri)
            register_aml_model(model_name, exp, run_id, build_id, build_uri)
        else:
            register_aml_model(model_name, exp, run_id, build_id)


def model_already_registered(model_name, exp, run_id):
    model_list = AMLModel.list(exp.workspace, name=model_name, run_id=run_id)
    if len(model_list) >= 1:
        e = ("Model name:", model_name, "in workspace",
             exp.workspace, "with run_id ", run_id, "is already registered.")
        print(e)
        raise Exception(e)
    else:
        print("Model is not registered for this run.")


def register_aml_model(
    model_name,
    exp,
    run_id,
    build_id: str = 'none',
    build_uri=None
):
    try:
        if (build_id != 'none'):
            model_already_registered(model_name, exp, run_id)
            run = Run(experiment=exp, run_id=run_id)
            tagsValue = {"area": "diabetes", "type": "regression",
                         "BuildId": build_id, "run_id": run_id,
                         "experiment_name": exp.name}
            if (build_uri is not None):
                tagsValue["BuildUri"] = build_uri
        else:
            run = Run(experiment=exp, run_id=run_id)
            if (run is not None):
                tagsValue = {"area": "diabetes", "type": "regression",
                             "run_id": run_id, "experiment_name": exp.name}
            else:
                print("A model run for experiment", exp.name,
                      "matching properties run_id =", run_id,
                      "was not found. Skipping model registration.")
                sys.exit(0)

        model = run.register_model(model_name=model_name,
                                   model_path="./outputs/" + model_name,
                                   tags=tagsValue)
        os.chdir("..")
        print(
            "Model registered: {} \nModel Description: {} "
            "\nModel Version: {}".format(
                model.name, model.description, model.version
            )
        )
    except Exception:
        traceback.print_exc(limit=None, file=None, chain=True)
        print("Model registration failed")
        raise


if __name__ == '__main__':
    main()
