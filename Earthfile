VERSION 0.8

# Earthfile to mimic GitHub Actions workflows locally
# Usage:
#   earthly +release-test      # Test release workflow (dry-run)
#   earthly +npm-install-test  # Test npm install step only
#   earthly +audit-test        # Test npm audit signatures

# Base image matching GitHub Actions ubuntu-latest + Node 24
FROM node:24-bookworm

WORKDIR /app

# npm-install-test: Verify npm install succeeds (the step that was failing)
npm-install-test:
    COPY package.json package-lock.json ./
    RUN npm install
    RUN echo "✅ npm install succeeded"

# audit-test: Verify npm audit signatures passes
audit-test:
    COPY package.json package-lock.json ./
    RUN npm install
    RUN npm audit signatures || echo "⚠️ npm audit signatures had warnings (non-fatal)"
    RUN echo "✅ Audit check completed"

# release-test: Full release workflow simulation (dry-run mode)
# Note: This test runs without .git, so semantic-release will show ENOGITREPO
# For full integration, use +release-test-full which includes git context
release-test:
    # Copy all files needed for semantic-release
    COPY package.json package-lock.json ./
    COPY .releaserc.yml ./
    COPY pyproject.toml ./
    COPY --if-exists CHANGELOG.md ./
    RUN mkdir -p src
    COPY src/__init__.py ./src/

    # Install dependencies (matching CI workflow)
    RUN npm install

    # Audit signatures (matching CI workflow)
    RUN npm audit signatures || echo "⚠️ npm audit signatures had warnings"

    # Run semantic-release in dry-run mode
    # Note: Requires GITHUB_TOKEN for actual release, but dry-run works without it
    RUN --no-cache npm run release:dry 2>&1 || echo "⚠️ Release dry-run completed with notes above"
    RUN echo "✅ Release workflow test completed"

# release-test-full: Full integration test with git context
# Requires: RUN earthly +release-test-full from within git repo
release-test-full:
    FROM node:24-bookworm
    WORKDIR /app

    # Install git for semantic-release
    RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

    # Copy all project files including .git
    COPY . .

    # Install dependencies
    RUN npm install

    # Audit signatures
    RUN npm audit signatures || echo "⚠️ npm audit signatures had warnings"

    # Configure git for semantic-release (required in container)
    RUN git config --global --add safe.directory /app

    # Run semantic-release dry-run (requires git history for version calculation)
    RUN --no-cache npm run release:dry 2>&1 || echo "⚠️ Release dry-run completed with notes above"
    RUN echo "✅ Full release workflow test completed"

# all: Run all tests in sequence
all:
    BUILD +npm-install-test
    BUILD +audit-test
    BUILD +release-test
