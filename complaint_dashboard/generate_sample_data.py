import asyncio
import datetime
import json
import uuid
import logging
from sqlalchemy import select
from app.database.connection import engine, Base, async_session_maker
from app.database.models import Complaint
from app.ai.topic_model import get_embedding
from app.services.complaint_service import retrain_all_topics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample realistic complaints with pre-defined AI attributes for instantaneous, rich dashboard presentation
SAMPLE_DATA = [
    {
        "text": "ATM machine debited $200 from my account, but it did not dispense any cash! The machine showed a timeout error.",
        "user_type": "regular",
        "source": "offline",
        "location": "New York City",
        "days_ago": 6,
        "time": "14:22:10",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.98,
        "intensity_score": 0.85,
        "severity": "high",
        "ai_summary": "Customer reported account deduction of $200 with no physical cash dispensed due to an ATM timeout.",
        "root_cause": "ATM dispenser mechanical jam or connectivity timeout with the switch system.",
        "solving_steps": ["Verify ATM transaction journal logs", "Check switch reconciliation ledger", "Trigger automated ledger reversal", "Notify customer of fund credit status"],
        "recommended_department": "ATM Operations",
        "escalation_priority": "high"
    },
    {
        "text": "Tried to transfer money to my landlord via UPI, the transaction failed but my account got debited. It is urgent, please refund!",
        "user_type": "student",
        "source": "mobile app",
        "location": "Mumbai",
        "days_ago": 5,
        "time": "10:15:30",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.97,
        "intensity_score": 0.80,
        "severity": "high",
        "ai_summary": "Customer reported account debited for a failed UPI transaction meant for rent payment.",
        "root_cause": "NPCI payment gateway timeout or interbank settlement sync delay.",
        "solving_steps": ["Locate NPCI unique transaction reference (UTR)", "Check digital payments gateway logs", "Trigger auto-reversal of funds", "Send verification SMS to customer"],
        "recommended_department": "UPI & Digital Payments",
        "escalation_priority": "high"
    },
    {
        "text": "My credit card was blocked suddenly without any warning or SMS notifications. I am trying to pay for dinner and it is embarrassing!",
        "user_type": "premium",
        "source": "website",
        "location": "London",
        "days_ago": 4,
        "time": "21:40:05",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.99,
        "intensity_score": 0.90,
        "severity": "critical",
        "ai_summary": "Premium client experienced unexpected credit card block causing embarrassment during dinner.",
        "root_cause": "Automatic fraud risk trigger due to suspicious activity pattern.",
        "solving_steps": ["Inspect active block flags in CMS", "Call customer to verify recent transaction list", "Unblock card in system", "Issue SMS warning explaining block cause"],
        "recommended_department": "Card Services",
        "escalation_priority": "immediate"
    },
    {
        "text": "I submitted my KYC documents (Aadhaar and PAN) over two weeks ago, but my account status is still showing as pending verification. I cannot access my funds.",
        "user_type": "senior citizen",
        "source": "offline",
        "location": "Delhi",
        "days_ago": 5,
        "time": "11:05:12",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.92,
        "intensity_score": 0.65,
        "severity": "high",
        "ai_summary": "Senior citizen reported KYC document verification delays blocking account access for two weeks.",
        "root_cause": "Compliance verification team backlog or document clarity check queue delay.",
        "solving_steps": ["Retrieve submitted KYC documents", "Verify identity documents in government database", "Approve KYC status", "Notify client of activation and apologize for delay"],
        "recommended_department": "KYC & Compliance",
        "escalation_priority": "medium"
    },
    {
        "text": "I noticed an unauthorized charge of $450 from an unknown vendor on my debit card. I did not make this purchase! Help, has my card been hacked?",
        "user_type": "business",
        "source": "email",
        "location": "San Francisco",
        "days_ago": 1,
        "time": "08:12:44",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.99,
        "intensity_score": 0.95,
        "severity": "critical",
        "ai_summary": "Business client reported an unauthorized transaction of $450, suspecting card hacking.",
        "root_cause": "Compromised card credentials leading to unauthorized transaction authorization.",
        "solving_steps": ["Immediately block the debit card", "Flag transaction as fraudulent in settlement gateway", "Initiate chargeback dispute process", "Contact cyber security for trace details"],
        "recommended_department": "Fraud Risk & Cyber Security",
        "escalation_priority": "immediate"
    },
    {
        "text": "The mobile banking app crashes every single time I try to open the transfer page after the new update. Please fix this bug.",
        "user_type": "student",
        "source": "social media",
        "location": "Boston",
        "days_ago": 3,
        "time": "16:50:22",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.96,
        "intensity_score": 0.70,
        "severity": "high",
        "ai_summary": "Customer reported mobile app crashing on the transfer screen after updating.",
        "root_cause": "Software defect or memory leak in the mobile application's latest build.",
        "solving_steps": ["Review application crash reports and stack traces", "Deploy hotfix release patch", "Reset user app profile data", "Provide instructions to clear application cache"],
        "recommended_department": "Digital Banking Services",
        "escalation_priority": "medium"
    },
    {
        "text": "Extremely pleased with the quick resolution of my account block. The branch manager was very helpful and pleasant.",
        "user_type": "premium",
        "source": "website",
        "location": "Mumbai",
        "days_ago": 4,
        "time": "12:00:00",
        "sentiment_label": "POSITIVE",
        "sentiment_score": 0.99,
        "intensity_score": 0.10,
        "severity": "low",
        "ai_summary": "Customer expressed satisfaction with swift account block resolution by the branch manager.",
        "root_cause": "Effective customer service and quick resolution by staff.",
        "solving_steps": ["Log appreciation in manager profile", "Archive positive feedback", "Send satisfaction thank you email"],
        "recommended_department": "Customer Accounts",
        "escalation_priority": "low"
    },
    {
        "text": "I was double charged for my monthly gym subscription. The transaction occurred twice on May 19th. Please reverse the second transaction.",
        "user_type": "regular",
        "source": "website",
        "location": "Chicago",
        "days_ago": 2,
        "time": "09:30:15",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.88,
        "intensity_score": 0.50,
        "severity": "medium",
        "ai_summary": "Customer requested reversal of duplicate subscription debit on May 19th.",
        "root_cause": "Merchant payment gateway double submission or processing error.",
        "solving_steps": ["Locate duplicate settlement records", "Send chargeback dispute notice to merchant bank", "Issue provisional credit of amount", "Reconcile final settlement"],
        "recommended_department": "Card Services",
        "escalation_priority": "medium"
    },
    {
        "text": "My home loan approval process is taking forever. It's been 30 days since I submitted the property documents and no one replies to my emails.",
        "user_type": "business",
        "source": "email",
        "location": "Seattle",
        "days_ago": 3,
        "time": "11:20:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.94,
        "intensity_score": 0.72,
        "severity": "high",
        "ai_summary": "Customer complained about 30-day delay in home loan approval and unresponsive staff.",
        "root_cause": "Underwriting queue delay or file processing bottleneck.",
        "solving_steps": ["Retrieve loan application status from LOS", "Assign priority underwriter review", "Contact client to request missing details if any", "Email status update to applicant"],
        "recommended_department": "Loan Operations",
        "escalation_priority": "high"
    },
    {
        "text": "I tried to withdraw money at the ATM, but the machine swallowed my debit card and went black. Now I don't have my card or cash!",
        "user_type": "regular",
        "source": "offline",
        "location": "Boston",
        "days_ago": 1,
        "time": "23:05:40",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.98,
        "intensity_score": 0.82,
        "severity": "high",
        "ai_summary": "Customer reported ATM swallowed debit card before shutting down.",
        "root_cause": "ATM terminal power failure or mechanical card-reader jam.",
        "solving_steps": ["Instruct customer to immediately freeze card via app", "Log service ticket for ATM physical retrieval", "Issue replacement debit card", "Reconcile ATM terminal contents"],
        "recommended_department": "ATM Operations",
        "escalation_priority": "high"
    },
    {
        "text": "Why does it take so long to transfer funds internationally? My wire transfer to Germany has been stuck for 5 days. High fees and terrible speed.",
        "user_type": "business",
        "source": "website",
        "location": "New York City",
        "days_ago": 2,
        "time": "15:10:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.95,
        "intensity_score": 0.75,
        "severity": "high",
        "ai_summary": "Customer complained about international wire transfer delay and high processing fees.",
        "root_cause": "SWIFT network correspondent bank hold or compliance routing delay.",
        "solving_steps": ["Check wire status in SWIFT Alliance gateway", "Confirm compliance check status", "Release transaction or notify correspondent bank", "Contact customer with routing update"],
        "recommended_department": "Customer Accounts",
        "escalation_priority": "high"
    },
    {
        "text": "Could not sign up for the new student bank account online. The website shows 'System error 500' on the final submit step.",
        "user_type": "student",
        "source": "website",
        "location": "San Francisco",
        "days_ago": 6,
        "time": "17:15:30",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.91,
        "intensity_score": 0.58,
        "severity": "medium",
        "ai_summary": "Student reported error 500 on online registration submit step.",
        "root_cause": "Web service database connection timeout or validation exception.",
        "solving_steps": ["Inspect web application error 500 server logs", "Check database sign-up queue status", "Fix submission endpoint script bug", "Re-engage client to retry sign-up"],
        "recommended_department": "Digital Banking Services",
        "escalation_priority": "medium"
    },
    {
        "text": "Urgent! Someone tried to log in to my online banking app from a device in Russia. I received a code verification prompt but did not trigger it. Lock my account now!",
        "user_type": "premium",
        "source": "mobile app",
        "location": "London",
        "days_ago": 0,
        "time": "22:15:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.99,
        "intensity_score": 0.98,
        "severity": "critical",
        "ai_summary": "Premium customer flagged suspicious login attempt from Russia and requested immediate lock.",
        "root_cause": "Password compromise and trigger of multi-factor authentication (MFA).",
        "solving_steps": ["Place immediate block on net banking account and app access", "Terminate all active user sessions", "Force credentials reset", "Initiate security inspection on customer profile"],
        "recommended_department": "Fraud Risk & Cyber Security",
        "escalation_priority": "immediate"
    },
    {
        "text": "My loan EMI was deducted twice this month, once on the 1st and again on the 5th. This is leaving my account overdrawn! Revert the extra charge immediately.",
        "user_type": "regular",
        "source": "email",
        "location": "Chicago",
        "days_ago": 0,
        "time": "09:00:20",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.98,
        "intensity_score": 0.88,
        "severity": "high",
        "ai_summary": "Customer reported duplicate EMI debit resulting in an account overdraft.",
        "root_cause": "Loan repayment automated clearing house (ACH) mandate double-execution error.",
        "solving_steps": ["Verify ACH clearing file for duplicate entries", "Approve immediate reversal of extra debit", "Waive any overdraft fees caused by error", "Notify customer of refund status"],
        "recommended_department": "Loan Operations",
        "escalation_priority": "high"
    },
    {
        "text": "I got an SMS saying my bank account will be blocked if I don't click a link to verify my identity. Is this a phishing scam? Please look into it.",
        "user_type": "senior citizen",
        "source": "social media",
        "location": "Delhi",
        "days_ago": 1,
        "time": "14:55:00",
        "sentiment_label": "NEUTRAL",
        "sentiment_score": 0.60,
        "intensity_score": 0.45,
        "severity": "high",
        "ai_summary": "Customer inquired about a suspicious SMS phishing link threatening account block.",
        "root_cause": "External phishing attempt targeting bank customers.",
        "solving_steps": ["Verify domain name in SMS headers", "Initiate takedown request for phishing website", "Broadcast security warning alert to all customers", "Log incident details"],
        "recommended_department": "Fraud Risk & Cyber Security",
        "escalation_priority": "high"
    },
    {
        "text": "I visited the branch to update my signature but the clerk refused saying my ID is not clear enough. It's a passport issued by the government, how is it not clear?",
        "user_type": "senior citizen",
        "source": "offline",
        "location": "Delhi",
        "days_ago": 2,
        "time": "13:00:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.94,
        "intensity_score": 0.70,
        "severity": "medium",
        "ai_summary": "Senior citizen reported branch clerk refused passport ID verification for signature update.",
        "root_cause": "Branch compliance rules over-interpretation or poor scan quality check.",
        "solving_steps": ["Inspect scanned passport copy in branch records", "Approve ID authenticity verification override", "Inform branch manager to assist customer", "Call customer to apologize and complete signature update"],
        "recommended_department": "KYC & Compliance",
        "escalation_priority": "medium"
    },
    {
        "text": "My UPI transactions keep failing since this morning with error 'decline by PSP'. Please check if your servers are down.",
        "user_type": "regular",
        "source": "mobile app",
        "location": "Mumbai",
        "days_ago": 0,
        "time": "11:45:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.93,
        "intensity_score": 0.60,
        "severity": "medium",
        "ai_summary": "Customer complained about repeated UPI failures with 'decline by PSP' error.",
        "root_cause": "PSP server connectivity loss or system maintenance downtime.",
        "solving_steps": ["Perform health check on digital PSP gateway servers", "Check routing tables and connection ports", "Redirect load to redundant server cluster", "Broadcast API system status details"],
        "recommended_department": "UPI & Digital Payments",
        "escalation_priority": "medium"
    },
    {
        "text": "The branch staff was extremely rude and unhelpful when I asked for a printed copy of my bank statement. They told me to use the app instead. I don't know how to use the app!",
        "user_type": "senior citizen",
        "source": "offline",
        "location": "Chicago",
        "days_ago": 3,
        "time": "10:30:10",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.97,
        "intensity_score": 0.78,
        "severity": "medium",
        "ai_summary": "Senior citizen reported staff refused to print bank statements and suggested using the mobile app.",
        "root_cause": "Poor branch staff empathy or customer service guidelines mismatch.",
        "solving_steps": ["Contact branch manager regarding complaint", "Instruct staff to assist senior citizens with offline statements", "Print statement and mail to client", "Log behavior warning in clerk file"],
        "recommended_department": "Customer Accounts",
        "escalation_priority": "medium"
    },
    {
        "text": "I tried to transfer $5000 using mobile app netbanking but got an error saying transaction limits exceeded. The app limits say $10000. Why is it blocking?",
        "user_type": "premium",
        "source": "mobile app",
        "location": "Seattle",
        "days_ago": 2,
        "time": "12:15:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.85,
        "intensity_score": 0.52,
        "severity": "medium",
        "ai_summary": "Premium customer reported netbanking transfer block below app transaction limits.",
        "root_cause": "Individual user account limit restriction overriding system defaults.",
        "solving_steps": ["Check limit configuration settings in customer profile", "Update daily transaction threshold for premium customer", "Validate transaction authorization logs", "Send confirmation notification"],
        "recommended_department": "Digital Banking Services",
        "escalation_priority": "medium"
    },
    {
        "text": "We are a corporate client and our salary disbursement file failed to upload today. Over 100 employees will miss their pay. Fix this immediately!",
        "user_type": "business",
        "source": "email",
        "location": "New York City",
        "days_ago": 0,
        "time": "16:10:00",
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.99,
        "intensity_score": 0.96,
        "severity": "critical",
        "ai_summary": "Corporate client reported salary disbursement file upload failure threatening 100 employee pay schedules.",
        "root_cause": "Corporate portal file parser exception or database lock during high load batch.",
        "solving_steps": ["Retrieve failed salary disbursement batch file", "Manually trigger batch parsing script", "Verify payroll funds transfer in ledger", "Inform corporate client of successful execution"],
        "recommended_department": "Customer Accounts",
        "escalation_priority": "immediate"
    }
]

async def seed_data():
    logger.info("Starting database seeding...")
    
    # 1. Initialize DB tables
    async with engine.begin() as conn:
        logger.info("Creating tables if not exists...")
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Check if database has entries
    async with async_session_maker() as db:
        result = await db.execute(select(Complaint))
        existing_count = len(result.all())
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} records. Skipping seeding to prevent duplicate data.")
            return

        # 3. Process and write sample complaints
        logger.info("Inserting sample complaints...")
        now = datetime.datetime.utcnow()
        
        for item in SAMPLE_DATA:
            complaint_id = str(uuid.uuid4())
            c_date = (now - datetime.timedelta(days=item["days_ago"])).strftime("%Y-%m-%d")
            c_time = item["time"]
            dt_obj = datetime.datetime.strptime(f"{c_date} {c_time}", "%Y-%m-%d %H:%M:%S")
            
            # Compute embeddings
            emb = get_embedding(item["text"])
            
            complaint = Complaint(
                complaint_id=complaint_id,
                complaint_text=item["text"],
                cleaned_text=item["text"],
                complaint_date=c_date,
                complaint_time=c_time,
                timestamp=dt_obj,
                location=item["location"],
                user_type=item["user_type"],
                complaint_source=item["source"],
                embedding_vector_reference=json.dumps(emb),
                
                # AI attributes pre-computed to skip Ollama requests at start
                sentiment_label=item["sentiment_label"],
                sentiment_score=item["sentiment_score"],
                intensity_score=item["intensity_score"],
                severity=item["severity"],
                ai_summary=item["ai_summary"],
                root_cause=item["root_cause"],
                solving_steps=json.dumps(item["solving_steps"]),
                recommended_department=item["recommended_department"],
                escalation_priority=item["escalation_priority"],
                
                # Set temporary topics, will run retraining later
                topic_id=-1,
                topic_label="Uncategorized",
                topic_keywords=json.dumps([])
            )
            
            db.add(complaint)
            
        await db.commit()
        logger.info(f"Inserted {len(SAMPLE_DATA)} raw complaints successfully.")
        
        # 4. Trigger Retraining Pipeline to group complaints into topics dynamically
        logger.info("Triggering initial BERTopic/KMeans dynamic clustering on seed complaints...")
        num_topics = await retrain_all_topics(db)
        logger.info(f"Seeding completed successfully! Dynamic topics discovered: {num_topics}")

if __name__ == "__main__":
    asyncio.run(seed_data())
