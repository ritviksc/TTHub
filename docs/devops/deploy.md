# DevOps process for Taurite Tu

## Deployment
For our system to be usable by the general public, we have to deploy it.
Right now our system is running locally, meaning only we can test/use it.
As you can see we are building a product for external use, so this defeats the purpose of making a system.
For the system to be accessible to external users, we must host it. This could be using the cloud, remote server,
or using existing client infrastructure.

### Possible Deployment Strategies
Possible methods of deploying a system:
  * Cloud platforms — AWS, Azure, Google Cloud, **Render**, etc
  * Your own server — university/company server, VPS
  * On-premises — deploy within an organisation's infrastructure

For the inital deployment we will use Render - it will host our web service on the cloud, using the free tier,
alebit limited but gets the job done. This can be changed in the future - if required.

We used Render to deploy the following components (all independently of each other):
  * Vue Frontend
  * Django Backend
  * Redis
  * Celery
  * Postgres

They were deployed in the order below:
```Deployment Order
1. PostgreSQL Database
         |
2. Django Backend
         |
3. Redis
         |
4. Celery Worker
         |
5. Vue Frontend
```

## CI/CD Pipeline
The project uses a **Continuous Integration and Continuous Deployment (CI/CD)** pipeline to automate testing, building, and deployment of the application. **GitBucket** serves as the team's primary source code repository, with the code mirrored to **GitLab** for CI and **GitHub** for deployment. GitLab CI/CD runs automated checks, including Django backend tests, Vue frontend tests, integration tests, and build validation, to help identify issues before deployment. The GitHub repository is connected to **Render**, which hosts the Django REST Framework backend as a web service and the Vue frontend as a static site. Render builds and deploys the application from the GitHub repository, allowing the team to make updated versions available online. This workflow reduces manual deployment effort, improves consistency, and supports rapid iteration during development and demonstration.

GitLab: https://gitlab.com/cosc345-group-4/tthub




