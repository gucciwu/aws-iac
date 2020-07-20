import logging
from os import path

from aws_cdk import (core, aws_s3 as s3,
                     aws_ec2 as ec2,
                     aws_autoscaling as autoscaling,
                     aws_elasticloadbalancing as elb,
                     aws_cloudfront as cloudfront,
                     aws_elasticache as elasticache,
                     aws_rds as rds,
                     aws_iam as iam,
                     aws_lambda as _lambda,
                     aws_apigateway as apigw
                     )

from utils import guid

logger = logging.getLogger(__name__)

base_dir = path.dirname(__file__)


class Microservice(core.Stack):
    DEFAULT_EC2_TYPE = ec2.InstanceType('t3.micro')
    DEFAULT_IMAGE = ec2.MachineImage.latest_amazon_linux(
        generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        edition=ec2.AmazonLinuxEdition.STANDARD,
        virtualization=ec2.AmazonLinuxVirt.HVM,
        storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
    )
    CERTIFICATE_ID = ""

    def __init__(self, scope: core.Construct, id: str, vpc_id: str = guid('VPC-'), **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # self.iam_key_id = self.create_key().to_string()
        self.vpc: ec2.Vpc = ec2.Vpc(self, vpc_id, max_azs=2)
        self.auto_scaling_group: autoscaling.AutoScalingGroup = self.create_auto_scaling_group()
        self.elb: elb.LoadBalancer = self.create_elb()
        self.rds: rds.DatabaseInstance = self.create_rds()
        self.cloudfront: cloudfront.Distribution = self.create_cloud_front()
        self.archive_storage: s3.Bucket = self.create_s3(id='archive_storage', versioned=True)
        self.ec2: ec2.Instance = self.create_ec2()
        # self.cache: elasticache.CfnCacheCluster = self.create_elasticache()
        self.create_sync_function()
        self.create_backup_function()

    def create_key(self):
        """
        Creates an access key for the test user.
        :return: The created access key.
        """
        try:
            key_pair = iam.CfnAccessKey(self, guid('IMA_KEY-'), user_name='test_user')
            logger.info(
                "Created access key pair for test user. Key ID is %s.",
                key_pair.user_name, key_pair.get_att('attr_secret_access_key'))
        except Exception as e:
            logger.exception("Couldn't create access key pair for test user")
            raise
        else:
            return key_pair.get_att('attr_secret_access_key')

    def create_elb(self):
        lb = elb.LoadBalancer(self, guid('ELB-'), vpc=self.vpc, cross_zone=True,
                              internet_facing=True,
                              health_check=elb.HealthCheck(port=80))

        lb.add_target(self.auto_scaling_group)
        lb.add_listener(external_port=80)

        return lb

    def create_cloud_front(self):
        static_bucket = self.create_s3('static_files', type='s3')
        distribution = cloudfront.Distribution(self, "distribution",
                                               default_behavior=cloudfront.BehaviorOptions(
                                                   allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                                                   origin=cloudfront.Origin.from_bucket(static_bucket))
                                               )
        # NEED CERTIFICATE, but I don't have one
        # distribution = cloudfront.CloudFrontWebDistribution(
        #     self, "AnAmazingWebsiteProbably",
        #     origin_configs=[cloudfront.SourceConfiguration(
        #         s3_origin_source=cloudfront.S3OriginConfig(
        #             s3_bucket_source=static_bucket),
        #         behaviors=[cloudfront.Behavior(is_default_behavior=True)]
        #     )],
        #     viewer_certificate=cloudfront.ViewerCertificate.from_iam_certificate(
        #         self.CERTIFICATE_ID,
        #         aliases=["example.com"],
        #         security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1,
        #         # default
        #         ssl_method=cloudfront.SSLMethod.SNI
        #     )
        # )
        return distribution

    def create_s3(self, id: str = guid('S3-'), versioned: bool = False, type: str = 's3'):
        """
        Creates an S3 bucket.
        :param: id
        :param: versioned
        :param: type: s3/Glacier/Glacier Deep Archive
        :return: The bucket.
        """
        bucket = s3.Bucket(self, id, versioned=versioned, cors=[s3.CorsRule(allowed_methods=[s3.HttpMethods.GET],
                                                                            allowed_origins=['*'])])
        return bucket

    def create_ec2(self):
        instance = ec2.Instance(self, guid('EC2-'),
                                vpc=self.vpc,
                                instance_type=self.DEFAULT_EC2_TYPE, machine_image=self.DEFAULT_IMAGE)

        return instance

    def create_elasticache(self):
        cache = elasticache.CfnCacheCluster(self, guid('ELASTICACHE-'),
                                            cache_node_type="cache.t3.micro",
                                            engine="redis",
                                            num_cache_nodes=1,
                                            port=6379,
                                            az_mode="cross-az",
                                            vpc_security_group_ids=['vpc-1657f27d']
                                            )
        return cache

    def create_rds(self):
        my_rds = rds.DatabaseInstance(
            self, guid('RDS-'),
            master_username="master",
            master_user_password=core.SecretValue.plain_text("password"),
            database_name="db1",
            engine=rds.DatabaseInstanceEngine.MYSQL,
            vpc=self.vpc,
            port=3306,
            instance_type=self.DEFAULT_EC2_TYPE,
            removal_policy=core.RemovalPolicy.DESTROY,
            deletion_protection=False,
            multi_az=True,
            max_allocated_storage=1000
        )
        return my_rds

    def create_sync_function(self):
        bucket = s3.Bucket.from_bucket_arn(self, guid('LAMBDA-BACKUP-'), bucket_arn="arn:aws:s3:::interview-lambda")
        fn = _lambda.Function(self, "SyncHandler",
                              runtime=_lambda.Runtime.PYTHON_3_8,
                              handler="lambda_function.lambda_handler",
                              code=_lambda.Code.from_bucket(bucket, 'sync.zip')
                              )
        bucket.grant_read_write(fn)
        apigw.LambdaRestApi(
            self, 'sync',
            handler=fn,
        )
        return fn

    def create_backup_function(self):
        bucket = s3.Bucket.from_bucket_arn(self, guid('LAMBDA-SYNC-'), bucket_arn="arn:aws:s3:::interview-lambda")
        fn = _lambda.Function(self, "BackupHandler",
                              runtime=_lambda.Runtime.PYTHON_3_8,
                              handler="lambda_function.lambda_handler",
                              code=_lambda.Code.from_bucket(bucket, 'backup.zip')
                              )

        apigw.LambdaRestApi(
            self, 'backup',
            handler=fn,
        )
        return fn

    def create_auto_scaling_group(self):
        auto_scaling_group = autoscaling.AutoScalingGroup(self, guid('ASG-'),
                                                          vpc=self.vpc,
                                                          instance_type=self.DEFAULT_EC2_TYPE,
                                                          machine_image=self.DEFAULT_IMAGE,
                                                          min_capacity=1,
                                                          max_capacity=5
                                                          )
        auto_scaling_group.scale_on_cpu_utilization("keepCpuUtilization", target_utilization_percent=10)
        return auto_scaling_group
