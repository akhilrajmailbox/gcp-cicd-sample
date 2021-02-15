#!/bin/bash
export _DEPLOYMENT_ID=$(python3 -c 'import uuid; _DEPLOYMENT_ID=str(uuid.uuid4()); print(_DEPLOYMENT_ID)')

if [[ ! -z "${_K8S_NAMESPACE}" ]] && [[ ! -z "${_K8S_CLUSTER}" ]] && [[ ! -z "${_K8S_LOCATION}" ]] && [[ ! -z "${PROJECT_ID}" ]] ; then

function gkeLogin() {
    gcloud container clusters get-credentials ${_K8S_CLUSTER} --region ${_K8S_LOCATION} --project ${PROJECT_ID}
}

function installDep() {
    apk add gettext jq
}

function gkeDeploy() {
    UPGRADE=$(jq '.upgrade' ./svc_info.json)
    if [[ ${UPGRADE} == '"enable"' ]] ; then
        for pod in $(kubectl get pods -n ${_K8S_NAMESPACE} -oname); do
            kubectl exec ${pod} -n ${_K8S_NAMESPACE} -- ls -la
        done
    else
        echo -e "UPGRADE is not enabled.\ntask aborting....!"
    fi
    sleep 10
    envsubst < ./k8s/deploy.yaml
    envsubst < ./k8s/deploy.yaml | kubectl -n ${_K8S_NAMESPACE} apply -f -
}


function createService() {
    if kubectl get services -n ${_K8S_NAMESPACE} | grep webserver-service >/dev/null ; then
        echo "Service for webserver available in environment : ${_K8S_NAMESPACE}"
    else
        if [[ -f ./k8s/service.yaml ]]; then
            echo "Service for webserver is available and is being Configuring"
            kubectl ${_K8S_NAMESPACE} apply -f ./k8s/service.yaml
        else
            echo "./k8s/service.yaml not found"
        fi
    fi
}


gkeLogin \
    && installDep \
    && gkeDeploy \
    && createService


else
  echo -e "_K8S_NAMESPACE=${_K8S_NAMESPACE}, _K8S_CLUSTER=${_K8S_CLUSTER}, _K8S_LOCATION=${_K8S_LOCATION} and PROJECT_ID=${PROJECT_ID} need to provide.\ntask aborting.....!"
  exit 1
fi