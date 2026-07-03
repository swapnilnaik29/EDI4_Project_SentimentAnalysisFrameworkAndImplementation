import httpx
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# Robust local rule-based fallback logic
def get_rule_based_fallback(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    
    # 1. ATM issues
    if any(k in text_lower for k in ["atm", "cash", "dispense", "withdraw"]):
        return {
            "summary": "Customer reported account deduction without receiving ATM cash.",
            "root_cause": "ATM mechanical dispenser failure or network synchronization error between switch and core ledger.",
            "solving_steps": [
                "Verify ATM journal logs and physical cash balance",
                "Reconcile network switch logs with core banking system",
                "Initiate chargeback reversal if discrepancy is found",
                "Send credit confirmation alert to the customer"
            ],
            "recommended_department": "ATM Operations",
            "escalation_priority": "high"
        }
        
    # 2. UPI/Transfer issues
    elif any(k in text_lower for k in ["upi", "transfer", "gpay", "phonepe", "paytm", "rtgs", "neft", "debited", "failed"]):
        return {
            "summary": "Customer experienced failed electronic fund transfer where funds were debited but not credited.",
            "root_cause": "Interbank network timeout or NPCI switch settlement delay.",
            "solving_steps": [
                "Track NPCI UTR (Unique Transaction Reference) status",
                "Check gateway integration logs for transmission errors",
                "Trigger auto-reversal to customer's account if payment failed at beneficiary bank",
                "Notify customer of transaction completion or refund status"
            ],
            "recommended_department": "UPI & Digital Payments",
            "escalation_priority": "high"
        }
        
    # 3. Card issues (Credit/Debit)
    elif any(k in text_lower for k in ["card", "credit", "debit", "blocked", "block", "cvv", "pin"]):
        return {
            "summary": "Customer reported card locking, block activation, or billing discrepancy.",
            "root_cause": "Automatic fraud prevention trigger or system validation failure.",
            "solving_steps": [
                "Inspect block flags in Card Management System (CMS)",
                "Conduct mandatory customer security verification",
                "Remove block or issue replacement card and PIN",
                "Update customer via registered email and SMS"
            ],
            "recommended_department": "Card Services",
            "escalation_priority": "medium"
        }
        
    # 4. KYC & Account opening
    elif any(k in text_lower for k in ["kyc", "verify", "verification", "document", "pan", "aadhaar", "aadhar", "compliance"]):
        return {
            "summary": "Customer experienced delay in KYC document verification and account activation.",
            "root_cause": "Compliance verification backlog or document quality check failure.",
            "solving_steps": [
                "Retrieve customer's submitted identity documents",
                "Cross-reference details with official government databases (e.g. UIDAI, NSDL)",
                "Approve KYC status in Core Banking System or request clearer documentation",
                "Send activation confirmation email to customer"
            ],
            "recommended_department": "KYC & Compliance",
            "escalation_priority": "medium"
        }
        
    # 5. App/Login issues
    elif any(k in text_lower for k in ["login", "app", "website", "password", "username", "otp", "mobile"]):
        return {
            "summary": "Customer reported failure to log in to the mobile banking app or internet banking portal.",
            "root_cause": "Authentication server timeout or credential synchronization error.",
            "solving_steps": [
                "Check status of authentication and OAuth services",
                "Reset customer password lock and incorrect attempts counter",
                "Verify OTP gateway queue and delivery logs",
                "Instruct customer to update mobile application to latest version"
            ],
            "recommended_department": "Digital Banking Services",
            "escalation_priority": "medium"
        }
        
    # 6. Fraud/Scam/Unauthorised transaction
    elif any(k in text_lower for k in ["fraud", "scam", "unauthorised", "unauthorized", "hacked", "stolen", "cyber"]):
        return {
            "summary": "Customer flagged an unauthorized transaction, indicating potential fraud or account breach.",
            "root_cause": "Credential compromise or phishing event leading to unauthorized system access.",
            "solving_steps": [
                "Immediately freeze all accounts and digital channels for the customer",
                "Trace IP addresses and destination account details of the fraudulent transfer",
                "Report incident to Cyber Crime Cell and network providers",
                "Initiate charge dispute/recovery procedures"
            ],
            "recommended_department": "Fraud Risk & Cyber Security",
            "escalation_priority": "immediate"
        }
        
    # Default fallback
    return {
        "summary": "Customer reported account maintenance issue or banking service discrepancy.",
        "root_cause": "General system synchronization delay or back-office operational error.",
        "solving_steps": [
            "Review customer account ledger and history",
            "Escalate to operations support desk for investigation",
            "Resolve reconciliation discrepancy manually",
            "Contact customer to provide status updates"
        ],
        "recommended_department": "Customer Accounts",
        "escalation_priority": "low"
    }

async def generate_complaint_analysis(complaint_text: str) -> Dict[str, Any]:
    """
    Sends complaint to local Ollama running Mistral.
    Returns a dictionary of analysis fields (summary, root_cause, solving_steps, etc.).
    Falls back to high-fidelity rule-based logic if Ollama is not responding.
    """
    prompt = (
        "You are an expert AI assistant specialized in analyzing bank customer complaints.\n"
        "Analyze the following customer complaint:\n"
        f"Complaint: \"{complaint_text}\"\n\n"
        "Generate a structured analysis. You must return ONLY a raw JSON object with the following keys, "
        "and nothing else (do not use markdown backticks or block formatting):\n"
        "{\n"
        '  "summary": "A clear, single-sentence summary of the customer\'s issue",\n'
        '  "root_cause": "The likely technical or operational root cause",\n'
        '  "solving_steps": ["step 1", "step 2", "step 3", "step 4"],\n'
        '  "recommended_department": "Choose one of: ATM Operations, UPI & Digital Payments, Card Services, Digital Banking Services, KYC & Compliance, Customer Accounts, Fraud Risk & Cyber Security",\n'
        '  "escalation_priority": "Choose one of: low, medium, high, immediate"\n'
        "}\n"
    )
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }
            )
            if response.status_code == 200:
                result_json = response.json()
                response_text = result_json.get("response", "").strip()
                # Clean up any potential markdown wrap
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    response_text = "\n".join(lines).strip()
                
                analysis = json.loads(response_text)
                # Ensure structure is sound
                required_keys = ["summary", "root_cause", "solving_steps", "recommended_department", "escalation_priority"]
                if all(k in analysis for k in required_keys):
                    return analysis
                
                logger.warning("Ollama response missing required keys. Using rule-based fallback.")
    except Exception as e:
        logger.info(f"Ollama Mistral unavailable ({e}). Running rule-based analysis fallback.")
        
    return get_rule_based_fallback(complaint_text)

async def generate_topic_label(keywords: List[str], representative_complaints: List[str]) -> str:
    """
    Asks local Mistral to suggest a concise, professional 3-5 word topic title
    based on keywords and representative complaints.
    """
    keywords_str = ", ".join(keywords[:6])
    complaints_str = "\n".join([f"- {c[:120]}..." for c in representative_complaints[:3]])
    
    prompt = (
        "You are a clustering labeling assistant.\n"
        "Suggest a single concise, professional 2-4 word banking topic label for a cluster of complaints.\n"
        f"Keywords: {keywords_str}\n"
        f"Representative Complaints:\n{complaints_str}\n\n"
        "Provide ONLY the label text itself (e.g. \"ATM Cash Deduction Failure\" or \"UPI Payment Failure\"). "
        "Do not include quotes, preamble, or code blocks."
    )
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0}
                }
            )
            if response.status_code == 200:
                label = response.json().get("response", "").strip()
                # Remove quotes if Ollama added them
                label = label.strip('\'"` ')
                if label and len(label) < 60:
                    return label
    except Exception as e:
        logger.info(f"Ollama topic labeling unavailable ({e}). Using keyword fallback.")
        
    # Heuristic fallback: construct title from top keywords
    if keywords:
        top_k = [k.capitalize() for k in keywords[:3]]
        return f"{' '.join(top_k)} Related Issue"
    return "General Support Issue"
