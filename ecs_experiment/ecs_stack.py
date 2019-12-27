from aws_cdk import core

from ecs_experiment import code, service


class EcsStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        prod = service.EcsService(self, "prod")
        # staging = service.EcsService(self, "staging")
        code.CodeService(self, "build", None, prod)

