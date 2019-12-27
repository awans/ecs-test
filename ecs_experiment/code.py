from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as actions
from aws_cdk import aws_iam as iam
from aws_cdk import core

GITHUB_USER = "awans"
GITHUB_REPO = "ecs-test"


class CodeService(core.Construct):

    def __init__(self, scope: core.Construct, id: str,
                 staging: core.Construct, prod: core.Construct,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        code_pipeline = codepipeline.Pipeline(
            self,
            'Build',
            # artifact_bucket=artifact_bucket,
            pipeline_name='ecs-pipeline',
            restart_execution_on_update=True,
        )
        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")


        token = core.SecretValue.secrets_manager("/ecs-pipeline/secrets/github/token", json_field="github-token")
        code_pipeline.add_stage(stage_name='Source', actions=[
            actions.GitHubSourceAction(
                action_name='Source',
                owner=GITHUB_USER,
                oauth_token=token,
                repo=GITHUB_REPO,
                branch='master',
                output=source_output,
        )])

        build_project = codebuild.PipelineProject(self, "BuildProject",
            build_spec=codebuild.BuildSpec.from_source_filename(filename='buildspec.yml'),
            environment=dict(
                build_image=codebuild.LinuxBuildImage.UBUNTU_14_04_DOCKER_18_09_0,
                privileged=True
            )
        )

        build_project.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryFullAccess"))

        code_pipeline.add_stage(stage_name='Build', actions=[
            actions.CodeBuildAction(
                action_name='CodeBuildProject',
                input=source_output,
                outputs=[build_output],
                project=build_project,
                type=actions.CodeBuildActionType.BUILD,
        )])

        deploy_stage = code_pipeline.add_stage(stage_name="Deploy", actions=[
            actions.EcsDeployAction(
                action_name='DeployAction',
                service=prod.service,
                input=build_output,
        )])

