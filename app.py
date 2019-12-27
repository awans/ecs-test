#!/usr/bin/env python3

from aws_cdk import core

from ecs_experiment.ecs_stack import EcsStack

app = core.App()
prod = EcsStack(app, "ecs-stack")
app.synth()
