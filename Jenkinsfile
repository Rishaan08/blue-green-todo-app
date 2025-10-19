pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "rishaan03/todo-app"
        DOCKER_CREDENTIALS = 'dockerhub-credentials'
        DOCKER_TAG = "${BUILD_NUMBER}"
        KUBECONFIG = "${HOME}/.kube/config"
        CURRENT_ENV = 'blue'
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
                    
                    CURRENT_ENV = serviceSelector ?: 'blue'
                    env.TARGET_ENV = (CURRENT_ENV == 'blue') ? 'green' : 'blue'
                    
                    echo "Current environment: ${CURRENT_ENV}"
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
                    dockerImage = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.build("${DOCKER_IMAGE}:latest")
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
                        docker stop test-todo-app
                        docker rm test-todo-app
                        
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
                    docker.withRegistry('https://registry.hub.docker.com', DOCKER_CREDENTIALS) {
                        dockerImage.push("${DOCKER_TAG}")
                        dockerImage.push("latest")
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
                        kubectl exec \$POD_NAME -- curl -f http://localhost:5000/health || exit 1
                        
                        echo "✓ ${env.TARGET_ENV} environment is healthy!"
                    """
                }
            }
        }
        
        stage('Switch Traffic') {
            steps {
                echo '========================================='
                echo "Stage 8: Switching traffic from ${CURRENT_ENV} to ${env.TARGET_ENV}"
                echo '========================================='
                input message: "Switch traffic to ${env.TARGET_ENV}?", ok: 'Deploy'
                script {
                    sh """
                        echo "Updating service to point to ${env.TARGET_ENV}..."
                        kubectl patch service todo-app-service -p '{"spec":{"selector":{"version":"${env.TARGET_ENV}"}}}'
                        
                        echo "Verifying service update..."
                        kubectl get service todo-app-service -o yaml
                        
                        echo "✓ Traffic switched to ${env.TARGET_ENV}!"
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
                        echo "Service Details:"
                        kubectl describe service todo-app-service
                        
                        echo "\nActive Pods:"
                        kubectl get pods -l app=todo-app -o wide
                        
                        echo "\nApplication URL:"
                        minikube service todo-app-service --url
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
            echo "Previous environment: ${CURRENT_ENV}"
            echo "New active environment: ${env.TARGET_ENV}"
            echo "Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
            echo "Access: minikube service todo-app-service --url"
            echo '========================================='
        }
        failure {
            echo '========================================='
            echo '✗ Deployment FAILED!'
            echo '========================================='
            echo "Keeping ${CURRENT_ENV} environment active"
        }
        always {
            echo 'Cleaning up Docker resources...'
            sh 'docker system prune -f || true'
        }
    }
}
