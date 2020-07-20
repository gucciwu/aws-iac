#!/usr/bin/env python3

from aws_cdk import core

from gw_interview_py.gw_interview_py_stack import Microservice


app = core.App()
Microservice(app, "microservice-dev", vpc_id='dev')
Microservice(app, "microservice-test", vpc_id='test')
Microservice(app, "microservice-uat", vpc_id='uat')
Microservice(app, "microservice-prod", vpc_id='prod')

app.synth()
