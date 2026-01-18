"""
InfoPilot Explorer - Revenue Routes
Revenue dashboard and PDF/CSV export
Optimized with aggregation pipelines
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict
from datetime import datetime, timezone
import io

from utils.db import db
from utils.auth import require_user
from utils.db_optimization import get_user_revenue_optimized

router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/dashboard")
async def get_revenue_dashboard(user: Dict = Depends(require_user)):
    """Get revenue dashboard data.
    
    Optimized: Uses aggregation pipeline for efficient calculation.
    """
    revenue_data = await get_user_revenue_optimized(user["id"])
    revenue_data["wallet_balance"] = user.get("wallet_balance", 0)
    return revenue_data


@router.get("/export")
async def export_revenue_pdf(format: str = "pdf", user: Dict = Depends(require_user)):
    """Export revenue report as PDF or CSV."""
    sales = await db.purchases.find({"seller_id": user["id"], "status": "completed"}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(s.get("price", 0) * 0.85 for s in sales)
    
    if format == "csv":
        # Create CSV content
        csv_content = "Date,Protocol,Price,Your Share (85%)\n"
        for sale in sales:
            csv_content += f"{sale['created_at'][:10]},{sale['protocol_name']},{sale['price']},{round(sale['price'] * 0.85, 2)}\n"
        csv_content += f"\n,TOTAL,{sum(s.get('price', 0) for s in sales)},{round(total_revenue, 2)}\n"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=revenue_report_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    
    # Generate PDF using reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(HexColor("#fbbf24"))
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    
    c.setFillColor(HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "InfoPilot Explorer")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Revenue Report - {user['username']}")
    
    # Date
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 10)
    c.drawString(width - 150, height - 50, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Summary section
    y = height - 120
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Revenue Summary")
    
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Total Sales: {len(sales)}")
    y -= 20
    c.drawString(50, y, f"Gross Revenue: ${sum(s.get('price', 0) for s in sales):.2f}")
    y -= 20
    c.drawString(50, y, f"Your Earnings (85%): ${total_revenue:.2f}")
    y -= 20
    c.drawString(50, y, f"Platform Fee (15%): ${sum(s.get('price', 0) for s in sales) * 0.15:.2f}")
    
    # Sales table
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Sales Details")
    
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Date")
    c.drawString(150, y, "Protocol")
    c.drawString(400, y, "Price")
    c.drawString(480, y, "Your Share")
    
    c.line(50, y - 5, width - 50, y - 5)
    
    y -= 20
    c.setFont("Helvetica", 10)
    for sale in sales[-20:]:  # Last 20 sales
        if y < 100:
            c.showPage()
            y = height - 50
        c.drawString(50, y, sale.get("created_at", "")[:10])
        c.drawString(150, y, sale.get("protocol_name", "Unknown")[:35])
        c.drawString(400, y, f"${sale.get('price', 0):.2f}")
        c.drawString(480, y, f"${sale.get('price', 0) * 0.85:.2f}")
        y -= 18
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 30, "Top Pilot Enterprises, Inc. - First in Flight with Monetization of Searches!")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=revenue_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )
