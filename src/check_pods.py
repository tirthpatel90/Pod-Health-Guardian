import os, boto3, datetime
from kubernetes import client, config

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
S3_BUCKET = os.getenv("S3_BUCKET")
REGION = os.getenv("AWS_REGION", "ap-south-1")

sns = boto3.client('sns', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def main():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces(watch=False)
    
    for pod in pods.items:
        if pod.status.phase not in ["Running", "Succeeded"]:
            pod_name = pod.metadata.name
            namespace = pod.metadata.namespace
            msg = f"Alert: Pod {pod_name} in {namespace} is {pod.status.phase}. Restarting..."
            print(msg)
            
            # Delete to restart
            v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            # Send Email
            sns.publish(TopicArn=SNS_TOPIC_ARN, Message=msg, Subject="K8s Pod Crash Alert")
            # Save Log
            s3.put_object(Bucket=S3_BUCKET, Key=f"logs/{pod_name}-{datetime.datetime.now().timestamp()}.txt", Body=msg)

if __name__ == '__main__':
    main()