# Blue-Green Todo App - Automated Deployment

## Overview
Automated Blue-Green deployment strategy for a dynamic Todo List application using Jenkins, Kubernetes, and Docker.

## Architecture
- **Blue Environment**: Stable production version
- **Green Environment**: New version for testing
- **Service**: Routes traffic between Blue/Green

## Features
- ✅ Add, complete, and delete tasks
- ✅ Persistent storage with SQLite
- ✅ Health check endpoints
- ✅ Blue/Green environment indicators
- ✅ Automated testing
- ✅ Zero-downtime deployments

## Deployment Flow
1. Build Docker image
2. Run automated tests
3. Deploy to inactive environment (Green if Blue is active)
4. Health check new environment
5. Manual approval to switch traffic
6. Update service to route to new environment

## Access Application
```bash
minikube service todo-app-service --url
```

## Manual Commands

### Check current active environment:
```bash
kubectl get service todo-app-service -o jsonpath='{.spec.selector.version}'
```

### View all deployments:
```bash
kubectl get deployments -l app=todo-app
```

### Switch traffic manually:
```bash
# To Blue
kubectl patch service todo-app-service -p '{"spec":{"selector":{"version":"blue"}}}'

# To Green
kubectl patch service todo-app-service -p '{"spec":{"selector":{"version":"green"}}}'
```

## Local Testing
```bash
docker build -t rishaan03/todo-app:test .
docker run -d -p 5000:5000 --name todo-test rishaan03/todo-app:test
curl http://localhost:5000
docker stop todo-test && docker rm todo-test
```
