#!/bin/bash
# Test runner script for Project Bootstrap Backend

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Project Bootstrap Backend - Test Runner${NC}\n"

# Check if test database exists
echo "Checking test database..."
if ! psql -U postgres -lqt | cut -d \| -f 1 | grep -qw bootstrap_test; then
    echo -e "${YELLOW}Creating test database...${NC}"
    createdb -U postgres bootstrap_test || psql -U postgres -c "CREATE DATABASE bootstrap_test;"
fi

# Export test database URL
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/bootstrap_test"

# Run tests based on argument
case "${1:-all}" in
    all)
        echo -e "\n${GREEN}Running all tests...${NC}\n"
        pytest tests/ -v
        ;;

    projects)
        echo -e "\n${GREEN}Running project API tests...${NC}\n"
        pytest tests/test_api_projects.py -v
        ;;

    coverage)
        echo -e "\n${GREEN}Running tests with coverage...${NC}\n"
        pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    fast)
        echo -e "\n${GREEN}Running fast tests only...${NC}\n"
        pytest tests/ -v -m "not slow"
        ;;

    watch)
        echo -e "\n${GREEN}Running tests in watch mode...${NC}\n"
        pytest-watch tests/ -- -v
        ;;

    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Usage: ./run_tests.sh [all|projects|coverage|fast|watch]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Tests completed!${NC}"
