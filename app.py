#!/usr/bin/env python3

from aws_cdk import core

from ecs_experiment.ecs_experiment_stack import EcsExperimentStack


app = core.App()
EcsExperimentStack(app, "ecs-experiment")

app.synth()
