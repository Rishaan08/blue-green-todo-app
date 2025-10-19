pipeline {
    agent {
        label 'built-in'
    }
    
    environment {
        DOCKER_IMAGE = "rishaan03/todo-app"
        DOCKER_CREDENTIALS = 'dockerhub-credentials'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '========================================='
                echo 'Stage 1: Checking out code'
                echo '========================================='
                checkout scm
            }
        }
        
        stage('Determine Current Environment') {
            steps {
                echo '========================================='
                echo 'Stage 2: Determining current active environment'
                echo '========================================='
                script {
                    def serviceSelector = sh(
                        script: "kubectl get service todo-app-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo 'blue'",
                        returnStdout: true
                    ).trim()
                    
                    env.CURRENT_ENV = serviceSelector ?: 'blue'
                    env.TARGET_ENV = (env.CURRENT_ENV == 'blue') ? 'green' : 'blue'
                    
                    echo "Current environment: ${env.CURRENT_ENV}"
                    echo "Target deployment environment: ${env.TARGET_ENV}"
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '========================================='
                echo 'Stage 3: Building Docker image'
                echo '========================================='
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
                }
            }
        }
        
        stage('Test Application') {
            steps {
                echo '========================================='
                echo 'Stage 4: Testing application'
                echo '========================================='
                script {
                    sh '''
                        echo "Starting test container..."
                        docker run -d --name test-todo-app -p 5001:5000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                        
                        echo "Waiting for application to start..."
                        sleep 15
                        
                        echo "Testing health endpoint..."
                        curl -f http://localhost:5001/health || exit 1
                        
                        echo "Testing main endpoint..."
                        curl -f http://localhost:5001/ || exit 1
                        
                        echo "Cleaning up test container..."
                        docker stop test-todo-app || true
                        docker rm test-todo-app || true
                        
                        echo "✓ All tests passed!"
                    '''
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                echo '========================================='
                echo 'Stage 5: Pushing to Docker Hub'
                echo '========================================='
                script {
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh '''
                            echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                            docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                            docker push ${DOCKER_IMAGE}:latest
                        '''
                    }
                }
            }
        }
        
        stage('Deploy to Target Environment') {
            steps {
                echo '========================================='
                echo "Stage 6: Deploying to ${env.TARGET_ENV} environment"
                echo '========================================='
                script {
                    sh """
                        echo "Deploying to ${env.TARGET_ENV} environment..."
                        kubectl apply -f k8s-${env.TARGET_ENV}-deployment.yaml
                        
                        echo "Waiting for ${env.TARGET_ENV} deployment to be ready..."
                        kubectl rollout status deployment/todo-app-${env.TARGET_ENV} --timeout=5m
                        
                        echo "Verifying ${env.TARGET_ENV} deployment..."
                        kubectl get deployment todo-app-${env.TARGET_ENV}
                        kubectl get pods -l version=${env.TARGET_ENV}
                    """
                }
            }
        }
        
        stage('Health Check Target Environment') {
            steps {
                echo '========================================='
                echo "Stage 7: Health checking ${env.TARGET_ENV} environment"
                echo '========================================='
                script {
                    sh """
                        echo "Getting pod from ${env.TARGET_ENV} environment..."
                        POD_NAME=\$(kubectl get pods -l version=${env.TARGET_ENV} -o jsonpath='{.items[0].metadata.name}')
                        
                        echo "Testing health endpoint on pod: \$POD_NAME"
                        kubectl exec \$POD_NAME -- python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
                        
                        echo "✓ ${env.TARGET_ENV} environment is healthy!"
                    """
                }
            }
        }
        
        stage('Switch Traffic') {
            steps {
                echo '========================================='
                echo "Stage 8: Switching traffic from ${env.CURRENT_ENV} to ${env.TARGET_ENV}"
                echo '========================================='
                script {
                    sh """
                        echo "Automatically switching traffic to ${env.TARGET_ENV}..."
                        kubectl patch service todo-app-service -p '{"spec":{"selector":{"version":"${env.TARGET_ENV}"}}}'
                        
                        echo "Waiting for service update to propagate..."
                        sleep 5
                        
                        echo "Verifying service update..."
                        ACTIVE_ENV=\$(kubectl get service todo-app-service -o jsonpath='{.spec.selector.version}')
                        echo "Service now points to: \$ACTIVE_ENV"
                        
                        if [ "\$ACTIVE_ENV" = "${env.TARGET_ENV}" ]; then
                            echo "✓ Traffic successfully switched to ${env.TARGET_ENV}!"
                        else
                            echo "✗ Traffic switch failed!"
                            exit 1
                        fi
                    """
                }
            }
        }
        
        stage('Verify Production') {
            steps {
                echo '========================================='
                echo 'Stage 9: Verifying production deployment'
                echo '========================================='
                script {
                    sh '''
                        echo "=== Service Details ==="
                        kubectl get service todo-app-service -o wide
                        
                        echo ""
                        echo "=== Active Environment ==="
                        kubectl get service todo-app-service -o jsonpath='{.spec.selector.version}'
                        echo ""
                        
                        echo ""
                        echo "=== All Deployments ==="
                        kubectl get deployments -l app=todo-app
                        
                        echo ""
                        echo "=== Active Pods ==="
                        kubectl get pods -l app=todo-app -o wide
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '========================================='
            echo '✓ Blue-Green Deployment SUCCESS!'
            echo '========================================='
            echo "Previous environment: ${env.CURRENT_ENV}"
            echo "New active environment: ${env.TARGET_ENV}"
            echo "Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
            echo ''
            echo 'Deployment Details:'
            echo "- Built and tested Docker image"
            echo "- Deployed to ${env.TARGET_ENV} environment"
            echo "- Passed health checks"
            echo "- Switched traffic automatically"
            echo "- Zero downtime achieved!"
            echo '========================================='
        }
        failure {
            echo '========================================='
            echo '✗ Deployment FAILED!'
            echo '========================================='
            echo "Failed at one of the pipeline stages"
            echo "Traffic remains on: ${env.CURRENT_ENV}"
            echo '========================================='
        }
        always {
            echo 'Cleaning up Docker resources...'
            sh 'docker system prune -f || true'
        }
    }
}
