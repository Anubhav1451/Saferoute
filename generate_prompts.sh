#!/bin/bash
# Script to generate prompt files for each category

categories=("architecture" "backend" "frontend" "security" "database" "performance" "testing" "ai" "devops" "code-review" "refactoring" "production" "debugging" "documentation" "planning" "system-design" "scaling")

for category in "${categories[@]}"; do
  file="./.claude/Engineer's Framework/prompts/$category/prompts.md"
  echo "# $category Prompts" > "$file"
  echo "" >> "$file"
  for i in {1..20}; do
    echo "## Prompt $i" >> "$file"
    echo "" >> "$file"
    case $category in
      "architecture")
        echo "How should I design a microservices architecture for a $RANDOM user e-commerce platform with high availability requirements?" >> "$file"
        ;;
      "backend")
        echo "What are the best practices for designing a RESTful API for a $RANDOM user social media application?" >> "$file"
        ;;
      "frontend")
        echo "How can I optimize the performance of a React application with large datasets and complex state management?" >> "$file"
        ;;
      "security")
        echo "What security measures should I implement to protect against OWASP Top 10 vulnerabilities in a $RANDOM user web application?" >> "$file"
        ;;
      "database")
        echo "When should I choose a NoSQL database over a relational database for a $RANDOM user application with varying data patterns?" >> "$file"
        ;;
      "performance")
        echo "How do I identify and resolve performance bottlenecks in a $RANDOM user distributed system under peak load?" >> "$file"
        ;;
      "testing")
        echo "What testing strategy should I use for a $RANDOM user microservices architecture to ensure adequate coverage without slowing down development?" >> "$file"
        ;;
      "ai")
        echo "How should I approach building a recommendation system for a $RANDOM user e-commerce platform using collaborative filtering?" >> "$file"
        ;;
      "devops")
        echo "What are the essential components of a CI/CD pipeline for a $RANDOM user Kubernetes-based microservices application?" >> "$file"
        ;;
      "code-review")
        echo "What should I look for during a code review of a $RANDOM user Python Django application to ensure maintainability and security?" >> "$file"
        ;;
      "refactoring")
        echo "How should I refactor a large monolithic $RANDOM user Java application to improve modularity and reduce technical debt?" >> "$file"
        ;;
      "production")
        echo "What are the key considerations for deploying a $RANDOM user application to production with zero downtime and blue-green deployment strategy?" >> "$file"
        ;;
      "debugging")
        echo "How do I debug a sporadic race condition in a $RANDOM user Go microservice that only appears under high concurrency?" >> "$file"
        ;;
      "documentation")
        echo "What are the best practices for maintaining up-to-date API documentation for a $RANDOM user REST service with multiple versions?" >> "$file"
        ;;
      "planning")
        echo "How should I plan a $RANDOM user software release cycle that balances feature development, technical debt reduction, and bug fixes?" >> "$file"
        ;;
      "system-design")
        echo "How would you design a URL shortening service like bit.ly for a $RANDOM user user base with analytics capabilities?" >> "$file"
        ;;
      "scaling")
        echo "What strategies should I use to horizontally scale a $RANDOM user stateful application like a gaming leaderboard service?" >> "$file"
        ;;
    esac
    echo "" >> "$file"
    echo "---" >> "$file"
    echo "" >> "$file"
  done
done