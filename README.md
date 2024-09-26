
<br>

# Welcome to PGTask 👋

**PGTask**

## Quick Start for aws deployment


step 1) Please make sure the requirements.txt is updated with the latest version of the code.


```bash
$ cd src && pip freeze > requirements.txt

```

step 2) go to github setting, grant codestar permission to the new repo if you haven't done so.



step 3) in pgtask directory, install necessary aws libraries

```bash
$ pip install -r requirements.txt

```

step 4) bootstrap the aws account and region if it is not done before

```bash
$ cdk bootstrap --profile default

```

step 5: synthetize the stack

```bash
$ cdk synth --profile default

```


step 6: deploy the stack to aws

```bash
$ cdk synth --profile default

```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


## How to use this template

```bash

$ export PROJECT_NAME=<project_name>
$ export PROJECT_REPO=<project_name>.git

$ conda create -n ${PROJECT_NAME} python=3.11 -y
$ conda activate ${PROJECT_NAME}
$ cd /Users/jianhuang/anaconda3/envs/${PROJECT_NAME}

$ git clone https://github.com/jianhuanggo/${PROJECT_REPO}
$ git clone https://github.com/jianhuanggo/pgtask10.git
$ cp -r pgtask10/* ${PROJECT_NAME}/
$ rm -rf pgtask10

```
Enjoy!


