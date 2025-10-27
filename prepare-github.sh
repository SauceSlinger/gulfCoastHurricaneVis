#!/bin/bash

# Gulf Coast Hurricane Visualization - GitHub Preparation Script
# This script prepares the repository for initial GitHub commit

set -e

echo "🌀 Gulf Coast Hurricane Visualization Dashboard"
echo "================================================"
echo "📦 Preparing repository for GitHub..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    echo "   Please install git first: sudo apt-get install git"
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo -e "${BLUE}📁 Initializing git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}"
fi

# Check for sensitive files
echo -e "${BLUE}🔍 Checking for sensitive files...${NC}"
SENSITIVE_FILES=(
    ".env"
    "*.key"
    "*.pem"
    "*secret*"
    "*password*"
    "*.db"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if ls $pattern 2>/dev/null | grep -q .; then
        echo -e "${YELLOW}⚠️  Found potentially sensitive files matching: $pattern${NC}"
        echo "   Make sure these are in .gitignore"
    fi
done

# Verify .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠️  .gitignore not found${NC}"
    echo "   Creating basic .gitignore..."
    cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.venv/
.env
*.db
*.log
EOF
    echo -e "${GREEN}✅ Created .gitignore${NC}"
else
    echo -e "${GREEN}✅ .gitignore exists${NC}"
fi

# Verify README exists
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ README.md not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ README.md exists${NC}"
fi

# Verify LICENSE exists
if [ ! -f "LICENSE" ]; then
    echo -e "${YELLOW}⚠️  LICENSE file not found${NC}"
    echo "   Consider adding a license (MIT recommended)"
else
    echo -e "${GREEN}✅ LICENSE exists${NC}"
fi

# Clean up Python cache files
echo -e "${BLUE}🧹 Cleaning Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Cache cleaned${NC}"

# Stage all files
echo -e "${BLUE}📝 Staging files for commit...${NC}"
git add .

# Show status
echo ""
echo -e "${BLUE}📊 Repository status:${NC}"
git status

# Count files to be committed
FILE_COUNT=$(git diff --cached --name-only | wc -l)
echo ""
echo -e "${GREEN}✅ $FILE_COUNT files ready to commit${NC}"

# Ask for confirmation
echo ""
echo -e "${YELLOW}Ready to create initial commit?${NC}"
echo "This will commit all staged files to your local repository."
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Commit cancelled. Files remain staged.${NC}"
    exit 0
fi

# Create initial commit
echo -e "${BLUE}💾 Creating initial commit...${NC}"
git commit -m "feat: initial commit - Gulf Coast Hurricane Visualization Dashboard

- Interactive dashboard with 4 tabs (Overview, Timeline, Map, Analysis)
- Docker support for easy deployment
- 19,066+ hurricane records (1975-2021)
- Real-time filtering and data exploration
- Professional loading screen with progress tracking
- Matplotlib/Cartopy visualizations
- CustomTkinter modern UI
- PostgreSQL support with CSV fallback

Features:
- Overview: Dataset summary with statistics and top storms
- Timeline: Interactive charts with year/month/category sliders
- Map: Geographic visualization with storm track filtering
- Analysis: Statistical breakdowns and trend analysis

Ready for deployment with Docker or local Python installation."

echo -e "${GREEN}✅ Initial commit created${NC}"

# Show log
echo ""
echo -e "${BLUE}📜 Commit log:${NC}"
git log --oneline -1

# Instructions for GitHub
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Repository ready for GitHub!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1️⃣  Create a new repository on GitHub:"
echo "   https://github.com/new"
echo ""
echo "2️⃣  Link your local repository to GitHub:"
echo -e "   ${YELLOW}git remote add origin https://github.com/YOUR_USERNAME/gulfCoastHurricaneVis.git${NC}"
echo ""
echo "3️⃣  Push your code to GitHub:"
echo -e "   ${YELLOW}git branch -M master${NC}"
echo -e "   ${YELLOW}git push -u origin master${NC}"
echo ""
echo "4️⃣  (Optional) Add topics/tags on GitHub:"
echo "   - hurricane-visualization"
echo "   - data-science"
echo "   - python"
echo "   - customtkinter"
echo "   - cartopy"
echo "   - docker"
echo "   - weather-data"
echo ""
echo -e "${BLUE}📝 Don't forget to:${NC}"
echo "   - Add a repository description on GitHub"
echo "   - Enable GitHub Pages (if you add documentation)"
echo "   - Add collaborators (if applicable)"
echo "   - Set up branch protection rules (recommended)"
echo ""
echo -e "${GREEN}🎉 Happy coding!${NC}"
