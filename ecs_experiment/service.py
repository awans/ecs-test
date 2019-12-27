import os.path

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_rds as rds
from aws_cdk import core

dirname = os.path.dirname(__file__)

# has to be done outside of CDK
CERT_ARN = "arn:aws:acm:us-west-1:312093006778:certificate/e00b73a0-f919-4ea0-a2d8-81f985331665"
REPO_ARN = "arn:aws:ecr:us-west-1:312093006778:repository/ecs-experiment"


class EcsService(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # by default this creates two subnets
        # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2.README.html
        vpc = ec2.Vpc(self, "VPC", cidr="10.0.0.0/21")

        # add access log logging
        alb = lb = elbv2.ApplicationLoadBalancer(self, "ALB",
            vpc=vpc,
            internet_facing=True)
        p80_listener = alb.add_listener("HTTPListener",
            port=80,
            open=True)
        p80_listener.add_redirect_response("TLSRedirect",
                                       status_code="HTTP_301",
                                       protocol="HTTPS")
        p443_listener = alb.add_listener("HTTPSListener",
            port=443,
            open=True,
            certificate_arns=[CERT_ARN])

        # database
        db_instance = rds.DatabaseInstance(self, "DB",
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            instance_class=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
            master_username="postgres",
            vpc=vpc)

        # fargate cluster
        cluster = ecs.Cluster(self, "Cluster",
            vpc=vpc
        )
        task_definition = ecs.FargateTaskDefinition(self, "TaskDef",
            memory_limit_mib=512,
            cpu=256)
        container = task_definition.add_container("Web",
            image=ecs.ContainerImage.from_ecr_repository(ecr.Repository.from_repository_arn(self, "repo", REPO_ARN), "latest"),
            environment={
                "STAGE": id,
                "DATABASE_URL": db_instance.instance_endpoint.socket_address,
                "DATABASE_USERNAME": "postgres",
            },
            secrets={
                "DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(db_instance.secret),
            },
            logging=ecs.LogDrivers.aws_logs(stream_prefix=f"{id}-ECSCluster"))
        container.add_port_mappings(ecs.PortMapping(container_port=5000))
        fargate_service = ecs.FargateService(self, "FargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2)

        db_instance.connections.allow_default_port_from(fargate_service)

        # connect it to the ALB
        p443_listener.add_targets("FargateServiceTarget",
            port=5000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[fargate_service])

