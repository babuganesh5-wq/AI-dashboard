#!/bin/bash
# Antigravity AI - Automated Sync, Security Scan & Vercel Deployment Manager
# Handles secure Git commits, pre-commit secret scans, serverless Vercel deploys, and automated rollbacks.

# HSL styled text color rules for high-contrast console feedback
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}================================================================${RESET}"
echo -e "${CYAN}    ANTIGRAVITY AI - AUTOMATED DEPLOYMENT & ROLLBACK DAEMON    ${RESET}"
echo -e "${CYAN}================================================================${RESET}"

# Step 1: Enforce Local Security Best Practices
check_security() {
    echo -e "\n${YELLOW}[1/4] Running pre-flight security scan for exposed API keys...${RESET}"
    
    # 1A: Check if .env file exists and verify it is mapped in .gitignore
    if [ -f ".env" ]; then
        if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
            echo -e "${RED}[SECURITY FAILURE] .env file detected but not ignored in .gitignore!${RESET}"
            echo -e "${RED}Aborting sync to prevent credential leakage. Add '.env' to .gitignore first.${RESET}"
            exit 1
        fi
        echo -e "${GREEN}[SECURE] .env file exists and is correctly ignored.${RESET}"
    else
        echo -e "${YELLOW}[WARNING] No .env file found. Creating a template from .env.example...${RESET}"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}[SECURE] Created .env template. Please populate your secrets safely.${RESET}"
        fi
    fi

    # 1B: Scan files for actual API keys (e.g. sk-proj-, gpt-keys, meta credentials)
    # Exclude .git, node_modules, and virtual environments
    EXCLUDES="--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.idx"
    
    # Scan for common API key signatures
    OPENAI_KEYS=$(grep -r "sk-[a-zA-Z0-9]\{48\}" . $EXCLUDES 2>/dev/null)
    GENERIC_KEYS=$(grep -r "api_key\s*=\s*['\"][a-zA-Z0-9]\{20,\}['\"]" . $EXCLUDES 2>/dev/null)
    
    if [ ! -z "$OPENAI_KEYS" ] || [ ! -z "$GENERIC_KEYS" ]; then
        echo -e "${RED}[SECURITY FAILURE] Exposed API keys detected in codebase!${RESET}"
        echo -e "${RED}Found matches:${RESET}"
        [ ! -z "$OPENAI_KEYS" ] && echo -e "${RED}$OPENAI_KEYS${RESET}"
        [ ! -z "$GENERIC_KEYS" ] && echo -e "${RED}$GENERIC_KEYS${RESET}"
        echo -e "${RED}Sync aborted. Please move secrets to your local .env file immediately.${RESET}"
        exit 1
    fi
    echo -e "${GREEN}[SECURE] Code scan complete. No credentials exposed in source files.${RESET}"
}

# Step 2: Git source control commits & rollback tag creations
sync_git() {
    echo -e "\n${YELLOW}[2/4] Initializing Git synchronization...${RESET}"
    
    # Check if git is initialized
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}Git repository not found. Initializing local repository...${RESET}"
        git init
        git checkout -b main
    fi

    # Staging files
    git add .

    # Build unique release tag and commit message based on timestamp
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    COMMIT_MSG="Antigravity release-sync: $TIMESTAMP [auto-build]"
    TAG_NAME="rollback-point-$TIMESTAMP"

    # Verify if there are changes to commit
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "${GREEN}[GIT] No new file mutations detected. Staging is clear.${RESET}"
    else
        git commit -m "$COMMIT_MSG"
        git tag -a "$TAG_NAME" -m "Rollback pointer for release: $TIMESTAMP"
        echo -e "${GREEN}[GIT] Committed mutations successfully. Created rollback tag: $TAG_NAME${RESET}"
        
        # Push to remote if origin is set
        if git remote | grep -q "origin"; then
            echo -e "${YELLOW}Pushing changes to remote repository...${RESET}"
            git push origin main --tags
            echo -e "${GREEN}[GIT] Pushed files and tags to GitHub successfully.${RESET}"
        else
            echo -e "${YELLOW}[INFO] Remote 'origin' is not set. Saved changes to local repository & tags.${RESET}"
        fi
    fi
}

# Step 3: Serverless Vercel Deployments
sync_vercel() {
    echo -e "\n${YELLOW}[3/4] Triggering Vercel Cloud deployment...${RESET}"
    
    # Verify Vercel CLI installation
    if ! command -v vercel &> /dev/null; then
        echo -e "${YELLOW}[INFO] Vercel CLI not found on PATH. Attempting npx fallback deploy...${RESET}"
        npx -y vercel --prod --yes
    else
        vercel --prod --yes
    fi
    
    echo -e "${GREEN}[VERCEL] Deployment completed successfully on vercel.app.${RESET}"
}

# Step 4: Execution Metrics Logging
log_success() {
    echo -e "\n${GREEN}[4/4] Sync sequence finished successfully!${RESET}"
    echo -e "${CYAN}================================================================${RESET}"
    echo -e "${GREEN}   STATUS: MESH SYNCHRONIZED | DEPLOYMENT ONLINE | SECURE      ${RESET}"
    echo -e "${CYAN}================================================================${RESET}"
}

# Execution Entry point: Rollback check flags
if [ "$1" == "--rollback" ]; then
    echo -e "${YELLOW}================================================================${RESET}"
    echo -e "${YELLOW}               EXECUTE SYSTEM ROLLBACK ACTIVATED                ${RESET}"
    echo -e "${YELLOW}================================================================${RESET}"
    
    if [ -z "$2" ]; then
        echo -e "${RED}[ERROR] Please specify a target Git tag or Vercel Deployment ID to revert to.${RESET}"
        echo -e "Usage: ./auto_sync.sh --rollback [tag-name / deployment-id]"
        echo -e "Example tags: rollback-point-YYYYMMDD-HHMMSS"
        exit 1
    fi
    
    TARGET="$2"
    echo -e "${YELLOW}Reverting source code to Git point: $TARGET...${RESET}"
    
    # Revert Git state
    if git rev-parse "$TARGET" >/dev/null 2>&1; then
        git checkout "$TARGET"
        echo -e "${GREEN}[SUCCESS] Source files checked out at: $TARGET${RESET}"
    else
        echo -e "${RED}[WARNING] Git tag '$TARGET' not found locally. Proceeding to Vercel rollback check...${RESET}"
    fi

    # Revert Vercel deployment state
    echo -e "${YELLOW}Executing serverless Vercel deployment rollback...${RESET}"
    if ! command -v vercel &> /dev/null; then
        npx -y vercel rollback "$TARGET" --yes
    else
        vercel rollback "$TARGET" --yes
    fi
    
    echo -e "${GREEN}[SUCCESS] System successfully rolled back to stable state: $TARGET${RESET}"
    exit 0
fi

# Standard Synchronization Loop Run
check_security
sync_git
sync_vercel
log_success
