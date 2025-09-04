#!/bin/bash

# A script to safely initialize a Git repository and push it to GitHub.

# --- Safety Check ---
if ! grep -q ".env" .gitignore; then
  echo "🔴 DANGER: Your .gitignore file does not seem to be ignoring the .env file."
  echo "Please fix this before proceeding. Aborting."
  exit 1
fi

echo "✅ Safety check passed: .env is in your .gitignore."
echo ""

# --- Get Repository URL ---
read -p "Enter your new GitHub repository SSH URL (e.g., git@github.com:your-username/your-repo.git): " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo "🔴 ERROR: GitHub URL cannot be empty. Aborting."
    exit 1
fi

# --- Initialize Git Repository ---
if [ ! -d ".git" ]; then
    echo "🔧 Initializing a new Git repository..."
    git init
    git branch -M main
else
    echo "✅ Git repository already initialized."
fi

# --- Add, Commit, and Push ---
echo "➕ Adding all project files to staging (respecting .gitignore)..."
git add .

echo "📝 Creating the first commit..."
git commit -m "feat: Initial commit of the Netguard project"

echo "🔗 Setting the remote origin to your GitHub repository..."
# Check if remote 'origin' already exists and set it, otherwise add it
if git remote | grep -q "origin"; then
    git remote set-url origin "$GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
fi

echo "🚀 Pushing your project to GitHub via SSH..."
git push -u origin main

echo ""
echo "🎉 SUCCESS! Your project has been pushed to GitHub."
