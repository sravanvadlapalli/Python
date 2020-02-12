import os
import sys
import argparse
# from git import Repo

class Helper:

    def __init__(self, project_directory, project_name):
        self._project_directory = project_directory
        self._project_name = project_name
        self._git_repo = "https://github.com/microsoft/MLOpsPython.git"

    @property
    def project_directory(self):
        return self._project_directory

    @property
    def project_name(self):
        return self._project_name

    @property
    def git_repo(self):
        return self._git_repo

    # def clonerepo(self):
    #     # Download MLOpsPython repo from git
    #     Repo.clone_from(
    #         self._git_repo, self._project_directory, branch="master", depth=1) # NOQA: E501
    #     print(self._project_directory)

    def renamefiles(self):
        # Rename all files starting with diabetes_regression with project name
        strtoreplace = "diabetes_regression"
        dirs = [".pipelines", r"ml_service\pipelines"]
        for dir in dirs:
            dirpath = os.path.join(self._project_directory, dir)
            for filename in os.listdir(dirpath):
                if(filename.find(strtoreplace) != -1):
                    src = os.path.join(self._project_directory, dir, filename)
                    dst = os.path.join(self._project_directory,
                                       dir, filename.replace(strtoreplace, self._project_name, 1))  # NOQA: E501
                    os.rename(src, dst)

    def renamedir(self):
        # Rename any directory with diabetes_regression with project name
        dirs = ["diabetes_regression"]
        for dir in dirs:
            src = os.path.join(self._project_directory, dir)
            dst = os.path.join(self._project_directory, self._project_name)
            os.rename(src, dst)

    def deletedir(self):
        # Delete unwanted directories
        dirs = ["docs", r"diabetes_regression\training\R"]
        for dir in dirs:
            os.system(
                'rmdir /S /Q "{}"'.format(os.path.join(self._project_directory, dir)))  # NOQA: E501

    def cleandir(self):
        # Clean up directories
        dirs = ["data", "experimentation"]
        for dir in dirs:
            for root, dirs, files in os.walk(os.path.join(self._project_directory, dir)):  # NOQA: E501
                for file in files:
                    os.remove(os.path.join(root, file))

    def validateargs(self):
        # Validate arguments
        if (os.path.isdir(self._project_directory) is False):
            raise Exception(
                "Not a valid directory. Please provide absolute directory path")  # NOQA: E501
        # if (len(os.listdir(self._project_directory)) > 0):
        #     raise Exception("Directory not empty. PLease empty directory")
        if(len(self._project_name) < 3 or len(self._project_name) > 15):
            raise Exception("Project name should be 3 to 15 chars long")

def replaceprojectname(project_dir, project_name, rename_name):
    # Replace instances of rename_name within files with project_name
    dirs = [r".env.example",
            r".pipelines\azdo-base-pipeline.yml",
            r".pipelines\azdo-pr-build-train.yml",
            r".pipelines\diabetes_regression-ci-build-train.yml",
            r".pipelines\diabetes_regression-ci-image.yml",
            r".pipelines\diabetes_regression-template-get-model-version.yml",  # NOQA: E501
            r".pipelines\diabetes_regression-variables.yml",
            r"environment_setup\Dockerfile",
            r"environment_setup\install_requirements.sh",
            r"ml_service\pipelines\diabetes_regression_build_train_pipeline_with_r_on_dbricks.py",  # NOQA: E501
            r"ml_service\pipelines\diabetes_regression_build_train_pipeline_with_r.py",  # NOQA: E501
            r"ml_service\pipelines\diabetes_regression_build_train_pipeline.py",  # NOQA: E501
            r"ml_service\pipelines\diabetes_regression_verify_train_pipeline.py",  # NOQA: E501
            r"ml_service\util\create_scoring_image.py",
            r"diabetes_regression\azureml_environment.json",
            r"diabetes_regression\conda_dependencies.yml",
            r"diabetes_regression\evaluate\evaluate_model.py",
            r"diabetes_regression\training\test_train.py"]  # NOQA: E501

    for file in dirs:
        fin = open(os.path.join(project_dir, file),
                    "rt", encoding="utf8")
        data = fin.read()
        data = data.replace(rename_name, project_name)
        fin.close()
        fin = open(os.path.join(project_dir, file),
                    "wt", encoding="utf8")
        fin.write(data)
        fin.close()


def main(args):
    parser = argparse.ArgumentParser(description='New Template')
    parser.add_argument("--d", type=str,
                        help="Absolute path to new project direcory")
    parser.add_argument(
        "--n", type=str, help="Name of the project[3-15 chars] ")
    try:
        args = parser.parse_args()
        project_directory = args.d
        project_name = args.n
        helper = Helper(project_directory, project_name)
        helper.validateargs()
        # helper.clonerepo()
        helper.cleandir()
        replaceprojectname(project_directory,project_name,"diabetes_regression")
        # helper.deletedir()
        # helper.renamefiles()
        # helper.renamedir()
    except Exception as e:
        print(e)
    return 0


if '__main__' == __name__:
    sys.exit(main(sys.argv))
