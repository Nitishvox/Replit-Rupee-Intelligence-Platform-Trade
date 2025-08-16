import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

class NLPParser:
    """Natural Language Processing parser for extracting entities from transaction narratives"""
    
    def __init__(self):
        # Predefined patterns for entity extraction
        self.patterns = {
            'amount': [
                r'(?:Rs\.?\s*|INR\s*|USD\s*|EUR\s*|GBP\s*|SGD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(?:amount|sum|value|worth|payment)\s+(?:of\s+)?(?:Rs\.?\s*|INR\s*|USD\s*|EUR\s*|GBP\s*|SGD\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:Rs\.?|INR|USD|EUR|GBP|SGD)'
            ],
            'account': [
                r'(?:account|acc|a/c)\s*(?:no|number|#)?\s*[:\-]?\s*([A-Z0-9]{8,20})',
                r'([A-Z0-9]{10,16})\s*(?:account|acc)',
                r'(?:from|to)\s+(?:account|acc)\s+([A-Z0-9]{8,20})'
            ],
            'date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(?:on|dated|date)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
            ],
            'reference': [
                r'(?:ref|reference|txn|transaction)\s*(?:no|number|#|id)?\s*[:\-]?\s*([A-Z0-9]{6,20})',
                r'(?:UTR|NEFT|RTGS|UPI)\s*[:\-]?\s*([A-Z0-9]{6,20})',
                r'([A-Z0-9]{8,16})\s*(?:ref|reference)'
            ],
            'bank': [
                r'(?:bank|financial\s+institution)\s*[:\-]?\s*([A-Z][A-Za-z\s&]{2,30})',
                r'([A-Z][A-Za-z\s&]{2,30})\s+(?:bank|banking)',
                r'(?:ICICI|HDFC|SBI|AXIS|PNB|BOB|CANARA|UNION|INDIAN)\s*(?:BANK)?'
            ],
            'purpose': [
                r'(?:purpose|for|towards)\s*[:\-]?\s*([A-Za-z\s]{5,50})',
                r'(?:payment\s+for|settlement\s+of)\s+([A-Za-z\s]{5,50})',
                r'(?:export|import|trade|business)\s+([A-Za-z\s]{3,30})'
            ],
            'currency': [
                r'\b(INR|USD|EUR|GBP|SGD|AED|JPY|RUB)\b',
                r'(?:Indian\s+Rupees?|US\s+Dollars?|Euros?|British\s+Pounds?|Singapore\s+Dollars?)',
                r'(?:Rs\.?|₹|\$|€|£)'
            ],
            'entity': [
                r'(?:entity|company|firm|corporation)\s*[:\-]?\s*([A-Z][A-Za-z\s&\.]{2,40})',
                r'([A-Z][A-Za-z\s&\.]{2,40})\s+(?:ltd|limited|inc|corp|pvt)',
                r'(?:M/s|Messrs)\s+([A-Z][A-Za-z\s&\.]{2,40})'
            ]
        }
        
        # Common trade-related keywords
        self.trade_keywords = {
            'export': ['export', 'exports', 'exported', 'exporting', 'shipment', 'shipped'],
            'import': ['import', 'imports', 'imported', 'importing', 'received', 'procurement'],
            'payment': ['payment', 'settlement', 'remittance', 'transfer', 'credit', 'debit'],
            'trade': ['trade', 'trading', 'commercial', 'business', 'transaction'],
            'finance': ['finance', 'financing', 'loan', 'credit', 'advance', 'facility']
        }
        
        # Country and region mappings
        self.country_patterns = {
            'USA': ['usa', 'united states', 'america', 'us', 'new york', 'california'],
            'Germany': ['germany', 'german', 'berlin', 'munich', 'hamburg'],
            'UK': ['uk', 'united kingdom', 'britain', 'england', 'london', 'scotland'],
            'Singapore': ['singapore', 'sg', 'singapura'],
            'Russia': ['russia', 'russian', 'moscow', 'petersburg'],
            'UAE': ['uae', 'dubai', 'abu dhabi', 'emirates', 'sharjah']
        }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract all entities from transaction narrative text"""
        
        if not text or not isinstance(text, str):
            return self._empty_entities()
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        entities = {}
        
        # Extract each entity type
        for entity_type, patterns in self.patterns.items():
            extracted = self._extract_entity_type(cleaned_text, patterns, entity_type)
            entities[entity_type] = extracted
        
        # Extract trade context
        entities['trade_context'] = self._extract_trade_context(cleaned_text)
        
        # Extract country/region
        entities['country'] = self._extract_country(cleaned_text)
        
        # Calculate confidence score
        entities['confidence_score'] = self._calculate_confidence(entities)
        
        # Add processing metadata
        entities['processed_at'] = datetime.now()
        entities['original_text'] = text
        entities['cleaned_text'] = cleaned_text
        
        return entities
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        
        # Convert to lowercase for pattern matching
        cleaned = text.lower()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters but keep important ones
        cleaned = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\/\&\#\@\$\€\£\₹]', ' ', cleaned)
        
        # Normalize common abbreviations
        abbreviations = {
            'a/c': 'account',
            'acc': 'account',
            'txn': 'transaction',
            'ref': 'reference',
            'amt': 'amount',
            'dt': 'date',
            'cr': 'credit',
            'dr': 'debit'
        }
        
        for abbrev, full_form in abbreviations.items():
            cleaned = re.sub(r'\b' + re.escape(abbrev) + r'\b', full_form, cleaned)
        
        return cleaned.strip()
    
    def _extract_entity_type(self, text: str, patterns: List[str], entity_type: str) -> List[str]:
        """Extract specific entity type using patterns"""
        
        extracted = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    # Take the first capturing group
                    entity_value = match.group(1).strip()
                else:
                    # Take the whole match if no capturing groups
                    entity_value = match.group(0).strip()
                
                # Clean and validate the extracted entity
                cleaned_entity = self._clean_entity(entity_value, entity_type)
                if cleaned_entity and cleaned_entity not in extracted:
                    extracted.append(cleaned_entity)
        
        return extracted[:5]  # Limit to top 5 matches
    
    def _clean_entity(self, entity: str, entity_type: str) -> Optional[str]:
        """Clean and validate extracted entity"""
        
        if not entity or len(entity.strip()) < 2:
            return None
        
        entity = entity.strip()
        
        # Type-specific cleaning
        if entity_type == 'amount':
            # Remove commas and validate numeric
            cleaned = re.sub(r'[,\s]', '', entity)
            try:
                float(cleaned)
                return cleaned
            except ValueError:
                return None
        
        elif entity_type == 'account':
            # Account numbers should be alphanumeric
            if re.match(r'^[A-Z0-9]{8,20}$', entity.upper()):
                return entity.upper()
            return None
        
        elif entity_type == 'reference':
            # Reference numbers should be alphanumeric
            if re.match(r'^[A-Z0-9]{6,20}$', entity.upper()):
                return entity.upper()
            return None
        
        elif entity_type == 'date':
            # Validate date format
            if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', entity):
                return entity
            return None
        
        elif entity_type in ['bank', 'entity', 'purpose']:
            # Text entities - capitalize properly
            if 3 <= len(entity) <= 50:
                return entity.title()
            return None
        
        elif entity_type == 'currency':
            # Normalize currency codes
            currency_map = {
                'rs': 'INR', 'rupees': 'INR', 'rupee': 'INR',
                'dollars': 'USD', 'dollar': 'USD',
                'euros': 'EUR', 'euro': 'EUR',
                'pounds': 'GBP', 'pound': 'GBP'
            }
            normalized = currency_map.get(entity.lower(), entity.upper())
            if normalized in ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'AED', 'JPY', 'RUB']:
                return normalized
            return None
        
        return entity
    
    def _extract_trade_context(self, text: str) -> Dict[str, Any]:
        """Extract trade-related context from text"""
        
        context = {
            'type': 'unknown',
            'keywords': [],
            'direction': 'unknown',
            'urgency': 'normal'
        }
        
        # Identify trade type
        for trade_type, keywords in self.trade_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    context['type'] = trade_type
                    context['keywords'].append(keyword)
                    break
        
        # Determine trade direction
        if any(word in text for word in ['export', 'exported', 'outgoing', 'send', 'remit']):
            context['direction'] = 'outbound'
        elif any(word in text for word in ['import', 'imported', 'incoming', 'receive', 'collection']):
            context['direction'] = 'inbound'
        
        # Assess urgency
        urgency_indicators = {
            'urgent': ['urgent', 'immediate', 'asap', 'emergency'],
            'high': ['priority', 'expedite', 'rush', 'fast'],
            'normal': ['regular', 'standard', 'normal']
        }
        
        for urgency_level, indicators in urgency_indicators.items():
            if any(indicator in text for indicator in indicators):
                context['urgency'] = urgency_level
                break
        
        return context
    
    def _extract_country(self, text: str) -> Optional[str]:
        """Extract country/region from text"""
        
        for country, patterns in self.country_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return country
        
        return None
    
    def _calculate_confidence(self, entities: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        
        confidence = 0.0
        total_weight = 0.0
        
        # Entity type weights
        weights = {
            'amount': 0.25,
            'account': 0.20,
            'reference': 0.15,
            'date': 0.10,
            'bank': 0.10,
            'currency': 0.10,
            'entity': 0.05,
            'purpose': 0.05
        }
        
        for entity_type, weight in weights.items():
            if entity_type in entities and entities[entity_type]:
                # More entities of a type = higher confidence
                entity_count = len(entities[entity_type])
                entity_confidence = min(1.0, entity_count / 3.0)  # Cap at 3 entities
                confidence += weight * entity_confidence
            
            total_weight += weight
        
        # Normalize to 0-1 scale
        if total_weight > 0:
            confidence = confidence / total_weight
        
        # Bonus for trade context
        if entities.get('trade_context', {}).get('type') != 'unknown':
            confidence += 0.1
        
        # Bonus for country identification
        if entities.get('country'):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _empty_entities(self) -> Dict[str, Any]:
        """Return empty entities structure"""
        
        return {
            'amount': [],
            'account': [],
            'date': [],
            'reference': [],
            'bank': [],
            'purpose': [],
            'currency': [],
            'entity': [],
            'trade_context': {'type': 'unknown', 'keywords': [], 'direction': 'unknown', 'urgency': 'normal'},
            'country': None,
            'confidence_score': 0.0,
            'processed_at': datetime.now(),
            'original_text': '',
            'cleaned_text': ''
        }
    
    def analyze_narrative_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis for transaction narratives"""
        
        if not text:
            return {'sentiment': 'neutral', 'confidence': 0.0}
        
        # Simple keyword-based sentiment analysis
        positive_words = ['successful', 'complete', 'approved', 'confirmed', 'cleared', 'processed']
        negative_words = ['failed', 'rejected', 'denied', 'error', 'invalid', 'cancelled', 'declined']
        neutral_words = ['pending', 'processing', 'review', 'verification', 'checking']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {'sentiment': 'neutral', 'confidence': 0.0}
        
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = 'positive'
            confidence = positive_count / total_sentiment_words
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = 'negative'
            confidence = negative_count / total_sentiment_words
        else:
            sentiment = 'neutral'
            confidence = max(neutral_count, max(positive_count, negative_count)) / total_sentiment_words
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'neutral_indicators': neutral_count
        }
    
    def extract_compliance_indicators(self, text: str) -> Dict[str, Any]:
        """Extract compliance-related indicators from narrative"""
        
        compliance_patterns = {
            'kyc': r'\b(?:kyc|know your customer|customer due diligence|cdd)\b',
            'aml': r'\b(?:aml|anti money laundering|money laundering)\b',
            'sanctions': r'\b(?:sanction|sanctioned|ofac|embargo)\b',
            'documentation': r'\b(?:documents?|invoice|bill of lading|letter of credit|lc)\b',
            'reporting': r'\b(?:report|reporting|declaration|regulatory)\b',
            'verification': r'\b(?:verify|verification|validate|validation|confirm)\b'
        }
        
        indicators = {}
        text_lower = text.lower()
        
        for indicator_type, pattern in compliance_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            indicators[indicator_type] = len(matches) > 0
        
        # Calculate compliance score
        compliance_score = sum(indicators.values()) / len(indicators)
        
        return {
            'indicators': indicators,
            'compliance_score': compliance_score,
            'compliance_mentions': sum(indicators.values())
        }
    
    def suggest_narrative_improvements(self, text: str) -> List[str]:
        """Suggest improvements for transaction narratives"""
        
        suggestions = []
        
        if not text or len(text.strip()) < 10:
            suggestions.append("Narrative is too short. Please provide more detailed description.")
            return suggestions
        
        entities = self.extract_entities(text)
        
        # Check for missing critical information
        if not entities['amount']:
            suggestions.append("Consider including the transaction amount in the narrative.")
        
        if not entities['reference']:
            suggestions.append("Include a reference number for better tracking.")
        
        if not entities['purpose']:
            suggestions.append("Specify the purpose or reason for the transaction.")
        
        if entities['confidence_score'] < 0.5:
            suggestions.append("Narrative lacks key information. Consider adding more details about amounts, accounts, or purpose.")
        
        # Check for compliance indicators
        compliance = self.extract_compliance_indicators(text)
        if compliance['compliance_score'] < 0.2:
            suggestions.append("Consider adding compliance-related information such as documentation or verification details.")
        
        # Check sentiment
        sentiment = self.analyze_narrative_sentiment(text)
        if sentiment['sentiment'] == 'negative':
            suggestions.append("Narrative contains negative indicators. Consider clarifying any issues or status.")
        
        if not suggestions:
            suggestions.append("Narrative appears complete and informative.")
        
        return suggestions
    
    def get_entity_statistics(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics on extracted entities across multiple transactions"""
        
        if not transactions:
            return {}
        
        stats = {
            'total_transactions': len(transactions),
            'successful_extractions': 0,
            'entity_counts': {},
            'confidence_distribution': [],
            'common_entities': {},
            'extraction_rate': 0.0
        }
        
        # Initialize entity counters
        for entity_type in self.patterns.keys():
            stats['entity_counts'][entity_type] = 0
            stats['common_entities'][entity_type] = {}
        
        for transaction in transactions:
            narrative = transaction.get('narrative', '')
            if narrative:
                entities = self.extract_entities(narrative)
                
                if entities['confidence_score'] > 0.3:
                    stats['successful_extractions'] += 1
                
                stats['confidence_distribution'].append(entities['confidence_score'])
                
                # Count entity types
                for entity_type in self.patterns.keys():
                    if entities.get(entity_type):
                        stats['entity_counts'][entity_type] += 1
                        
                        # Track common entities
                        for entity_value in entities[entity_type]:
                            if entity_value not in stats['common_entities'][entity_type]:
                                stats['common_entities'][entity_type][entity_value] = 0
                            stats['common_entities'][entity_type][entity_value] += 1
        
        # Calculate extraction rate
        stats['extraction_rate'] = stats['successful_extractions'] / stats['total_transactions']
        
        # Get top common entities for each type
        for entity_type in stats['common_entities']:
            common_dict = stats['common_entities'][entity_type]
            if common_dict:
                # Get top 5 most common
                sorted_entities = sorted(common_dict.items(), key=lambda x: x[1], reverse=True)
                stats['common_entities'][entity_type] = dict(sorted_entities[:5])
        
        return stats
