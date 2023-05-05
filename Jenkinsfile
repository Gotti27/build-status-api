void setBuildStatus(String message, String state) {
    step([
        $class: "GitHubCommitStatusSetter",
        reposSource: [$class: "ManuallyEnteredRepositorySource", url: "https://github.com/Gotti27/build-status-api/"],
        contextSource: [$class: "ManuallyEnteredCommitContextSource", context: "ci/jenkins/build-status"],
        errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
        statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
    ]);
}

pipeline {
    agent any
    triggers {
        pollSCM 'H/5 * * * *'
    }
    stages {
        stage('Build') {
            steps {
                echo "Build started"
                echo env.BRANCH_NAME
                sh """
                    cp $JENKINS_HOME/.envvars/buildStatusApi/flaskProd.env application/.env
                    BRANCH=${env.BRANCH_NAME} docker compose -f docker-compose.yml --env-file $JENKINS_HOME/.envvars/buildStatusApi/.env build
                """
                echo "Build finished"
            }
        }
        stage('Test') {
            steps {
                echo "Tests started"
                echo env.BRANCH_NAME
                echo "Test TODO"
                /*
                sh """
                    ls
                    python3 -m venv venv
                    . venv/bin/activate
                    cd application
                    pip install -r requirements.txt
                    python3 manage.py test
                """
                */
                echo "Tests finished"
            }
        }
        stage('Deliver') {
            when {
                branch "master"
            }
            steps {
                echo 'Deliver started'

                withEnv(readFile("$JENKINS_HOME/.envvars/buildStatusApi/jenkinsEnv.txt").split('\n') as List) {
                    sh """
                    echo ${PRODUCTION_DOCKER_ENGINE}
                    DOCKER_HOST=${PRODUCTION_DOCKER_ENGINE} docker container ls -a
                    DOCKER_HOST=${PRODUCTION_DOCKER_ENGINE} BRANCH=${env.BRANCH_NAME} docker compose -f docker-compose.yml --project-name build-status-api --env-file $JENKINS_HOME/.envvars/buildStatusApi/production.env up -d --build
                    DOCKER_HOST=${PRODUCTION_DOCKER_ENGINE} docker container ls -a
                    """
                }

                echo 'Deliver finished'
            }
        }
    }
    post {
        success {
            setBuildStatus("Build succeeded", "SUCCESS");
        }
        failure {
            setBuildStatus("Build failed", "FAILURE");
        }
    }
}