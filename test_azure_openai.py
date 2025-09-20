#!/usr/bin/env python3
"""Test script to validate Azure OpenAI API key and endpoint."""

import os
import sys
from openai import AzureOpenAI

def test_azure_openai():
    """Test Azure OpenAI API access."""
    
    # Your configuration
    api_key = input("Enter your Azure OpenAI API key: ").strip()
    endpoint = "https://sre-agent-resource.cognitiveservices.azure.com/"
    api_version = "2025-01-01-preview"
    model_name = "o4-mini"
    
    print(f"\n🔧 Testing Azure OpenAI Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   API Version: {api_version}")
    print(f"   Model: {model_name}")
    print(f"   API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}")
    
    try:
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        print(f"\n🚀 Testing API connection...")
        
        # Test with a simple completion
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello! Please respond with 'API test successful' if you can read this."}],
                max_completion_tokens=50,
                temperature=0.1
            )
        except Exception as temp_error:
            if "temperature" in str(temp_error).lower():
                print(f"   Note: Model doesn't support custom temperature, using default")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Hello! Please respond with 'API test successful' if you can read this."}],
                    max_completion_tokens=50
                )
            else:
                raise temp_error
        
        response_text = response.choices[0].message.content
        print(f"✅ API Test Successful!")
        print(f"   Response: {response_text}")
        
        # Test with a security analysis prompt
        print(f"\n🔍 Testing security analysis capability...")
        
        security_prompt = """You are a security engineer. Analyze this simple workflow for security issues:

```yaml
name: test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v1
      - run: echo "Hello World"
```

Respond with JSON format:
{
  "findings": [],
  "analysis_summary": {
    "files_reviewed": 1,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0,
    "review_completed": true
  }
}"""
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": security_prompt}],
                max_completion_tokens=500,
                temperature=0.1
            )
        except Exception as temp_error:
            if "temperature" in str(temp_error).lower():
                print(f"   Note: Model doesn't support custom temperature, using default")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": security_prompt}],
                    max_completion_tokens=500
                )
            else:
                raise temp_error
        
        response_text = response.choices[0].message.content
        print(f"✅ Security Analysis Test Successful!")
        print(f"   Response: {response_text[:200]}...")
        
        print(f"\n🎉 All tests passed! Your Azure OpenAI setup is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed!")
        print(f"   Error: {str(e)}")
        
        # Provide specific troubleshooting tips
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print(f"\n💡 Troubleshooting:")
            print(f"   - Check if your API key is correct")
            print(f"   - Verify the API key has access to the model")
        elif "404" in str(e) or "not found" in str(e).lower():
            print(f"\n💡 Troubleshooting:")
            print(f"   - Check if the model 'o4-mini' is deployed in your Azure OpenAI resource")
            print(f"   - Verify the model name is correct")
        elif "400" in str(e) or "bad request" in str(e).lower():
            print(f"\n💡 Troubleshooting:")
            print(f"   - Check if the API version is correct")
            print(f"   - Verify the endpoint URL is correct")
        
        return False

if __name__ == "__main__":
    print("🧪 Azure OpenAI API Key Tester")
    print("=" * 40)
    
    success = test_azure_openai()
    
    if success:
        print(f"\n✅ Your Azure OpenAI setup is ready for the GitHub Action!")
        print(f"\n📋 Next steps:")
        print(f"   1. Add your API key as a GitHub secret: AZURE_OPENAI_API_KEY")
        print(f"   2. Use the action configuration I provided earlier")
    else:
        print(f"\n❌ Please fix the issues above before using the GitHub Action.")
    
    sys.exit(0 if success else 1)
