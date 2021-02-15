## application service

## Deployment and configuration

Set the project id and project number to the environment variable

```
export PROJECT_ID=my-project
export PROJECT_NUMBER=$(gcloud projects list  | grep ${PROJECT_ID} | awk '{print $3}')
```

This deployment tool is completely built on top of the google deployment manager to create infrastructure.



### Create an IAM (Service Account for the Application)

The IAM role and user is created outside of the deployment, this service account is going to use by the application to perform its task

```shell
gcloud iam service-accounts create application-app --display-name='application Application'
```

#### Application level permission

Give `iam.serviceAccountTokenCreator` permission to the application-app service account.

```shell
gcloud iam service-accounts add-iam-policy-binding application-app@${PROJECT_ID}.iam.gserviceaccount.com --member serviceAccount:application-app@${PROJECT_ID}.iam.gserviceaccount.com --role roles/iam.serviceAccountTokenCreator
```

**WARNING :** `Make sure this role (roles/iam.serviceAccountTokenCreator) is only applied so your service account can impersonate itself. If this role is applied GCP project-wide, this will allow the service account to impersonate any service account in the GCP project where it resides.`


Grant access to the storage bucket which we created before to read and write the data : `legacyBucketWriter`

```shell
gsutil iam ch serviceAccount:application-app@${PROJECT_ID}.iam.gserviceaccount.com:legacyBucketWriter gs://${PROJECT_ID}-application-data
```

Grant access to the storage bucket (docker registry bucket) for pull the docker images : `objectViewer`

```shell
gsutil iam ch serviceAccount:application-app@${PROJECT_ID}.iam.gserviceaccount.com:objectViewer gs://artifacts.${PROJECT_ID}.appspot.com
```



Enable IAM Service Account Credentials API

enable [here](https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com)




### Create an IAM (Service Account for Deployment)

This user is for deploying the application in an automated way, do not use this service account inside the application

```shell
gcloud iam service-accounts create application-deployment --display-name='application Deployment'
```


#### Infra / Deployment level permission


Give `cloudbuild.builds.editor` permission to the application-deployment service account.

```shell
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:application-deployment@${PROJECT_ID}.iam.gserviceaccount.com --role roles/cloudbuild.builds.editor
```

Give `cloudscheduler.jobRunner` permission to the application-deployment service account.

```shell
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:application-deployment@${PROJECT_ID}.iam.gserviceaccount.com --role roles/cloudscheduler.jobRunner
```


Grant access to the storage bucket (docker registry bucket) for push and pull the docker images : [`objectCreator` and `objectViewer`] or [`legacyBucketWriter`]

```shell
gsutil iam ch serviceAccount:application-deployment@${PROJECT_ID}.iam.gserviceaccount.com:legacyBucketWriter gs://artifacts.${PROJECT_ID}.appspot.com
gsutil iam ch serviceAccount:application-deployment@${PROJECT_ID}.iam.gserviceaccount.com:objectViewer gs://artifacts.${PROJECT_ID}.appspot.com
```

Grant permission to the cloud build service account for rolling the instance group

```shell
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com --role roles/compute.instanceAdmin.v1
```



### Run the setup to create new vpc (optional)

```shell
gcloud deployment-manager deployments create my-vpc --config setup_vpc.yaml --project=${PROJECT_ID}
```

:exclamation: warning :exclamation:

#### firewall configuration

* deny rule to block outgoing connection to peering network

~~~
By default the firewall denied all egress (outbound) connection from this VPC Network to 172.16.0.1/32, This is a sample ip address which is used to configure the firewall (GCP won't allow you to leave it blank). Remove this IP address and add the destination subnet range to deny the access from this VPC network.
~~~

* allow rule to accept connection to application service from peering network

~~~
Add the subnet range of the eering network subnet's to the firewall : application-allow-firewall
~~~

Detailed Information about the `properties` of `setup_vpc.yaml`


| Variable Name | Description |
|---------------|---------------|
| region | Region under the VPC  |
| createSubnet | GCP created subnets (auto) / manual created subnet (manual) (options --> auto / manual)  |
| ipCidrRange | Valid only if `createSubnet: manual`, Choose the right CIDR for the private subnet  |


Find the subnet range at [subnet calculator](https://community.spiceworks.com/tools/subnet-calc) or choose from the table

**Note : Change the value for `X` for each VPC (`X` range can vary from `20` to `31` ; this range can start from `16` also but make sure that none of the applications are not using any of these range like docker using `172.17.0.0/16`)**


| Subnet | Network | Hosts |
|-------|---------|-------|
| subnet 1 | 172.`X`.0.0/24 | 254 |
| subnet 2 | 172.`X`.1.0/24 | 254 |
| subnet 3 | 172.`X`.2.0/24 | 254 |
| subnet 4 | 172.`X`.3.0/24 | 254 |
| subnet 5 | 172.`X`.4.0/24 | 254 |
| subnet 6 | 172.`X`.5.0/24 | 254 |
| subnet 7 | 172.`X`.6.0/24 | 254 |
| subnet 8 | 172.`X`.7.0/24 | 254 |
| subnet 9 | 172.`X`.8.0/24 | 254 |
| subnet 10 | 172.`X`.9.0/24 | 254 |
| subnet 11 | 172.`X`.10.0/24 | 254 |
| subnet 12 | 172.`X`.11.0/24 | 254 |
| subnet 13 | 172.`X`.12.0/24 | 254 |
| subnet 14 | 172.`X`.13.0/24 | 254 |
| subnet 15 | 172.`X`.14.0/24 | 254 |
| subnet 16 | 172.`X`.15.0/24 | 254 |



### VPC Peering (configure only if you need it)

Configure peering between VPC Network regardless of whether they belong to the same project or the same organization by referring the [configuration steps](https://cloud.google.com/vpc/docs/using-vpc-peering). Please find the [overview of vpc peering](https://cloud.google.com/vpc/docs/vpc-peering) to understand more about VPC network peering.



### Now run the setup to spin up the deployment

Before deploying new cluster check config in file `setup_application_v1.yaml` and update the *Properties*

* When setting up new cluster copy setup_application_v1.yaml to `setup_application_v<cluster_version>.yaml` and update `cluster_version` inside the file too.

```shell
gcloud deployment-manager deployments create application-cluster --config setup_application_v1.yaml --project=${PROJECT_ID}
```


Detailed Information about the `properties` of `setup_application_v<cluster_version>.yaml`


| Variable Name | Description |
|---------------|---------------|
| network | VPC name where the app get deployed |
| region | Region under the VPC  |
| subnetwork | subnet name |
| cluster_version | version number for identifying the deployment version |
| preemptableMachineType | Type of GCE instance to use for main cluster (preemptable instance) |
| dedicatedMachineType | Type of GCE instance to use for failover cluster (dedicated instance) |
| targetSize | number of instance to be deployed in the preemptable instance group (main cluster)|
| maxSize | maximum number of instance can scale-in on preemptable instance group (main cluster autoscaling configuration) |
| serviceAccount | Service Account Name which we created (Not the complete email address, its just name till '@'), eg : `application-app` |
| dockerImage | docker image name |


**Note : If the Load Balancer is Internal, then configure the client machines with network tags : `application-client` to establish the connection with `application-server`**



### reference 

[Supported Resource Types](https://cloud.google.com/deployment-manager/docs/configuration/supported-resource-types)

[Deployment Manager](https://medium.com/google-cloud/google-cloud-deployment-manager-865931dd6880)

[Scheduling Cloud Builds](https://medium.com/google-cloud/scheduling-cloud-builds-24d821d5a3d2)

[Google Cloud Auth Method](https://www.vaultproject.io/docs/auth/gcp)

[Google Cloud roles](https://cloud.google.com/iam/docs/understanding-roles)

[Oauth2 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes)