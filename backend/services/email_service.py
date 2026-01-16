"""
InfoPilot Explorer - Email Service
Handles sending emails via Gmail SMTP for A/B test reports and notifications
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Optional, List
import os

from config import logger

# Gmail SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def is_email_configured() -> bool:
    """Check if email credentials are configured"""
    return bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None,
    attachments: Optional[List[dict]] = None
) -> dict:
    """
    Send an email via Gmail SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body of the email
        plain_content: Plain text fallback (optional)
        attachments: List of {'filename': str, 'content': bytes} (optional)
    
    Returns:
        dict with success status and message
    """
    if not is_email_configured():
        logger.warning("Email not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        return {
            "success": False,
            "error": "Email not configured. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD."
        }
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"InfoPilot Explorer <{GMAIL_ADDRESS}>"
        message["To"] = to_email
        
        # Add plain text part (fallback)
        if plain_content:
            part1 = MIMEText(plain_content, "plain")
            message.attach(part1)
        
        # Add HTML part
        part2 = MIMEText(html_content, "html")
        message.attach(part2)
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment['filename']}"
                )
                message.attach(part)
        
        # Create secure connection and send
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, message.as_string())
        
        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True, "message": f"Email sent to {to_email}"}
    
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed. Check app password.")
        return {
            "success": False,
            "error": "Gmail authentication failed. Please check your app password."
        }
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}


def generate_ab_test_report_html(report_data: dict) -> str:
    """
    Generate HTML email content for A/B test report
    
    Args:
        report_data: Dictionary containing A/B test analytics data
    
    Returns:
        HTML string for the email body
    """
    tests = report_data.get("tests", [])
    period = report_data.get("period_days", 7)
    total_impressions = report_data.get("total_impressions", 0)
    total_conversions = report_data.get("total_conversions", 0)
    overall_rate = report_data.get("overall_conversion_rate", 0)
    generated_at = report_data.get("generated_at", datetime.now(timezone.utc).isoformat())
    
    # Build test rows
    test_rows = ""
    for test in tests:
        status_color = "#10b981" if test.get("is_active") else "#6b7280"
        status_text = "Active" if test.get("is_active") else "Paused"
        leading = test.get("leading_variant", "-")
        
        test_rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: 500;">{test['name'].replace('_', ' ').title()}</td>
            <td style="padding: 12px; text-align: center;">
                <span style="background: {status_color}20; color: {status_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                    {status_text}
                </span>
            </td>
            <td style="padding: 12px; text-align: center;">{test.get('variant_count', 0)}</td>
            <td style="padding: 12px; text-align: center;">{test.get('total_events', 0):,}</td>
            <td style="padding: 12px; text-align: center;">
                <strong style="color: #8b5cf6;">{leading}</strong>
            </td>
        </tr>
        """
    
    # Winners section
    winners_section = ""
    winners = [t for t in tests if t.get("leading_variant") and t.get("total_events", 0) >= 100]
    if winners:
        winners_section = """
        <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h3 style="color: #92400e; margin: 0 0 15px 0;">🏆 Winning Variants (100+ events)</h3>
            <ul style="margin: 0; padding-left: 20px; color: #78350f;">
        """
        for w in winners:
            winners_section += f"<li><strong>{w['name'].replace('_', ' ').title()}</strong>: Variant {w['leading_variant']} is leading</li>"
        winners_section += "</ul></div>"
    
    # Revenue impact estimate (hypothetical calculation)
    estimated_impact = ""
    if total_conversions > 0 and overall_rate > 0:
        # Assume 10% improvement from A/B testing optimization
        potential_improvement = total_conversions * 0.1
        # Assume average order value of $2.99 (book price)
        potential_revenue = potential_improvement * 2.99
        estimated_impact = f"""
        <div style="background: linear-gradient(135deg, #d1fae5, #a7f3d0); border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h3 style="color: #065f46; margin: 0 0 10px 0;">💰 Estimated Revenue Impact</h3>
            <p style="color: #047857; margin: 0; font-size: 14px;">
                With {total_conversions:,} conversions and {overall_rate}% conversion rate, 
                optimizing winning variants could potentially add <strong>${potential_revenue:.2f}</strong> in revenue 
                (assuming 10% improvement from A/B optimization).
            </p>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🧪 A/B Test Weekly Report</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">
                    InfoPilot Explorer • Last {period} Days
                </p>
            </div>
            
            <!-- Summary Cards -->
            <div style="padding: 20px; display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
                <div style="background: #f0f9ff; border-radius: 12px; padding: 15px 25px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: 700; color: #3b82f6;">{len(tests)}</div>
                    <div style="font-size: 12px; color: #6b7280;">Active Tests</div>
                </div>
                <div style="background: #f0fdf4; border-radius: 12px; padding: 15px 25px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: 700; color: #10b981;">{total_impressions:,}</div>
                    <div style="font-size: 12px; color: #6b7280;">Impressions</div>
                </div>
                <div style="background: #fef3c7; border-radius: 12px; padding: 15px 25px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: 700; color: #f59e0b;">{total_conversions:,}</div>
                    <div style="font-size: 12px; color: #6b7280;">Conversions</div>
                </div>
                <div style="background: #fce7f3; border-radius: 12px; padding: 15px 25px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: 700; color: #ec4899;">{overall_rate}%</div>
                    <div style="font-size: 12px; color: #6b7280;">Conv. Rate</div>
                </div>
            </div>
            
            {winners_section}
            
            {estimated_impact}
            
            <!-- Tests Table -->
            <div style="padding: 0 20px 20px 20px;">
                <h3 style="color: #1f2937; margin: 0 0 15px 0;">📊 Test Performance</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <thead>
                            <tr style="background: #f9fafb;">
                                <th style="padding: 12px; text-align: left; color: #6b7280; font-weight: 600;">Test Name</th>
                                <th style="padding: 12px; text-align: center; color: #6b7280; font-weight: 600;">Status</th>
                                <th style="padding: 12px; text-align: center; color: #6b7280; font-weight: 600;">Variants</th>
                                <th style="padding: 12px; text-align: center; color: #6b7280; font-weight: 600;">Events</th>
                                <th style="padding: 12px; text-align: center; color: #6b7280; font-weight: 600;">Leading</th>
                            </tr>
                        </thead>
                        <tbody>
                            {test_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div style="background: #ede9fe; padding: 20px; margin: 0 20px 20px 20px; border-radius: 12px;">
                <h3 style="color: #5b21b6; margin: 0 0 10px 0;">🎯 Recommendations</h3>
                <ul style="color: #6d28d9; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                    <li>Tests with 1,000+ impressions have statistical significance</li>
                    <li>Consider promoting winning variants to 100% traffic</li>
                    <li>Create new tests for underperforming elements</li>
                    <li>Review the A/B Dashboard for detailed variant breakdowns</li>
                </ul>
            </div>
            
            <!-- CTA -->
            <div style="text-align: center; padding: 0 20px 30px 20px;">
                <a href="https://infopilot-explorer.preview.emergentagent.com/#admin" 
                   style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    View Full Dashboard →
                </a>
            </div>
            
            <!-- Footer -->
            <div style="background: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; margin: 0; font-size: 12px;">
                    Generated on {generated_at[:10]} • InfoPilot Explorer
                </p>
                <p style="color: #9ca3af; margin: 10px 0 0 0; font-size: 11px;">
                    You're receiving this because you're an admin of InfoPilot Explorer.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_ab_test_report_plain(report_data: dict) -> str:
    """Generate plain text version of A/B test report"""
    tests = report_data.get("tests", [])
    period = report_data.get("period_days", 7)
    
    plain = f"""
A/B TEST WEEKLY REPORT - InfoPilot Explorer
============================================
Period: Last {period} days

SUMMARY
-------
Active Tests: {len(tests)}
Total Impressions: {report_data.get('total_impressions', 0):,}
Total Conversions: {report_data.get('total_conversions', 0):,}
Overall Conversion Rate: {report_data.get('overall_conversion_rate', 0)}%

TEST PERFORMANCE
----------------
"""
    
    for test in tests:
        status = "Active" if test.get("is_active") else "Paused"
        leading = test.get("leading_variant", "N/A")
        plain += f"""
{test['name'].replace('_', ' ').title()}
  Status: {status}
  Variants: {test.get('variant_count', 0)}
  Events: {test.get('total_events', 0):,}
  Leading Variant: {leading}
"""
    
    plain += """
RECOMMENDATIONS
---------------
- Tests with 1,000+ impressions have statistical significance
- Consider promoting winning variants to 100% traffic
- Review the A/B Dashboard for detailed breakdowns

View full dashboard: https://infopilot-explorer.preview.emergentagent.com/#admin
"""
    
    return plain


# ==================== LEGACY EMAIL SERVICE CLASS ====================
# For backward compatibility with newsletter routes in admin.py

class EmailService:
    """Legacy email service class for backward compatibility"""
    
    @staticmethod
    async def generate_newsletter_content():
        """Generate newsletter content"""
        from config import BOOK_PROMO
        return f"""
        <h1>InfoPilot Weekly Update</h1>
        <p>Welcome to this week's InfoPilot newsletter!</p>
        <h2>Featured Book: {BOOK_PROMO.get('title', 'Letters to Evelyn')}</h2>
        <p>By {BOOK_PROMO.get('author', 'John Selman')}</p>
        <p>{BOOK_PROMO.get('genre', 'Fiction')}</p>
        <p>Available for {BOOK_PROMO.get('price', '$2.99')} on <a href="{BOOK_PROMO.get('amazon_url', '#')}">Amazon</a></p>
        """
    
    @staticmethod
    async def get_subscriber_emails():
        """Get list of subscriber emails"""
        from config import db
        users = await db.users.find({"email": {"$exists": True}}).to_list(1000)
        return [u["email"] for u in users if u.get("email")]
    
    @staticmethod
    async def send_newsletter(subject: str, content: str, emails: List[str]) -> dict:
        """Send newsletter to multiple recipients"""
        if not is_email_configured():
            return {"success": False, "error": "Email not configured"}
        
        success_count = 0
        failed_count = 0
        
        for email in emails[:100]:  # Limit to 100
            try:
                result = await send_email(email, subject, content)
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {email}: {e}")
                failed_count += 1
        
        return {
            "success": success_count > 0,
            "sent_count": success_count,
            "failed_count": failed_count
        }
    
    @staticmethod
    async def send_test_email(recipient: str) -> dict:
        """Send a test newsletter email"""
        content = await EmailService.generate_newsletter_content()
        return await send_email(recipient, "InfoPilot Test Newsletter", content)
