const { IncomingWebhook } = require('@slack/webhook');

const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL;
const GH_ORG_NAME = process.env.GH_ORG_NAME;
const GH_REPO_NAME = process.env.GH_REPO_NAME;

const webhook = new IncomingWebhook(SLACK_WEBHOOK_URL);
const BAD_STATUSES = ['FAILURE', 'INTERNAL_ERROR', 'TIMEOUT'];
const RETURN_STATUSES = ['SUCCESS', 'CANCELLED', 'FAILURE', 'INTERNAL_ERROR', 'TIMEOUT'];

// subscribeSlack is the main function called by Cloud Functions.
module.exports.subscribeSlack = (pubSubEvent, context) => {
  const build = eventToBuild(pubSubEvent.data);
  // Skip if the current status is not in the status list.
  // Add additional statuses to list if you'd like:
  // QUEUED, WORKING, SUCCESS, FAILURE,
  // INTERNAL_ERROR, TIMEOUT, CANCELLED
  if (!RETURN_STATUSES.includes(build.status)) {
    return;
  }
  // Send message to Slack.
  const message = createSlackMessage(build);
  const GET_REPO_NAME = build.substitutions.REPO_NAME
  
  if (GH_REPO_NAME==GET_REPO_NAME) {
    webhook.send(message);
  }
};
// eventToBuild transforms pubsub event message to a build object.
const eventToBuild = (data) => {
  return JSON.parse(Buffer.from(data, 'base64').toString());
}
// createSlackMessage creates a message from a build object.
const createSlackMessage = (build) => {
  const failedStep = build.steps.find((step) => {
    return BAD_STATUSES.includes(step.status);
  });
  const hasStatus = failedStep ? `has failed step \`${failedStep.id}\`` : 'succeed';
  const GCP_PROJECT_ID = build.projectId
  
  const msg = (() => {
    return [];
  })();

  return {
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": `Build for commit \`${build.substitutions.SHORT_SHA}\` on branch \`${build.substitutions.BRANCH_NAME}\` of repository \`${build.substitutions.REPO_NAME}\` ${hasStatus}.`,
        }
      },
      {
        "type": "actions",
        "elements": [
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": ":open_book: View Logs on CloudBuild",
              "emoji": true
            },
            "url": `https://console.cloud.google.com/cloud-build/builds/${build.id};tab=detail?project=${GCP_PROJECT_ID}`
          },
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": ":scroll: View Commit",
              "emoji": true
            },
            "url": `https://github.com/${GH_ORG_NAME}/${build.substitutions.REPO_NAME}/commit/${build.substitutions.COMMIT_SHA}`,
          },
        ]
      },
    ]
  }; 
};