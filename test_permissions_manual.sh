#!/bin/bash
# Manual Permissions Testing Script
# Run these commands to test the permissions system manually

BASE_URL="http://localhost:8002"
echo "🚀 Permissions Testing - Manual Commands"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check service health
echo -e "${BLUE}1. Checking service health...${NC}"
curl -s "$BASE_URL/health" | python -m json.tool
echo

# Create test users
echo -e "${BLUE}2. Creating test users...${NC}"

echo -e "${YELLOW}Creating Alice (Manager)...${NC}"
ALICE_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Manager", 
    "email": "alice@test.com",
    "role": "ADMIN"
  }')
echo "$ALICE_RESPONSE" | python -m json.tool
ALICE_ID=$(echo "$ALICE_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null || echo "0")
echo "Alice ID: $ALICE_ID"
echo

echo -e "${YELLOW}Creating Bob (Trader)...${NC}"
BOB_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Bob",
    "last_name": "Trader", 
    "email": "bob@test.com",
    "role": "EDITOR"
  }')
echo "$BOB_RESPONSE" | python -m json.tool
BOB_ID=$(echo "$BOB_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null || echo "0")
echo "Bob ID: $BOB_ID"
echo

echo -e "${YELLOW}Creating Charlie (Viewer)...${NC}"
CHARLIE_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Charlie",
    "last_name": "Viewer", 
    "email": "charlie@test.com",
    "role": "VIEWER"
  }')
echo "$CHARLIE_RESPONSE" | python -m json.tool
CHARLIE_ID=$(echo "$CHARLIE_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null || echo "0")
echo "Charlie ID: $CHARLIE_ID"
echo

# Test 1: Data Sharing - All Except Pattern
echo -e "${BLUE}3. Test: Data Sharing - Share with all except Bob${NC}"
echo "Command:"
echo "curl -X POST $BASE_URL/api/permissions/data-sharing \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"resource_types\": [\"positions\", \"holdings\"],"
echo "    \"scope\": \"all_except\","
echo "    \"excluded_users\": [$BOB_ID],"
echo "    \"notes\": \"Test: Share with all except Bob\""
echo "  }'"
echo

curl -X POST "$BASE_URL/api/permissions/data-sharing" \
  -H "Content-Type: application/json" \
  -d "{
    \"resource_types\": [\"positions\", \"holdings\"],
    \"scope\": \"all_except\",
    \"excluded_users\": [$BOB_ID],
    \"notes\": \"Test: Share with all except Bob\"
  }" | python -m json.tool
echo

# Test 2: Trading Permissions with Instrument Controls
echo -e "${BLUE}4. Test: Trading Permissions - Allow Bob to trade but restrict exit on HDFC${NC}"
echo "Command:"
echo "curl -X POST $BASE_URL/api/permissions/trading \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"grantee_user_id\": $BOB_ID,"
echo "    \"permissions\": ["
echo "      {\"action\": \"create\", \"scope\": \"all\"},"
echo "      {\"action\": \"modify\", \"scope\": \"all\"},"
echo "      {\"action\": \"exit\", \"scope\": \"blacklist\", \"instruments\": [\"NSE:HDFCBANK\", \"NSE:RELIANCE\"]}"
echo "    ],"
echo "    \"notes\": \"Test: Allow trading but restrict exit on specific instruments\""
echo "  }'"
echo

curl -X POST "$BASE_URL/api/permissions/trading" \
  -H "Content-Type: application/json" \
  -d "{
    \"grantee_user_id\": $BOB_ID,
    \"permissions\": [
      {\"action\": \"create\", \"scope\": \"all\"},
      {\"action\": \"modify\", \"scope\": \"all\"},
      {\"action\": \"exit\", \"scope\": \"blacklist\", \"instruments\": [\"NSE:HDFCBANK\", \"NSE:RELIANCE\"]}
    ],
    \"notes\": \"Test: Allow trading but restrict exit on specific instruments\"
  }" | python -m json.tool
echo

# Test 3: Trading Restrictions
echo -e "${BLUE}5. Test: Trading Restrictions - Block Charlie from high-risk instruments${NC}"
echo "Command:"
echo "curl -X POST $BASE_URL/api/permissions/restrictions/trading \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"target_user_id\": $CHARLIE_ID,"
echo "    \"restrictions\": ["
echo "      {\"type\": \"instrument_blacklist\", \"actions\": [\"all\"], \"instruments\": [\"NSE:YESBANK\", \"NSE:VODAFONE\"], \"enforcement\": \"HARD\"}"
echo "    ],"
echo "    \"notes\": \"Test: Block high-risk instruments\""
echo "  }'"
echo

curl -X POST "$BASE_URL/api/permissions/restrictions/trading" \
  -H "Content-Type: application/json" \
  -d "{
    \"target_user_id\": $CHARLIE_ID,
    \"restrictions\": [
      {\"type\": \"instrument_blacklist\", \"actions\": [\"all\"], \"instruments\": [\"NSE:YESBANK\", \"NSE:VODAFONE\"], \"enforcement\": \"HARD\"}
    ],
    \"notes\": \"Test: Block high-risk instruments\"
  }" | python -m json.tool
echo

# Test 4: Permission Checks
echo -e "${BLUE}6. Test: Permission Checks${NC}"

echo -e "${YELLOW}Check if Bob can CREATE NSE:HDFCBANK (should be allowed)${NC}"
curl -X POST "$BASE_URL/api/permissions/trading/check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $BOB_ID,
    \"action\": \"create\",
    \"resource\": \"positions\",
    \"instrument_key\": \"NSE:HDFCBANK\"
  }" | python -m json.tool
echo

echo -e "${YELLOW}Check if Bob can EXIT NSE:HDFCBANK (should be denied)${NC}"
curl -X POST "$BASE_URL/api/permissions/trading/check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $BOB_ID,
    \"action\": \"exit\",
    \"resource\": \"positions\",
    \"instrument_key\": \"NSE:HDFCBANK\"
  }" | python -m json.tool
echo

echo -e "${YELLOW}Check if Charlie can CREATE NSE:YESBANK (should be denied)${NC}"
curl -X POST "$BASE_URL/api/permissions/trading/check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $CHARLIE_ID,
    \"action\": \"create\",
    \"resource\": \"positions\",
    \"instrument_key\": \"NSE:YESBANK\"
  }" | python -m json.tool
echo

# Test 5: View Permission Settings
echo -e "${BLUE}7. Test: View Permission Settings${NC}"

echo -e "${YELLOW}Get data sharing settings${NC}"
curl -s "$BASE_URL/api/permissions/data-sharing/my-settings" | python -m json.tool
echo

echo -e "${YELLOW}Get viewers for positions${NC}"
curl -s "$BASE_URL/api/permissions/data-sharing/viewers?resource_type=positions" | python -m json.tool
echo

echo -e "${YELLOW}Get audit log${NC}"
curl -s "$BASE_URL/api/permissions/audit-log?limit=10" | python -m json.tool
echo

echo -e "${GREEN}🎉 Manual testing complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Check the responses above to verify permissions are working"
echo "2. Try different combinations of users and instruments"
echo "3. Test permission expiration by adding expires_at dates"
echo "4. Test permission revocation using the revoke endpoint"