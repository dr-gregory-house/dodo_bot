#!/bin/bash
# Deploy group.json to production server

echo "Deploying group.json to server..."
ssh -i ~/.ssh/ubuntu_dodo_bot.pem ubuntu@45.12.4.173 << 'ENDSSH'
cat > ~/dodo_bot/data/group.json << 'EOF'
{
  "group_id": "-1003458096259"
}
EOF

echo "File created successfully:"
cat ~/dodo_bot/data/group.json
echo ""
echo "Restarting bot service..."
sudo systemctl restart dodo-bot.service
echo "Done! Bot restarted with group.json"
ENDSSH
