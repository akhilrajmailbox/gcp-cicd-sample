import os
import json
import base64
from slack_webhook import Slack

SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
GH_ORG_NAME = os.environ['GH_ORG_NAME']
GH_REPO_NAME = os.environ['GH_REPO_NAME'].split(' ')
RETURN_STATUSES = ['SUCCESS', 'CANCELLED', 'FAILURE', 'INTERNAL_ERROR', 'TIMEOUT']
slack = Slack(url=SLACK_WEBHOOK_URL)

# subscribeSlack is the main function called by Cloud Functions.
def subscribeSlack(data, context):
    build_data = json.loads(base64.b64decode(data['data']).decode('utf-8'))
    # Skip if the current status is not in the status list.
    # Add additional statuses to list if you'd like:
    # QUEUED, WORKING, SUCCESS, FAILURE,
    # INTERNAL_ERROR, TIMEOUT, CANCELLED
    if build_data['status'] not in RETURN_STATUSES:
        return
    
    GET_REPO_NAME = build_data['substitutions']['REPO_NAME']
    if GET_REPO_NAME in GH_REPO_NAME:
        createSlackMessage(build_data)


def createSlackMessage(build_data):
    GCP_PROJECT_ID = build_data['projectId']
    BUILD_ID = build_data['id']
    BUILD_STATUS = build_data['status']
    COMMIT_SHA = build_data['substitutions']['SHORT_SHA']
    REPO_NAME = build_data['substitutions']['REPO_NAME']
    BRANCH_NAME = build_data['substitutions']['BRANCH_NAME']

    slack.post(text="Build Status",
    blocks = [{
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Build {BUILD_STATUS}".format(BUILD_STATUS=BUILD_STATUS)
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Repository:*\n{REPO_NAME}".format(REPO_NAME=REPO_NAME)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Branch:*\n{BRANCH_NAME}".format(BRANCH_NAME=BRANCH_NAME)
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":open_book: View Logs on CloudBuild"
                    },
                    "url": "https://console.cloud.google.com/cloud-build/builds/{BUILD_ID};tab=detail?project={GCP_PROJECT_ID}".format(
                        BUILD_ID=BUILD_ID, GCP_PROJECT_ID=GCP_PROJECT_ID
                    )
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":scroll: View Commit"
                    },
                    "url": "https://github.com/{GH_ORG_NAME}/{REPO_NAME}/commit/{COMMIT_SHA}".format(
                        GH_ORG_NAME=GH_ORG_NAME, REPO_NAME=REPO_NAME, COMMIT_SHA=COMMIT_SHA
                        )
                }
            ]
        }]
    )