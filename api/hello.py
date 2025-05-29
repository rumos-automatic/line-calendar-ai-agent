"""
最もシンプルなVercelテスト
"""

def handler(request):
    """Vercel Python ランタイム用ハンドラー"""
    return {
        'statusCode': 200,
        'body': 'Hello from Python on Vercel!'
    }