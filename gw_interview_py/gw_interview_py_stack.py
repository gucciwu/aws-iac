from aws_cdk import (core, aws_s3 as s3,
                     aws_ec2 as ec2,
                     aws_autoscaling as autoscaling,
                     aws_elasticloadbalancing as elb,
                     aws_cloudfront as cloudfront,
                     aws_elasticache as elasticache,
                     aws_rds as rds
                     )


class GwInterviewPyStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


class Microservice(core.Stack):
    DEFAULT_EC2_TYPE = ec2.InstanceType('t3.micro')
    DEFAULT_IMAGE = ec2.MachineImage.latest_amazon_linux(
        generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        edition=ec2.AmazonLinuxEdition.STANDARD,
        virtualization=ec2.AmazonLinuxVirt.HVM,
        storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
    )

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc: ec2.Vpc = ec2.Vpc(self, 'vpc-1657f27d', max_azs=2)
        self.auto_scaling_group: autoscaling.AutoScalingGroup = self.create_auto_scaling_group()
        self.elb: elb.LoadBalancer = self.create_elb()
        self.rds: rds.DatabaseInstance = self.create_rds()
        self.cloudfront: cloudfront.Distribution = self.create_cloud_front()
        self.archive_storage: s3.Bucket = self.create_s3(id='archive_storage', versioned=True)
        self.ec2: ec2.Instance = self.create_ec2()
        # self.cache: elasticache.CfnCacheCluster = self.create_elasticache()

    def create_elb(self):
        lb = elb.LoadBalancer(self, 'myElb', vpc=self.vpc, cross_zone=True,
                              internet_facing=True,
                              health_check=elb.HealthCheck(port=80))

        lb.add_target(self.auto_scaling_group)
        lb.add_listener(external_port=80)

        return lb

    def create_cloud_front(self):
        static_bucket = self.create_s3('static_files')
        distribution = cloudfront.Distribution(self, "distribution",
                                               default_behavior=cloudfront.BehaviorOptions(
                                                   allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                                                   origin=cloudfront.Origin.from_bucket(static_bucket))
                                               )
        return distribution

    def create_s3(self, id: str = 'files', versioned: bool = False):
        bucket = s3.Bucket(self, id, versioned=versioned)
        return bucket

    def create_ec2(self):
        instance = ec2.Instance(self, 'myEC2',
                                vpc=self.vpc,
                                instance_type=self.DEFAULT_EC2_TYPE, machine_image=self.DEFAULT_IMAGE)

        return instance

    def create_elasticache(self):
        cache = elasticache.CfnCacheCluster(self, 'myCache',
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
            self, "myRDS",
            master_username="master",
            master_user_password=core.SecretValue.plain_text("password"),
            database_name="db1",
            engine=rds.DatabaseInstanceEngine.MYSQL,
            vpc=self.vpc,
            port=3306,
            instance_type=self.DEFAULT_EC2_TYPE,
            removal_policy=core.RemovalPolicy.DESTROY,
            deletion_protection=False,
            multi_az=True
        )
        return my_rds

    def create_sync_function(self):
        pass

    def create_backup_function(self):
        pass

    def create_auto_scaling_group(self):
        auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
                                                          vpc=self.vpc,
                                                          instance_type=self.DEFAULT_EC2_TYPE,
                                                          machine_image=self.DEFAULT_IMAGE,
                                                          min_capacity=1,
                                                          max_capacity=5
                                                          )
        return auto_scaling_group
