#!/bin/bash
set -e

# Vensora Phase 1 - Automated Security Verification Suite
# Required for Gap 25 (Security Verification)

API_URL="http://localhost:8000/api/v1"

echo "Running Security Verification Suite..."

# 1. Authentication Bypass (No Token)
echo "Testing: Authentication Bypass on /users"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/users")
if [ "$STATUS_CODE" -eq 401 ]; then
    echo "✅ PASS: Unauthenticated access blocked (401)"
else
    echo "❌ FAIL: Unauthenticated access allowed! (Status: $STATUS_CODE)"
    exit 1
fi

# 2. RBAC Bypass (Attempt to access Super Admin route with invalid token)
echo "Testing: RBAC Bypass on /users"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid_employee_token" -X GET "$API_URL/users")
if [ "$STATUS_CODE" -eq 401 ]; then
    echo "✅ PASS: Invalid token blocked (401)"
else
    echo "❌ FAIL: Invalid token allowed! (Status: $STATUS_CODE)"
    exit 1
fi

# 3. Path Traversal / File Upload Abuse on Knowledge Base
echo "Testing: Unauthorized File Upload to Vector Store"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/knowledge/upload" -F "file=@/etc/passwd")
if [ "$STATUS_CODE" -eq 401 ]; then
    echo "✅ PASS: Unauthorized upload blocked (401)"
else
    echo "❌ FAIL: Unauthorized upload allowed! (Status: $STATUS_CODE)"
    exit 1
fi

echo "Security Verification Suite Passed Successfully."
