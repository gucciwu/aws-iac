from aws_cdk.aws_s3_assets import Asset
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core
)

from utils import guid


class EC2InstanceStack(core.Construct):
    DEFAULT_EC2_TYPE = 't3.micro'
    DEFAULT_IMAGE = ec2.MachineImage.latest_amazon_linux(
        generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        edition=ec2.AmazonLinuxEdition.STANDARD,
        virtualization=ec2.AmazonLinuxVirt.HVM,
        storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
    )

    def __init__(self, scope: core.Construct, id: str = guid(), vpc: str = "VPC") -> None:
        super().__init__(scope, id)

        # VPC
        self.vpc = ec2.Vpc(self, vpc,
                           nat_gateways=0,
                           subnet_configuration=[
                               ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC)]
                           )

        instance = self.create_instance()

    def create_instance(self):
        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))

        # Instance
        instance = ec2.Instance(self, "Instance",
                                instance_type=ec2.InstanceType(self.DEFAULT_EC2_TYPE),
                                machine_image=self.DEFAULT_IMAGE,
                                vpc=self.vpc,
                                role=role
                                )

        return instance
