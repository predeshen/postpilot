#!/bin/bash
# Deploy Social Media Generator to AWS Lambda using SAM CLI
#
# Prerequisites:
#   - AWS CLI configured with valid credentials (aws configure)
#   - SAM CLI installed (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
#   - Docker running (for building the container image)
#
# Usage:
#   First deployment:  ./deploy-aws.sh --guided
#   Update deployment: ./deploy-aws.sh
#   Staging:           ./deploy-aws.sh --config-env staging

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Building SAM application ==="
sam build

if [[ "${1:-}" == "--guided" ]]; then
    echo "=== Running guided deployment (first time) ==="
    sam deploy --guided
else
    echo "=== Deploying to AWS ==="
    sam deploy "$@"
fi

echo ""
echo "=== Deployment complete ==="
echo ""
echo "To get your API URL:"
echo "  aws cloudformation describe-stacks --stack-name social-media-generator --query 'Stacks[0].Outputs[?OutputKey==\`ApiUrl\`].OutputValue' --output text"
echo ""
echo "To view logs:"
echo "  sam logs --stack-name social-media-generator --tail"
echo ""
echo "To delete the stack:"
echo "  sam delete --stack-name social-media-generator"
