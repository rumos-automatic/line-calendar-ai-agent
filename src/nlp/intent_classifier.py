"""
Intent classification for Japanese messages
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classify user intent from Japanese text"""
    
    def __init__(self):
        self.intent_patterns = {
            'add_event': [
                r'(追加|作成|登録|予約)',
                r'(〜に|〜で).*(ミーティング|会議|アポ|打ち合わせ)',
                r'\d+(時|:\d+).*(ミーティング|会議|アポ|打ち合わせ)',
                r'(明日|今日|明後日).*(ミーティング|会議|アポ|打ち合わせ|予定)',
            ],
            'list_events': [
                r'(予定|スケジュール).*?(教えて|見せて|確認|一覧)',
                r'(今日|明日|明後日|今週|来週).*?(予定|スケジュール).*?(は|？)',
                r'(何|なに).*?(予定|スケジュール)',
                r'(予定|スケジュール).*?(ある|あります)',
            ],
            'delete_event': [
                r'(削除|キャンセル|取り消し)',
                r'(予定|スケジュール).*?(削除|キャンセル|取り消し)',
                r'(ミーティング|会議|アポ|打ち合わせ).*?(削除|キャンセル|取り消し)',
            ],
            'update_event': [
                r'(変更|修正|更新)',
                r'(予定|スケジュール).*?(変更|修正|更新)',
                r'(時間|日時).*?(変更|修正)',
            ],
            'check_subscription': [
                r'(プラン|課金|契約)',
                r'(AIモード|AIエージェント).*?(使える|使えない|利用)',
                r'(残り|利用).*?(回数|使用)',
            ],
            'upgrade_plan': [
                r'(プラン|課金).*?(アップグレード|変更|申し込み)',
                r'(ベーシック|プレミアム).*?(プラン|契約)',
                r'AIモード.*?(使いたい|利用したい)',
            ]
        }
    
    def classify(self, text: str) -> str:
        """
        Classify intent from text
        
        Args:
            text: Input text
            
        Returns:
            Intent string
        """
        text = text.lower().strip()
        
        # Score each intent
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            scores[intent] = score
        
        # Return highest scoring intent
        if scores:
            best_intent = max(scores, key=scores.get)
            if scores[best_intent] > 0:
                return best_intent
        
        # Default classification based on simple heuristics
        return self._fallback_classification(text)
    
    def _fallback_classification(self, text: str) -> str:
        """Fallback classification using simple rules"""
        
        # If text contains time and activity, likely add_event
        if (re.search(r'\d+(時|:\d+)', text) and 
            any(word in text for word in ['ミーティング', '会議', 'アポ', '打ち合わせ', '予定'])):
            return 'add_event'
        
        # If asking about schedule
        if any(word in text for word in ['予定', 'スケジュール']) and text.endswith('？'):
            return 'list_events'
        
        # If contains question words
        if any(word in text for word in ['何', 'なに', 'いつ', 'どこ']):
            return 'list_events'
        
        # Default to unknown
        return 'unknown'