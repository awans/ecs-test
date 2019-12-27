from aws_cdk import core

GITHUB_USER = "awans"
GITHUB_REPO = "ecs-test"


class ECSBuildProject(codebuild.PipelineProject):
    def __init__(self, scope: core.Construct, id: str,
                 **kwargs) -> None:
        build_spec = codebuild.BuildSpec.from_object(dict(
            version="0.2",
            phases=dict(
                pre_build=dict(commands=[
                    "echo Logging in to Amazon ECR...",
                    "aws --version",
                    "$(aws ecr get-login --region $AWS_DEFAULT_REGION --no-include-email)",
                    "REPOSITORY_URI=312093006778.dkr.ecr.us-west-1.amazonaws.com/ecs-experiment",
                    "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                    "IMAGE_TAG=${COMMIT_HASH:=latest}",
                ]),
                build=dict(commands=[
                    "echo Build started on `date`",
                    "echo Building the Docker image...",
                    "docker build -t $REPOSITORY_URI:latest .",
                    "docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG",
                ]),
                post_build=dict(commands=[
                    "echo Build completed on `date`",
                    "echo Pushing the Docker images...",
                    "docker push $REPOSITORY_URI:latest",
                    "docker push $REPOSITORY_URI:$IMAGE_TAG",
                    "echo Writing image definitions file...",
                    'printf \'[{"name":"Web","imageUri":"%s"}]\' $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json',
                ]),
            ),
            artifacts={
                "files": ["imagedefinitions.json"]
            },
            environment=dict(buildImage=
                codebuild.LinuxBuildImage.UBUNTU_14_04_DOCKER_18_09_0
        super().__init__(scope, id, build_spec=build_spec, **kwargs)


class CodeService(core.Construct):

    def __init__(self, scope: core.Construct, id: str,
                 staging: core.Construct, prod: core.Construct,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline = pipeline.Pipeline(
            self,
            'Build',
            # artifact_bucket=artifact_bucket,
            pipeline_name='ecs-pipeline',
            restart_execution_on_update=True,
        )
        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")


        token = cdk.SecretValue.secretsManager("/ecs-pipeline/secrets/github/token")
        pipeline.add_stage(stage_name='Source', actions=[
            actions.GitHubSourceAction(
                action_name='Source',
                owner=GITHUB_USER,
                oauth_token=token,
                repo=GITHUB_REPO,
                branch='master',
                output=source_output,
        )])

        build_project = ECSBuildProject(self, "Build")

        pipeline.add_stage(stage_name='Build', actions=[
            actions.CodeBuildAction(
                action_name='CodeBuildProject',
                input=source_output,
                outputs=[build_output],
                project=build_project,
                type=actions.CodeBuildActionType.BUILD,
        )])

        deploy_stage = pipeline.add_stage(stage_name="Deploy", actions=[
            actions.EcsDeployAction({
                action_name='DeployAction',
                service=prod.service,
                input=build_output,
        })])

