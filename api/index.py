"""
最もシンプルなVercelテスト用エンドポイント
"""

def handler(event, context):
    """直接的なVercelハンドラー"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': '{"message": "Hello from Vercel!", "status": "working"}'
    }