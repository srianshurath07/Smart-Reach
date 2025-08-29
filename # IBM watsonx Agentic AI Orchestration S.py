# IBM watsonx Agentic AI Orchestration System
# Complete implementation based on the architecture document

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from abc import ABC, abstractmethod

# Mock imports for demonstration - replace with actual IBM watsonx imports
class MockWatsonxAI:
    """Mock watsonx.ai client"""
    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id
    
    def generate_text(self, prompt: str, model_id: str = "ibm/granite-13b-chat-v2") -> str:
        # Mock response - replace with actual watsonx.ai call
        return f"Generated response for: {prompt[:50]}..."
    
    def get_embeddings(self, text: str, model_id: str = "ibm/slate-125m-english-rtrvr") -> List[float]:
        # Mock embeddings - replace with actual embedding call
        return [0.1] * 768

class MockKafkaProducer:
    """Mock Kafka producer"""
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.sent_messages = []
    
    async def send(self, topic: str, value: Dict) -> None:
        self.sent_messages.append({"topic": topic, "value": value})
        print(f"Sent to {topic}: {json.dumps(value, indent=2)}")

class MockKafkaConsumer:
    """Mock Kafka consumer"""
    def __init__(self, topics: List[str], bootstrap_servers: str):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.messages = []
    
    async def consume(self) -> Dict:
        # Mock consumption - return empty for demo
        await asyncio.sleep(1)
        return {}

class MockFeatureStore:
    """Mock Feature Store"""
    def __init__(self):
        self.features = {
            "user_123": {
                "last_login": "2024-07-30",
                "total_spend": 1500.0,
                "preferred_channel": "email",
                "segment": "dormant",
                "consent_email": True,
                "frequency_cap_email": 2
            }
        }
    
    def get_features(self, user_id: str) -> Dict[str, Any]:
        return self.features.get(user_id, {})

# Core Data Models
@dataclass
class AgentTrace:
    agent: str
    version: str
    timestamp: str

@dataclass
class BaseMessage:
    request_id: str
    user_id: str
    timestamp: str
    agent_trace: List[AgentTrace]
    payload: Dict[str, Any]

@dataclass
class NBADecision:
    offer_id: str
    channel: str
    send_time: str
    priority: int
    decision_reason: str
    confidence: float

@dataclass
class ContentVariant:
    variant_id: str
    subject: str
    body: str
    cited_doc_ids: List[str]
    safety_tags: List[str]

@dataclass
class ComplianceDecision:
    status: str  # "approved", "rejected", "needs_review"
    reasons: List[str]
    mandatory_edits: Optional[Dict[str, str]]

class AlertType(Enum):
    LOW_CTR = "low_ctr"
    HIGH_CHURN = "high_churn"
    DORMANT_SEGMENT = "dormant_segment"
    MODEL_DRIFT = "model_drift"

# Base Agent Class
class BaseAgent(ABC):
    def __init__(self, agent_id: str, version: str, kafka_producer: MockKafkaProducer):
        self.agent_id = agent_id
        self.version = version
        self.kafka_producer = kafka_producer
        self.logger = logging.getLogger(f"{agent_id}")
    
    def create_trace(self) -> AgentTrace:
        return AgentTrace(
            agent=self.agent_id,
            version=self.version,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def log_decision(self, request_id: str, inputs: Dict, outputs: Dict, 
                          model_versions: Dict[str, str] = None):
        """Log agent decision for audit trail"""
        log_entry = {
            "request_id": request_id,
            "agent_id": self.agent_id,
            "agent_version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            "inputs": inputs,
            "outputs": outputs,
            "model_versions": model_versions or {}
        }
        await self.kafka_producer.send("agent.audit.actions", log_entry)

# Insights Agent
class InsightsAgent(BaseAgent):
    def __init__(self, kafka_producer: MockKafkaProducer):
        super().__init__("insights", "v1.0", kafka_producer)
        self.thresholds = {
            "low_ctr_threshold": 0.02,
            "dormant_days": 30,
            "drift_threshold": 0.1
        }
    
    async def analyze_engagement_metrics(self, metrics: Dict[str, float]) -> Optional[AlertType]:
        """Analyze metrics and detect anomalies"""
        if metrics.get("ctr", 0) < self.thresholds["low_ctr_threshold"]:
            return AlertType.LOW_CTR
        
        if metrics.get("days_since_login", 0) > self.thresholds["dormant_days"]:
            return AlertType.DORMANT_SEGMENT
        
        return None
    
    async def generate_alert(self, alert_type: AlertType, segment_data: Dict[str, Any]):
        """Generate and publish alerts"""
        request_id = str(uuid.uuid4())
        
        alert_payload = {
            "alert_type": alert_type.value,
            "segment": segment_data.get("segment", "unknown"),
            "affected_users": segment_data.get("user_count", 0),
            "metrics": segment_data.get("metrics", {}),
            "recommended_action": self._get_recommended_action(alert_type)
        }
        
        message = BaseMessage(
            request_id=request_id,
            user_id="system",
            timestamp=datetime.utcnow().isoformat(),
            agent_trace=[self.create_trace()],
            payload=alert_payload
        )
        
        await self.kafka_producer.send("agent.insights.alerts.v1", asdict(message))
        await self.log_decision(request_id, segment_data, alert_payload)
    
    def _get_recommended_action(self, alert_type: AlertType) -> str:
        recommendations = {
            AlertType.LOW_CTR: "Run content A/B test with new creatives",
            AlertType.DORMANT_SEGMENT: "Launch re-engagement campaign",
            AlertType.HIGH_CHURN: "Implement retention offers",
            AlertType.MODEL_DRIFT: "Retrain prediction models"
        }
        return recommendations.get(alert_type, "Manual review required")

# NBA (Next-Best-Action) Agent
class NBAAgent(BaseAgent):
    def __init__(self, kafka_producer: MockKafkaProducer, feature_store: MockFeatureStore):
        super().__init__("nba", "v1.2", kafka_producer)
        self.feature_store = feature_store
        self.offers_catalog = {
            "cashback_10": {"name": "10% Cashback Card", "priority": 8, "eligibility": ["premium"]},
            "savings_promo": {"name": "High Yield Savings", "priority": 6, "eligibility": ["all"]},
            "loan_offer": {"name": "Personal Loan", "priority": 9, "eligibility": ["qualified"]}
        }
    
    async def recommend_action(self, user_id: str, context: Dict[str, Any]) -> NBADecision:
        """Generate next-best-action recommendation"""
        request_id = str(uuid.uuid4())
        
        # Get user features
        user_features = self.feature_store.get_features(user_id)
        
        # Select best offer based on features and context
        selected_offer = await self._select_offer(user_features, context)
        
        # Determine optimal channel and timing
        channel = self._select_channel(user_features)
        send_time = self._calculate_send_time(user_features)
        
        decision = NBADecision(
            offer_id=selected_offer["id"],
            channel=channel,
            send_time=send_time,
            priority=selected_offer["priority"],
            decision_reason=selected_offer["reason"],
            confidence=selected_offer["confidence"]
        )
        
        # Publish decision
        message = BaseMessage(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_trace=[self.create_trace()],
            payload=asdict(decision)
        )
        
        await self.kafka_producer.send("agent.nba.decisions.v1", asdict(message))
        await self.log_decision(request_id, {"user_features": user_features, "context": context}, 
                              asdict(decision), {"ranker_model": "xgb_v2.1", "policy_model": "bandit_v1.0"})
        
        return decision
    
    async def _select_offer(self, user_features: Dict, context: Dict) -> Dict[str, Any]:
        """Select best offer using model scores and business rules"""
        segment = user_features.get("segment", "unknown")
        
        if segment == "dormant":
            return {
                "id": "cashback_10",
                "priority": 9,
                "reason": "Re-engagement offer for dormant user",
                "confidence": 0.75
            }
        elif user_features.get("total_spend", 0) > 1000:
            return {
                "id": "loan_offer",
                "priority": 8,
                "reason": "High-value customer eligible for loan",
                "confidence": 0.82
            }
        else:
            return {
                "id": "savings_promo",
                "priority": 6,
                "reason": "Standard savings offer",
                "confidence": 0.65
            }
    
    def _select_channel(self, user_features: Dict[str, Any]) -> str:
        """Select optimal communication channel"""
        preferred = user_features.get("preferred_channel", "email")
        consent_key = f"consent_{preferred}"
        
        if user_features.get(consent_key, False):
            return preferred
        return "push"  # Fallback
    
    def _calculate_send_time(self, user_features: Dict[str, Any]) -> str:
        """Calculate optimal send time"""
        # Simple logic - can be enhanced with ML models
        tomorrow_9am = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        return tomorrow_9am.isoformat()

# Content Agent
class ContentAgent(BaseAgent):
    def __init__(self, kafka_producer: MockKafkaProducer, watsonx_ai: MockWatsonxAI):
        super().__init__("content", "v1.1", kafka_producer)
        self.watsonx_ai = watsonx_ai
        self.templates = {
            "cashback_10": {
                "subject_templates": ["Get {percentage}% cashback on every purchase!", 
                                    "Limited time: {percentage}% cashback card"],
                "body_template": "Dear {name}, enjoy {percentage}% cashback with our premium card."
            }
        }
        self.rag_docs = {
            "legal_footer": "Terms and conditions apply. See website for details.",
            "cashback_terms": "Cashback applies to eligible purchases only. Maximum $500 per month.",
            "brand_voice": "Keep messaging friendly, clear, and action-oriented."
        }
    
    async def generate_content(self, nba_decision: NBADecision, user_id: str) -> List[ContentVariant]:
        """Generate content variants with RAG-based fact checking"""
        request_id = str(uuid.uuid4())
        
        # Retrieve relevant context using RAG
        context_docs = await self._retrieve_context(nba_decision.offer_id)
        
        # Generate multiple variants
        variants = []
        for i in range(2):  # Generate 2 variants
            subject, body, cited_docs = await self._generate_variant(
                nba_decision, user_id, context_docs, i
            )
            
            variant = ContentVariant(
                variant_id=f"{request_id}_v{i}",
                subject=subject,
                body=body,
                cited_doc_ids=cited_docs,
                safety_tags=["financial_product", "promotional"]
            )
            variants.append(variant)
        
        # Publish variants
        message = BaseMessage(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_trace=[self.create_trace()],
            payload={"variants": [asdict(v) for v in variants], "nba_decision": asdict(nba_decision)}
        )
        
        await self.kafka_producer.send("agent.content.variants.v1", asdict(message))
        await self.log_decision(request_id, {"nba_decision": asdict(nba_decision)}, 
                              {"variants_count": len(variants)}, {"llm_model": "ibm/granite-13b-chat-v2"})
        
        return variants
    
    async def _retrieve_context(self, offer_id: str) -> List[Dict[str, str]]:
        """Retrieve relevant documents using RAG"""
        relevant_docs = []
        
        if "cashback" in offer_id:
            relevant_docs.extend([
                {"doc_id": "cashback_terms", "content": self.rag_docs["cashback_terms"]},
                {"doc_id": "legal_footer", "content": self.rag_docs["legal_footer"]}
            ])
        
        relevant_docs.append({"doc_id": "brand_voice", "content": self.rag_docs["brand_voice"]})
        return relevant_docs
    
    async def _generate_variant(self, decision: NBADecision, user_id: str, 
                              context_docs: List[Dict], variant_num: int) -> Tuple[str, str, List[str]]:
        """Generate single content variant using LLM"""
        context_text = "\n".join([doc["content"] for doc in context_docs])
        cited_doc_ids = [doc["doc_id"] for doc in context_docs]
        
        prompt = f"""
        Generate email content for offer: {decision.offer_id}
        Context: {context_text}
        
        Requirements:
        - Use only facts from the provided context
        - Include clear call-to-action
        - Follow brand voice guidelines
        - Variant #{variant_num + 1}
        
        Format: Subject: [subject]\nBody: [body]
        """
        
        response = self.watsonx_ai.generate_text(prompt)
        
        # Parse response (simplified)
        lines = response.split('\n')
        subject = "Exclusive Offer Just for You!"  # Fallback
        body = "Check out our amazing new offer."  # Fallback
        
        for line in lines:
            if line.startswith("Subject:"):
                subject = line.replace("Subject:", "").strip()
            elif line.startswith("Body:"):
                body = line.replace("Body:", "").strip()
        
        return subject, body, cited_doc_ids

# Compliance Agent
class ComplianceAgent(BaseAgent):
    def __init__(self, kafka_producer: MockKafkaProducer, feature_store: MockFeatureStore):
        super().__init__("compliance", "v1.0", kafka_producer)
        self.feature_store = feature_store
        self.required_phrases = ["Terms and conditions apply", "See website for details"]
        self.blacklisted_phrases = ["guaranteed", "risk-free", "instant approval"]
    
    async def validate_content(self, variants: List[ContentVariant], user_id: str, 
                              nba_decision: NBADecision) -> ComplianceDecision:
        """Validate content variants for compliance"""
        request_id = str(uuid.uuid4())
        
        # Get user consent and eligibility
        user_features = self.feature_store.get_features(user_id)
        
        # Run compliance checks
        compliance_issues = []
        
        # Check consent
        if not self._check_consent(user_features, nba_decision.channel):
            compliance_issues.append("User consent required for selected channel")
        
        # Check frequency caps
        if not self._check_frequency_caps(user_features, nba_decision.channel):
            compliance_issues.append("Frequency cap exceeded")
        
        # Check content compliance
        for variant in variants:
            content_issues = self._validate_content_rules(variant)
            compliance_issues.extend(content_issues)
        
        # Determine decision
        if not compliance_issues:
            decision = ComplianceDecision(
                status="approved",
                reasons=["All compliance checks passed"],
                mandatory_edits=None
            )
        elif any("required" in issue.lower() or "consent" in issue.lower() for issue in compliance_issues):
            decision = ComplianceDecision(
                status="rejected",
                reasons=compliance_issues,
                mandatory_edits=None
            )
        else:
            decision = ComplianceDecision(
                status="needs_review",
                reasons=compliance_issues,
                mandatory_edits={"body": "Add required legal disclaimer"}
            )
        
        # Publish decision
        message = BaseMessage(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_trace=[self.create_trace()],
            payload=asdict(decision)
        )
        
        await self.kafka_producer.send("agent.compliance.decisions.v1", asdict(message))
        await self.log_decision(request_id, {"variants_count": len(variants)}, asdict(decision))
        
        return decision
    
    def _check_consent(self, user_features: Dict, channel: str) -> bool:
        """Check user consent for channel"""
        consent_key = f"consent_{channel}"
        return user_features.get(consent_key, False)
    
    def _check_frequency_caps(self, user_features: Dict, channel: str) -> bool:
        """Check frequency caps"""
        cap_key = f"frequency_cap_{channel}"
        current_frequency = user_features.get(f"current_frequency_{channel}", 0)
        max_frequency = user_features.get(cap_key, 5)
        return current_frequency < max_frequency
    
    def _validate_content_rules(self, variant: ContentVariant) -> List[str]:
        """Validate content against rules"""
        issues = []
        content = f"{variant.subject} {variant.body}"
        
        # Check for required phrases
        for phrase in self.required_phrases:
            if phrase not in content:
                issues.append(f"Missing required phrase: {phrase}")
        
        # Check for blacklisted phrases
        for phrase in self.blacklisted_phrases:
            if phrase.lower() in content.lower():
                issues.append(f"Contains prohibited phrase: {phrase}")
        
        return issues

# Experimentation Agent
class ExperimentationAgent(BaseAgent):
    def __init__(self, kafka_producer: MockKafkaProducer):
        super().__init__("experimentation", "v1.0", kafka_producer)
        self.active_experiments = {}
        self.significance_threshold = 0.05
    
    async def assign_experiment(self, user_id: str, variants: List[ContentVariant]) -> str:
        """Assign user to experiment variant"""
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d')}_{len(variants)}_variants"
        
        # Simple hash-based assignment
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        variant_index = user_hash % len(variants)
        assigned_variant = variants[variant_index].variant_id
        
        # Log assignment
        assignment = {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "assigned_variant": assigned_variant,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.kafka_producer.send("agent.experimentation.assignments.v1", assignment)
        return assigned_variant
    
    async def analyze_experiment_results(self, experiment_id: str, metrics: Dict[str, Dict]) -> Dict:
        """Analyze experiment results and make promotion decisions"""
        # Simple statistical analysis (in real implementation, use proper statistical tests)
        best_variant = max(metrics.keys(), key=lambda k: metrics[k].get("conversion_rate", 0))
        best_ctr = metrics[best_variant]["conversion_rate"]
        
        # Check if difference is significant (simplified)
        control_ctr = metrics.get("control", {}).get("conversion_rate", 0)
        improvement = (best_ctr - control_ctr) / control_ctr if control_ctr > 0 else 0
        
        decision = {
            "experiment_id": experiment_id,
            "winning_variant": best_variant,
            "improvement": improvement,
            "action": "promote" if improvement > 0.1 else "continue",
            "confidence": 0.95 if improvement > 0.2 else 0.75
        }
        
        await self.kafka_producer.send("agent.experimentation.decisions.v1", decision)
        return decision

# Main Orchestration System
class AgenticOrchestrationSystem:
    def __init__(self):
        # Initialize mock services (replace with real IBM watsonx services)
        self.watsonx_ai = MockWatsonxAI("your-api-key", "your-project-id")
        self.kafka_producer = MockKafkaProducer("localhost:9092")
        self.feature_store = MockFeatureStore()
        
        # Initialize agents
        self.insights_agent = InsightsAgent(self.kafka_producer)
        self.nba_agent = NBAAgent(self.kafka_producer, self.feature_store)
        self.content_agent = ContentAgent(self.kafka_producer, self.watsonx_ai)
        self.compliance_agent = ComplianceAgent(self.kafka_producer, self.feature_store)
        self.experimentation_agent = ExperimentationAgent(self.kafka_producer)
        
        self.logger = logging.getLogger("orchestration_system")
    
    async def process_user_recommendation(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """End-to-end recommendation process for a user"""
        try:
            # Step 1: NBA Agent generates recommendation
            nba_decision = await self.nba_agent.recommend_action(user_id, context)
            
            # Step 2: Content Agent generates variants
            content_variants = await self.content_agent.generate_content(nba_decision, user_id)
            
            # Step 3: Compliance Agent validates
            compliance_decision = await self.compliance_agent.validate_content(
                content_variants, user_id, nba_decision
            )
            
            if compliance_decision.status == "approved":
                # Step 4: Experimentation Agent assigns variant
                assigned_variant = await self.experimentation_agent.assign_experiment(
                    user_id, content_variants
                )
                
                # Step 5: Send approved campaign (mock)
                campaign_data = {
                    "user_id": user_id,
                    "nba_decision": asdict(nba_decision),
                    "selected_variant": assigned_variant,
                    "compliance_status": "approved",
                    "send_time": nba_decision.send_time
                }
                
                await self.kafka_producer.send("campaigns.execute.v1", campaign_data)
                
                return {
                    "status": "success",
                    "campaign_scheduled": True,
                    "variant_assigned": assigned_variant,
                    "send_time": nba_decision.send_time
                }
            
            elif compliance_decision.status == "needs_review":
                return {
                    "status": "pending_review",
                    "compliance_issues": compliance_decision.reasons,
                    "required_edits": compliance_decision.mandatory_edits
                }
            
            else:  # rejected
                return {
                    "status": "rejected",
                    "compliance_issues": compliance_decision.reasons
                }
        
        except Exception as e:
            self.logger.error(f"Error processing recommendation for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def handle_dormant_user_campaign(self, dormant_users: List[str]):
        """Handle campaign for dormant users triggered by Insights Agent"""
        
        # Insights Agent generates alert
        await self.insights_agent.generate_alert(
            AlertType.DORMANT_SEGMENT,
            {
                "segment": "dormant",
                "user_count": len(dormant_users),
                "metrics": {"avg_days_dormant": 35, "total_spend_drop": 0.4}
            }
        )
        
        # Process each dormant user
        results = []
        for user_id in dormant_users[:5]:  # Process first 5 for demo
            context = {"trigger": "dormant_reengagement", "campaign_type": "retention"}
            result = await self.process_user_recommendation(user_id, context)
            results.append({"user_id": user_id, "result": result})
        
        return results

# Demo Usage
async def main():
    """Demo the agentic orchestration system"""
    system = AgenticOrchestrationSystem()
    
    print("=== IBM watsonx Agentic AI Orchestration Demo ===\n")
    
    # Demo 1: Single user recommendation
    print("1. Processing single user recommendation...")
    result = await system.process_user_recommendation(
        "user_123", 
        {"source": "web", "page": "homepage", "time_on_site": 300}
    )
    print(f"Result: {json.dumps(result, indent=2)}\n")
    
    # Demo 2: Dormant user campaign
    print("2. Processing dormant user campaign...")
    dormant_users = ["user_123", "user_456", "user_789"]
    campaign_results = await system.handle_dormant_user_campaign(dormant_users)
    
    for user_result in campaign_results:
        print(f"User {user_result['user_id']}: {user_result['result']['status']}")
    
    print(f"\n=== Campaign Summary ===")
    print(f"Total users processed: {len(campaign_results)}")
    successful = sum(1 for r in campaign_results if r['result']['status'] == 'success')
    print(f"Successfully scheduled campaigns: {successful}")
    
    # Demo 3: Show Kafka messages sent
    print(f"\n=== Messages Sent to Kafka ===")
    for msg in system.kafka_producer.sent_messages[-5:]:  # Show last 5 messages
        print(f"Topic: {msg['topic']}")
        print(f"Message: {json.dumps(msg['value'], indent=2)}\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())