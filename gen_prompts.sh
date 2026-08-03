#!/bin/bash
categories=("architecture" "backend" "frontend" "security" "database" "performance" "testing" "ai" "devops" "code-review" "refactoring" "production" "debugging" "documentation" "planning" "system-design" "scaling")
for cat in "${categories[@]}"; do
  mkdir -p "prompts/$cat"
  file="prompts/$cat/prompts.md"
  echo "# $cat Prompts" > "$file"
  echo "" >> "$file"
  for i in {1..20}; do
    echo "## Prompt $i" >> "$file"
    echo "" >> "$file"
    case $cat in
      "architecture")
        echo "How should I design a microservices architecture for a high-traffic e-commerce platform with requirements for scalability, fault tolerance, and continuous deployment?" >> "$file"
        ;;
      "backend")
        echo "What are the best practices for designing a RESTful API for a social media application that needs to handle millions of users, ensure data consistency, and provide real-time updates?" >> "$file"
        ;;
      "frontend")
        echo "How can I optimize the performance of a React application with large datasets and complex state management, including techniques like memoization, virtualized lists, and code splitting?" >> "$file"
        ;;
      "security")
        echo "What security measures should I implement to protect against OWASP Top 10 vulnerabilities in a web application handling sensitive user data, including authentication, authorization, input validation, and secure headers?" >> "$file"
        ;;
      "database")
        echo "When should I choose a NoSQL database like MongoDB over a relational database like PostgreSQL for a content management system with flexible schema requirements and high write throughput?" >> "$file"
        ;;
      "performance")
        echo "How do I identify and resolve performance bottlenecks in a distributed microservices system under peak load, using profiling, tracing, and load testing tools?" >> "$file"
        ;;
      "testing")
        echo "What testing strategy should I use for a microservices architecture to ensure adequate coverage of unit, integration, contract, and end-to-end tests without slowing down the CI/CD pipeline?" >> "$file"
        ;;
      "ai")
        echo "How should I approach building a recommendation system for an e-commerce product catalog using collaborative filtering and deep learning models, considering cold-start and scalability challenges?" >> "$file"
        ;;
      "devops")
        echo "What are the essential components of a CI/CD pipeline for a Kubernetes-based microservices application, including source control, automated testing, container image building, security scanning, and deployment strategies?" >> "$file"
        ;;
      "code-review")
        echo "What should I look for during a code review of a Python Django application to ensure maintainability, security, and adherence to best practices, including ORM usage, template safety, and dependency management?" >> "$file"
        ;;
      "refactoring")
        echo "How should I refactor a large monolithic Java application to improve modularity and reduce technical debt, using techniques like domain-driven design, strangler fig pattern, and gradual strangulation?" >> "$file"
        ;;
      "production")
        echo "What are the key considerations for deploying a Python Flask application to production with zero downtime using blue-green deployment, feature flags, and database migration strategies?" >> "$file"
        ;;
      "debugging")
        echo "How do I debug a sporadic race condition in a Go microservice that only appears under high concurrency, using tools like delvetrace, race detector, and logging?" >> "$file"
        ;;
      "documentation")
        echo "What are the best practices for maintaining up-to-date API documentation for a REST service with multiple versions, using tools like Swagger/OpenAPI, Redoc, and automated documentation generation from code comments?" >> "$file"
        ;;
      "planning")
        echo "How should I plan a software release cycle that balances feature development, technical debt reduction, and bug fixes, using agile frameworks like Scrum or Kanban, capacity planning, and sprint goals?" >> "$file"
        ;;
      "system-design")
        echo "How would you design a URL shortening service like bit.ly with analytics capabilities, considering scalability, redirect latency, and abuse prevention?" >> "$file"
        ;;
      "scaling")
        echo "What strategies should I use to horizontally scale a stateful application like a gaming leaderboard service, considering session persistence, sharding, and conflict resolution strategies?" >> "$file"
        ;;
    esac
    echo "" >> "$file"
    echo "---" >> "$file"
    echo "" >> "$file"
  done
done
echo "Generated prompts for ${#categories[@]} categories."
