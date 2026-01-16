"""
InfoPilot Explorer - Legal Documents
User Agreement and Privacy Policy for Top Pilot Enterprises, Inc.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/legal", tags=["Legal"])

# ==================== USER AGREEMENT ====================

USER_AGREEMENT = """
# User Agreement

## Top Pilot Enterprises, Inc.
### InfoPilot Explorer Terms of Service

**Effective Date: January 16, 2026**

Welcome to InfoPilot Explorer! By accessing or using our service, you agree to be bound by these terms.

---

## 1. Acceptance of Terms

By creating an account or using InfoPilot Explorer, you acknowledge that you have read, understood, and agree to be bound by this User Agreement and our Privacy Policy.

## 2. Description of Service

InfoPilot Explorer is a web-based information discovery platform that provides:
- **InfoJet 2.0™** proprietary search and categorization technology
- **Protocol Marketplace** for buying and selling search protocols
- **Social Features** including groups, pages, and direct messaging
- **Gamification** features including achievements, badges, and leaderboards
- **Voice Search** powered by AI technology
- **Collaborative Tools** for protocol development

## 3. User Accounts

### 3.1 Account Creation
- You must provide accurate and complete information when creating an account
- You are responsible for maintaining the security of your account credentials
- You must be at least 13 years old to use this service
- One account per person; no automated account creation

### 3.2 Account Responsibilities
- You are responsible for all activity under your account
- You must notify us immediately of any unauthorized access
- You may not share your account credentials with others

## 4. Acceptable Use Policy

### 4.1 You Agree NOT To:
- Post or transmit unlawful, threatening, abusive, or harassing content
- Impersonate any person or entity
- Upload viruses, malware, or other harmful code
- Attempt to gain unauthorized access to our systems
- Use the service for any illegal purpose
- Spam, harass, or abuse other users
- Circumvent any access restrictions or usage limits
- Scrape or collect user data without permission
- Post content that infringes intellectual property rights

### 4.2 Content Standards
All content you post must:
- Be accurate and not misleading
- Not violate any applicable laws
- Not contain hate speech or discrimination
- Not promote violence or illegal activities
- Respect the privacy of others

## 5. Marketplace Terms

### 5.1 Protocol Sales
- Sellers receive 85% of the sale price (platform retains 15%)
- Minimum payout threshold is $1.00 (earnings accumulate)
- All sales are final unless otherwise specified
- Sellers are responsible for the accuracy of their protocols

### 5.2 Purchases
- All purchases are subject to our refund policy
- You receive a license to use purchased protocols
- Redistribution of purchased protocols is prohibited

## 6. Intellectual Property

### 6.1 Our Content
InfoPilot Explorer, InfoJet 2.0™, and all related trademarks, logos, and content are owned by Top Pilot Enterprises, Inc.

### 6.2 Your Content
- You retain ownership of content you create
- You grant us a license to display and distribute your content
- You warrant that you have rights to all content you post

## 7. Community Guidelines

### 7.1 Groups and Pages
- Creators/admins may remove members who violate these terms
- Harassment or abuse will result in removal and potential account suspension
- Spam and self-promotion must comply with community standards

### 7.2 Moderation
- Group creators and admins may: boot, ban, or mute members
- Banned users cannot rejoin without admin approval
- Muted users can view but not post content

## 8. Subscription and Payment

### 8.1 Pay As You Go
- Our "Pay What You Want" model is currently in a promotional testing phase
- This promotion is available while supplies last
- We reserve the right to modify pricing at any time

### 8.2 Service Costs Disclosure
We want to be transparent: maintaining InfoPilot Explorer requires significant investment in:
- Google Maps API subscriptions
- AI Search API services (SerpAPI, DuckDuckGo)
- OpenAI Whisper for voice search
- GPT-5.2 for AI features
- Server infrastructure and bandwidth

Your support helps us keep this innovative platform running!

## 9. Limitation of Liability

InfoPilot Explorer is provided "AS IS" without warranties of any kind. We are not liable for:
- Service interruptions or data loss
- Accuracy of search results
- Actions of other users
- Third-party content or services

## 10. Termination

### 10.1 By You
You may delete your account at any time through Settings.

### 10.2 By Us
We may suspend or terminate accounts that violate these terms without notice.

## 11. Changes to Terms

We may update these terms at any time. Continued use constitutes acceptance of changes.

## 12. Governing Law

These terms are governed by the laws of the State of Maine, United States.

## 13. Contact Information

**Top Pilot Enterprises, Inc.**
Email: support@infopilotexplorer.com
Brunswick, Maine, USA

---

*"Three ventures. One mission. Zero turbulence."*

---

**By using InfoPilot Explorer, you acknowledge that you have read and agree to this User Agreement.**
"""

# ==================== PRIVACY POLICY ====================

PRIVACY_POLICY = """
# Privacy Policy

## Top Pilot Enterprises, Inc.
### InfoPilot Explorer Privacy Policy

**Effective Date: January 16, 2026**

Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your information.

---

## 1. Information We Collect

### 1.1 Account Information
- Email address
- Username and display name
- Password (encrypted)
- Profile information you choose to provide

### 1.2 Usage Information
- Search queries and protocols
- Categories and preferences
- Interaction with features
- Device and browser information
- IP address and location data

### 1.3 Payment Information
- PayPal email for marketplace sellers
- Transaction records
- Purchase history

### 1.4 Communication Data
- Messages sent through our platform
- Group and page posts
- Comments and reactions

## 2. How We Use Your Information

### 2.1 To Provide Services
- Deliver search results and recommendations
- Process marketplace transactions
- Enable social features and messaging
- Track achievements and gamification progress

### 2.2 To Improve Our Service
- Analyze usage patterns
- Develop new features
- Optimize performance
- Conduct A/B testing

### 2.3 To Communicate With You
- Send newsletters (if subscribed)
- Notify about account activity
- Provide customer support
- Send important service updates

## 3. Information Sharing

### 3.1 We DO NOT Sell Your Data
We never sell your personal information to third parties.

### 3.2 We May Share With:
- **Service Providers**: Payment processors (PayPal), AI services (OpenAI)
- **Legal Requirements**: When required by law or to protect rights
- **Business Transfers**: In case of merger or acquisition

### 3.3 Public Information
Your username, public posts, and public protocols are visible to other users.

## 4. Data Security

We implement industry-standard security measures:
- Encrypted passwords (bcrypt hashing)
- HTTPS encryption
- Secure session management
- Regular security audits

## 5. Your Rights

### 5.1 Access and Portability
You can access and download your data through Settings.

### 5.2 Correction
You can update your profile information at any time.

### 5.3 Deletion
You can request account deletion through Settings or by contacting us.

### 5.4 Opt-Out
You can unsubscribe from marketing emails at any time.

## 6. Cookies and Tracking

We use cookies and similar technologies to:
- Maintain your login session
- Remember preferences
- Analyze site usage
- Improve user experience

You can control cookies through your browser settings.

## 7. Third-Party Services

We integrate with:
- **Google Maps API**: For location-based features
- **PayPal**: For payment processing
- **OpenAI**: For AI-powered features
- **OAuth Providers**: For social login

These services have their own privacy policies.

## 8. Children's Privacy

InfoPilot Explorer is not intended for users under 13 years of age. We do not knowingly collect data from children under 13.

## 9. International Users

Our servers are located in the United States. By using our service, you consent to the transfer of your data to the US.

## 10. Data Retention

We retain your data as long as your account is active. After account deletion:
- Personal data is deleted within 30 days
- Anonymized usage data may be retained for analytics

## 11. Changes to This Policy

We may update this Privacy Policy. We will notify you of significant changes via email or in-app notification.

## 12. Contact Us

For privacy-related inquiries:

**Top Pilot Enterprises, Inc.**
Email: privacy@infopilotexplorer.com
Brunswick, Maine, USA

---

*Your trust is our priority. Thank you for choosing InfoPilot Explorer.*

---

**Last Updated: January 16, 2026**
"""


# ==================== API ENDPOINTS ====================

@router.get("/user-agreement", response_model=dict)
async def get_user_agreement():
    """Get the User Agreement document"""
    # Get any admin customizations
    custom = await db.settings.find_one({"key": "user_agreement_custom"})
    
    return {
        "content": custom.get("value", USER_AGREEMENT) if custom else USER_AGREEMENT,
        "version": "1.0.0",
        "effective_date": "2026-01-16",
        "last_updated": "2026-01-16"
    }


@router.get("/privacy-policy", response_model=dict)
async def get_privacy_policy():
    """Get the Privacy Policy document"""
    # Get any admin customizations
    custom = await db.settings.find_one({"key": "privacy_policy_custom"})
    
    return {
        "content": custom.get("value", PRIVACY_POLICY) if custom else PRIVACY_POLICY,
        "version": "1.0.0",
        "effective_date": "2026-01-16",
        "last_updated": "2026-01-16"
    }


@router.get("/terms-summary", response_model=dict)
async def get_terms_summary():
    """Get a short summary for sign-up flow"""
    return {
        "summary": """By creating an account, you agree to:
• Our User Agreement and Privacy Policy
• Be at least 13 years old
• Not post harmful, illegal, or abusive content
• Respect other users and community guidelines
• Allow us to use cookies and process your data as described in our Privacy Policy

Full documents available in Settings after sign-up.""",
        "links": {
            "user_agreement": "/api/legal/user-agreement",
            "privacy_policy": "/api/legal/privacy-policy"
        }
    }


@router.post("/accept-terms", response_model=dict)
async def accept_terms(user = Depends(get_current_user)):
    """Record user's acceptance of terms"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "terms_accepted": True,
            "terms_accepted_at": datetime.utcnow(),
            "terms_version": "1.0.0"
        }}
    )
    
    return {
        "success": True,
        "message": "Terms accepted",
        "accepted_at": datetime.utcnow().isoformat()
    }


@router.get("/acceptance-status", response_model=dict)
async def get_acceptance_status(user = Depends(get_current_user)):
    """Check if user has accepted current terms"""
    return {
        "terms_accepted": user.get("terms_accepted", False),
        "accepted_at": user.get("terms_accepted_at").isoformat() if user.get("terms_accepted_at") else None,
        "version_accepted": user.get("terms_version"),
        "current_version": "1.0.0",
        "needs_update": user.get("terms_version") != "1.0.0" if user.get("terms_accepted") else True
    }
