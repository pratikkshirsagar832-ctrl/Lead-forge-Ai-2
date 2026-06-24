#!/bin/bash
set -e

echo "=== Hyperclients Deploy Script ==="

cd /root

# Clone or pull latest code
if [ -d "Lead-forge-Ai-2" ]; then
  cd Lead-forge-Ai-2
  git pull
else
  git clone https://github.com/pratikkshirsagar832-ctrl/Lead-forge-Ai-2.git
  cd Lead-forge-Ai-2
fi

# Ensure frontend .env.local has all keys
cat > frontend/.env.local << 'ENVEOF'
NEXT_PUBLIC_API_URL=https://hyperclients.online
NEXT_PUBLIC_SUPABASE_URL=https://wtradahkkpbkbhmkkpal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cmFkYWhra3Bia2JobWtrcGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwMDcyNjcsImV4cCI6MjA5NjU4MzI2N30.erQe6RS6nAog2OinQQdDiwWLe4yAutq_70eKdcGnTDg
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_live_T1w6TIu4oOl1dt
GOOGLE_SEARCH_API_KEY=AIzaSyAeMXbKN7AiaEh5J_GNkhEZnB8WjaAoihA
OPENAI_API_KEY=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
ENVEOF

# Backend env
cat > backend/.env << 'ENVEOF'
ENVIRONMENT=production
SUPABASE_URL=https://wtradahkkpbkbhmkkpal.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cmFkYWhra3Bia2JobWtrcGFsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTAwNzI2NywiZXhwIjoyMDk2NTgzMjY3fQ.QUKn8jhwCSyT1mnsMIq4dhPZND7xzG5VWxO5heO4fJI
OPENAI_API_KEY=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
RAZORPAY_KEY_ID=rzp_live_T1w6TIu4oOl1dt
RAZORPAY_KEY_SECRET=Q51LHnmMnVRFcxafMELkH9hW
ENVEOF

# Stop old containers
cd /root/Lead-forge-Ai-2
docker compose down 2>/dev/null || true

# Build and start
docker compose up -d --build

echo "=== Deploy complete! ==="
echo "Frontend: http://$(curl -s ifconfig.me):3000"
echo "Backend:  http://$(curl -s ifconfig.me):8000"
echo ""
echo "Check logs: docker compose logs -f"
