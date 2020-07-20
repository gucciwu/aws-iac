#!/usr/bin/env python3

from aws_cdk import core

from gw_interview_py.gw_interview_py_stack import Microservice


app = core.App()
Microservice(app, "microservice")

app.synth()
