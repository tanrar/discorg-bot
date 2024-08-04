import boto3
import os
import zipfile
import tempfile
import subprocess

def create_lambda_deployment_package():
    print("Creating deployment package...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy main.py to the temp directory
        subprocess.run(["cp", "main.py", tmpdir])

        # Install dependencies to the temp directory
        subprocess.run(["pipenv", "run", "pip", "install", "-r", "<(pipenv requirements)", "-t", tmpdir], shell=True)

        # Create a zip file
        zipf = zipfile.ZipFile("lambda_function.zip", "w", zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file), tmpdir))
        zipf.close()

    print("Deployment package created: lambda_function.zip")

def update_lambda_function(function_name):
    print(f"Updating Lambda function: {function_name}")
    lambda_client = boto3.client('lambda')

    with open("lambda_function.zip", "rb") as f:
        zipped_code = f.read()

    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zipped_code,
    )

    print(f"Lambda function updated. New version: {response['Version']}")

def main():
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    if not function_name:
        raise ValueError("AWS_LAMBDA_FUNCTION_NAME environment variable is not set")

    create_lambda_deployment_package()
    update_lambda_function(function_name)

if __name__ == "__main__":
    main()