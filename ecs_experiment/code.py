from aws_cdk import core


class CodeService(core.Construct):

    def __init__(self, scope: core.Construct, id: str,
                 staging: core.Construct, prod: core.Construct,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

