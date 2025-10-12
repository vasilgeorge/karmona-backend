"""
Custom browser_session that uses explicit AWS credentials.
Based on bedrock_agentcore but accepts custom credentials.
"""
import boto3
import uuid
import time
import base64
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Tuple, Dict, Any
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials


class KarmonaBrowserClient:
    """Browser client with explicit credentials."""
    
    def __init__(self, browser_id: str, session_id: str, control_client, data_client, region: str, credentials: Credentials):
        self.browser_id = browser_id
        self.session_id = session_id
        self.control_client = control_client
        self.data_client = data_client
        self.region = region
        self.credentials = credentials
        self._ws_url = None
        self._headers = None
    
    def _generate_sigv4_headers(self, ws_url: str) -> Dict[str, str]:
        """Generate SigV4 authentication headers for WebSocket connection."""
        parsed_url = urlparse(ws_url)
        host = parsed_url.netloc
        path = parsed_url.path
        
        # Generate timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        # Create AWS request for signing
        request = AWSRequest(
            method='GET',
            url=f'https://{host}{path}',
            headers={
                'host': host,
                'x-amz-date': timestamp
            }
        )
        
        # Sign with SigV4
        auth = SigV4Auth(self.credentials, "bedrock-agentcore", self.region)
        auth.add_auth(request)
        
        # Generate WebSocket key
        ws_key = base64.b64encode(secrets.token_bytes(16)).decode()
        
        # Build headers as dictionary for Playwright
        headers = {
            'Host': host,
            'X-Amz-Date': timestamp,
            'Authorization': request.headers['Authorization'],
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Key': ws_key,
            'User-Agent': 'Karmona-BrowserAgent/1.0'
        }
        
        return headers
    
    def generate_ws_headers(self) -> Tuple[str, Dict[str, str]]:
        """Generate WebSocket URL and headers for browser connection."""
        if self._ws_url is None:
            # Get browser session details
            session_response = self.data_client.get_browser_session(
                browserIdentifier=self.browser_id,
                sessionId=self.session_id
            )
            
            # Extract automation stream endpoint
            streams = session_response.get('streams', {})
            automation_stream = streams.get('automationStream', {})
            self._ws_url = automation_stream.get('streamEndpoint')
            
            if not self._ws_url:
                raise Exception("No automation stream endpoint found")
            
            # Generate signed headers for WebSocket authentication
            self._headers = self._generate_sigv4_headers(self._ws_url)
        
        return self._ws_url, self._headers


@contextmanager
def karmona_browser_session(
    region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
):
    """
    Context manager that creates a browser session with explicit credentials.
    
    Args:
        region: AWS region
        aws_access_key_id: AWS access key
        aws_secret_access_key: AWS secret key
        
    Yields:
        KarmonaBrowserClient: Client for browser operations
    """
    control_client = None
    data_client = None
    browser_id = None
    session_id = None
    
    try:
        # Create clients with explicit credentials
        control_client = boto3.client(
            'bedrock-agentcore-control',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        data_client = boto3.client(
            'bedrock-agentcore',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        
        # Create browser
        browser_name = f"karmona_browser_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        create_response = control_client.create_browser(
            name=browser_name,
            networkConfiguration={
                "networkMode": "PUBLIC"
            }
        )
        browser_id = create_response['browserId']
        print(f"✅ Created browser: {browser_id}")
        
        # Start browser session
        session_name = f"session_{uuid.uuid4().hex[:8]}"
        session_response = data_client.start_browser_session(
            browserIdentifier=browser_id,
            name=session_name,
            sessionTimeoutSeconds=3600
        )
        session_id = session_response['sessionId']
        print(f"✅ Started session: {session_id}")
        
        # Create frozen credentials for SigV4 signing
        creds = Credentials(
            access_key=aws_access_key_id,
            secret_key=aws_secret_access_key,
        )
        
        # Create and yield the client
        client = KarmonaBrowserClient(
            browser_id,
            session_id,
            control_client,
            data_client,
            region,
            creds,
        )
        yield client
        
    finally:
        # Cleanup
        try:
            if session_id and data_client:
                data_client.stop_browser_session(
                    browserIdentifier=browser_id,
                    sessionId=session_id
                )
                print(f"🛑 Stopped session: {session_id}")
        except Exception as e:
            print(f"⚠️  Error stopping session: {e}")
        
        try:
            if browser_id and control_client:
                control_client.delete_browser(browserId=browser_id)
                print(f"🗑️  Deleted browser: {browser_id}")
        except Exception as e:
            print(f"⚠️  Error deleting browser: {e}")
