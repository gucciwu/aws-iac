
# CKD Project of AWS interview!

## Installation
Install python 3.8 and CDK
```
SKIP
```
To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth [stack]
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth [stack]`       emits the synthesized CloudFormation template
 * `cdk deploy [stack]`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Stacks
 * `microservice-dev`: development environment
 * `microservice-test`: test environment
 * `microservice-uat`: UAT environment
 * `microservice-prod`: production environment
 
 ## Problems
 * I got a `500-internal server error` when accessing sync and backup lambda functions, but there is no error message in the log of CloudWatch
 * I can't find a way to create S3 Glacier and S3 Glacier Deep Archive with CDK
 * Since there is no business logic mentioned in the case, 
   and there are different architecture solutions based on different business logic, 
   only a framework of single service shows in my stack