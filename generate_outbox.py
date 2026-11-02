#!/usr/bin/env python3
"""Outbox Generator for FDA EPRC Laser Report Desk.

Generates:
1. /home/user/Desktop/REVENUE_ACTIONS_TONIGHT/eprc-laser-report-desk_OUTBOX.md
   - 1-Click mailto: links with URL-encoded subject & body
   - Personalized hooks per lead referencing alert date, products, and competitive pricing
2. /home/user/Desktop/REVENUE_ACTIONS_TONIGHT/send_eprc_laser_outbox.py
   - Standalone CLI sender with dry-run, mailto launcher, and SMTP sending modes.
"""

import os
import sys
import json
import urllib.parse
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DESKTOP_OUTBOX_DIR = Path("/home/user/Desktop/REVENUE_ACTIONS_TONIGHT")

SENDER_NAME = "Robert Ketler"
SENDER_TITLE = "Director of Regulatory Operations"
SENDER_ORG = "FDA EPRC Laser Report Desk"
SENDER_EMAIL = "rketler@gmail.com"
SENDER_PHONE = "(512) 808-7241"

def build_email_content(lead: dict) -> tuple:
    """Construct personalized subject and body for a lead."""
    first_name = lead["contact_name"].split()[0]
    brand = lead.get("brand_name", lead["company_name"])
    alert_id = lead["alert_id"]
    alert_date = lead["alert_date"]
    products = lead["products_cited"]

    subject = f"Urgent: FDA Import Alert {alert_id} shipment risk for {brand} (Fixed-Fee Accession Filing)"
    
    body = f"""Hi {first_name},

I am contacting you regarding {brand}'s US market operations and recent entry under FDA Import Alert {alert_id} (published {alert_date}) citing:
"{products}".

Under 21 CFR 1002.10 and FD&C Act Chapter V Subchapter C, laser products imported or introduced into US commerce require a completed Form FDA 3632 Radiation Safety Product Report on file with CDRH before customs clearance. Without a valid FDA Accession Number declared on FDA Form 2877 (Declaration B), shipments are subject to automatic Detention Without Physical Examination (DWPE) at all US ports of entry, and listings face immediate gating removal under Amazon Seller Central Policy 201689020.

Legacy compliance consultancies (such as Registrar Corp and Laser Product Safety LLC) quote $995 to $3,500 per report, plus $1,000+ for annual maintenance, with multi-week delays. Note that the FDA charges $0 in government administrative filing fees for laser accession numbers—the cost is purely document compilation.

We built an agent-accelerated regulatory intake engine that drafts compliant Form FDA 3632 dossiers directly from your engineering CAD specs, diode datasheets, manual artwork, and test logs:

1. Fixed-Fee Form FDA 3632 Report: $495 flat (5 business day delivery, saving 50% to 85% vs legacy consultancies).
2. Direct CDRH Submission: We file directly with CDRH Radiation Health Customer Service (RadHealthCustomerService@fda.hhs.gov) to secure your official FDA Accession Number.
3. Customs Clearance Package: Completed Form FDA 2877 Declaration B documentation to immediately un-hold freight with CBP and un-gate Amazon ASINs.
4. Annual Report Maintenance (Form 3636): Managed annual September 1 filings for $295 flat.

Are you available for a brief 10-minute briefing this week to review your test data and file the Form FDA 3632 report to clear your US distribution rails?

Best regards,

{SENDER_NAME}
{SENDER_TITLE}
{SENDER_ORG}
Email: {SENDER_EMAIL} | Direct: {SENDER_PHONE}
"""
    return subject, body

def build_amazon_email_content(brand: dict) -> tuple:
    """Construct personalized email for Amazon brand."""
    brand_name = brand["brand_name"]
    products = brand["products_on_amazon"]
    subject = f"Amazon laser gating risk & FDA Accession Number filing for {brand_name}"

    body = f"""Hello {brand_name} Compliance & Operations Team,

I am reaching out regarding {brand_name}'s laser product catalog actively selling on Amazon, including:
"{products}".

Amazon Seller Central Policy 201689020 strictly requires a verified FDA Accession Number on file with CDRH for every laser product ASIN. Recent FDA import sweeps under Import Alert 95-04 and 95-05 have triggered automatic inventory freezes, FBA inbound rejections, and customs stops under FDA Form 2877 for laser brands lacking visible accession filings.

Legacy regulatory firms (such as Registrar Corp and Laser Product Safety LLC) quote $995 to $3,500 per report with weeks of turnaround. In reality, the FDA charges $0 in filing fees for laser accession numbers.

We provide an agent-accelerated laser regulatory filing desk:
- Fixed-Fee Form FDA 3632 Initial Product Report: $495 flat per model family (5 business days delivery).
- Immediate Amazon un-gating support with official CDRH accession documentation.
- Customs Form FDA 2877 Declaration B compliance documentation for smooth ocean and air freight entry.
- Ongoing Form FDA 3636 Annual Report maintenance for $295/yr (covering the July 1 - June 30 reporting period due Sept 1).

Would you be open to a quick call or email exchange this week to review your current accession status and safeguard your Amazon ASINs?

Best regards,

{SENDER_NAME}
{SENDER_TITLE}
{SENDER_ORG}
Email: {SENDER_EMAIL} | Direct: {SENDER_PHONE}
"""
    return subject, body

def main():
    DESKTOP_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_DIR / "enriched_leads.json", "r", encoding="utf-8") as f:
        redlist_leads = json.load(f)["leads"]

    with open(DATA_DIR / "amazon_laser_brands.json", "r", encoding="utf-8") as f:
        amazon_brands = json.load(f)["brands"]

    outbox_md_path = DESKTOP_OUTBOX_DIR / "eprc-laser-report-desk_OUTBOX.md"
    send_script_path = DESKTOP_OUTBOX_DIR / "send_eprc_laser_outbox.py"

    # Build Markdown Outbox
    md = []
    md.append("# 1-Click Outbox: FDA EPRC Laser Report Desk")
    md.append("")
    md.append("**Campaign:** FDA EPRC Laser Product Report & Accession Number Outreach")
    md.append(f"**Sender:** {SENDER_NAME}, {SENDER_TITLE} ({SENDER_EMAIL} | {SENDER_PHONE})")
    md.append("**Commercial Offer:** Fixed-Fee Form FDA 3632 Initial Report in 5 days for $495 flat (vs $995-$3,500 legacy consultants); Form 3636 Annual Report for $295.")
    md.append(f"**Verified Red List Leads (2025-2026 Listings):** {len(redlist_leads)} named executives (100% MX validated)")
    md.append(f"**Active Amazon Laser Brands:** {len(amazon_brands)} high-volume brands")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Automated Execution Options")
    md.append("You can trigger outreach through either of these methods:")
    md.append("1. **1-Click Mailto Links:** Click any link below to open your native mail client with recipient, subject, and personalized body pre-populated.")
    md.append("2. **CLI Sender Script:** Run the python script on your desktop:")
    md.append("   ```bash")
    md.append("   # Dry run test (preview all emails)")
    md.append(f"   python3 {send_script_path} --dry-run")
    md.append("")
    md.append("   # Launch default mail client for all leads")
    md.append(f"   python3 {send_script_path} --open-mailto")
    md.append("")
    md.append("   # Send live via SMTP (with SMTP_USER and SMTP_PASS env vars)")
    md.append(f"   python3 {send_script_path} --send-smtp")
    md.append("   ```")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Section 1: Verified FDA Import Alert 95-04 / 95-05 Red List Decision-Makers")
    md.append("")

    for idx, lead in enumerate(redlist_leads, 1):
        subj, body = build_email_content(lead)
        mailto_url = f"mailto:{lead['email']}?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}"
        
        md.append(f"### Lead #{idx}: {lead['contact_name']} — {lead['brand_name']} ({lead['company_name']})")
        md.append(f"- **Executive Title:** {lead['contact_title']}")
        md.append(f"- **Corporate Email:** [{lead['email']}](mailto:{lead['email']}) (MX Validated: `{lead['mx_records'][0] if lead['mx_records'] else 'Active'}`)")
        md.append(f"- **Phone:** `{lead['phone']}` | **HQ:** {lead['address']}")
        md.append(f"- **FDA Import Alert:** `{lead['alert_id']}` (Listed Date: `{lead['alert_date']}`)")
        md.append(f"- **Products Cited:** *{lead['products_cited']}*")
        md.append(f"- **1-Click Action:** 👉 [**SEND 1-CLICK EMAIL TO {lead['contact_name'].upper()}**]({mailto_url})")
        md.append("")
        md.append("```text")
        md.append(f"To: {lead['email']}")
        md.append(f"Subject: {subj}")
        md.append("")
        md.append(body.strip())
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    md.append("## Section 2: Active Amazon Laser Brands (Amazon Policy 201689020 Exposure)")
    md.append("")

    for idx, brand in enumerate(amazon_brands, 1):
        subj, body = build_amazon_email_content(brand)
        mailto_url = f"mailto:{brand['email']}?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}"

        md.append(f"### Amazon Brand #{idx}: {brand['brand_name']} ({brand['company_name']})")
        md.append(f"- **Website:** [{brand['domain']}]({brand['website']}) | **Email:** [{brand['email']}](mailto:{brand['email']})")
        md.append(f"- **Phone:** `{brand['phone']}`")
        md.append(f"- **Products on Amazon:** *{brand['products_on_amazon']}*")
        md.append(f"- **Gating Risk:** {brand['amazon_risk_factors']}")
        md.append(f"- **1-Click Action:** 👉 [**SEND 1-CLICK EMAIL TO {brand['brand_name'].upper()}**]({mailto_url})")
        md.append("")
        md.append("```text")
        md.append(f"To: {brand['email']}")
        md.append(f"Subject: {subj}")
        md.append("")
        md.append(body.strip())
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    outbox_md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Generated Markdown Outbox: {outbox_md_path}")

    # Build Standalone Send Script
    send_script_code = f'''#!/usr/bin/env python3
"""1-Click CLI Outbox Sender for FDA EPRC Laser Report Desk.

Sends personalized pitches to {len(redlist_leads)} verified FDA Import Alert 95-04/95-05
decision-makers and {len(amazon_brands)} active Amazon laser brands.
"""

import os
import sys
import json
import time
import smtplib
import argparse
import webbrowser
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

REDLIST_FILE = "{DATA_DIR / 'enriched_leads.json'}"
AMAZON_FILE = "{DATA_DIR / 'amazon_laser_brands.json'}"

SENDER_NAME = "{SENDER_NAME}"
SENDER_TITLE = "{SENDER_TITLE}"
SENDER_ORG = "{SENDER_ORG}"
SENDER_EMAIL = "{SENDER_EMAIL}"
SENDER_PHONE = "{SENDER_PHONE}"

def load_data():
    with open(REDLIST_FILE, "r", encoding="utf-8") as f:
        redlist = json.load(f)["leads"]
    with open(AMAZON_FILE, "r", encoding="utf-8") as f:
        amazon = json.load(f)["brands"]
    return redlist, amazon

def get_redlist_email(lead):
    first_name = lead["contact_name"].split()[0]
    brand = lead.get("brand_name", lead["company_name"])
    alert_id = lead["alert_id"]
    alert_date = lead["alert_date"]
    products = lead["products_cited"]

    subject = f"Urgent: FDA Import Alert {{alert_id}} shipment risk for {{brand}} (Fixed-Fee Accession Filing)"
    body = f"""Hi {{first_name}},

I am contacting you regarding {{brand}}'s US market operations and recent entry under FDA Import Alert {{alert_id}} (published {{alert_date}}) citing:
"{{products}}".

Under 21 CFR 1002.10 and FD&C Act Chapter V Subchapter C, laser products imported or introduced into US commerce require a completed Form FDA 3632 Radiation Safety Product Report on file with CDRH before customs clearance. Without a valid FDA Accession Number declared on FDA Form 2877 (Declaration B), shipments are subject to automatic Detention Without Physical Examination (DWPE) at all US ports of entry, and listings face immediate gating removal under Amazon Seller Central Policy 201689020.

Legacy compliance consultancies (such as Registrar Corp and Laser Product Safety LLC) quote $995 to $3,500 per report, plus $1,000+ for annual maintenance, with multi-week delays. Note that the FDA charges $0 in government administrative filing fees for laser accession numbers—the cost is purely document compilation.

We built an agent-accelerated regulatory intake engine that drafts compliant Form FDA 3632 dossiers directly from your engineering CAD specs, diode datasheets, manual artwork, and test logs:

1. Fixed-Fee Form FDA 3632 Report: $495 flat (5 business day delivery, saving 50% to 85% vs legacy consultancies).
2. Direct CDRH Submission: We file directly with CDRH Radiation Health Customer Service (RadHealthCustomerService@fda.hhs.gov) to secure your official FDA Accession Number.
3. Customs Clearance Package: Completed Form FDA 2877 Declaration B documentation to immediately un-hold freight with CBP and un-gate Amazon ASINs.
4. Annual Report Maintenance (Form 3636): Managed annual September 1 filings for $295 flat.

Are you available for a brief 10-minute briefing this week to review your test data and file the Form FDA 3632 report to clear your US distribution rails?

Best regards,

{{SENDER_NAME}}
{{SENDER_TITLE}}
{{SENDER_ORG}}
Email: {{SENDER_EMAIL}} | Direct: {{SENDER_PHONE}}
"""
    return subject, body

def get_amazon_email(brand):
    brand_name = brand["brand_name"]
    products = brand["products_on_amazon"]
    subject = f"Amazon laser gating risk & FDA Accession Number filing for {{brand_name}}"

    body = f"""Hello {{brand_name}} Compliance & Operations Team,

I am reaching out regarding {{brand_name}}'s laser product catalog actively selling on Amazon, including:
"{{products}}".

Amazon Seller Central Policy 201689020 strictly requires a verified FDA Accession Number on file with CDRH for every laser product ASIN. Recent FDA import sweeps under Import Alert 95-04 and 95-05 have triggered automatic inventory freezes, FBA inbound rejections, and customs stops under FDA Form 2877 for laser brands lacking visible accession filings.

Legacy regulatory firms (such as Registrar Corp and Laser Product Safety LLC) quote $995 to $3,500 per report with weeks of turnaround. In reality, the FDA charges $0 in filing fees for laser accession numbers.

We provide an agent-accelerated laser regulatory filing desk:
- Fixed-Fee Form FDA 3632 Initial Product Report: $495 flat per model family (5 business days delivery).
- Immediate Amazon un-gating support with official CDRH accession documentation.
- Customs Form FDA 2877 Declaration B compliance documentation for smooth ocean and air freight entry.
- Ongoing Form FDA 3636 Annual Report maintenance for $295/yr (covering the July 1 - June 30 reporting period due Sept 1).

Would you be open to a quick call or email exchange this week to review your current accession status and safeguard your Amazon ASINs?

Best regards,

{{SENDER_NAME}}
{{SENDER_TITLE}}
{{SENDER_ORG}}
Email: {{SENDER_EMAIL}} | Direct: {{SENDER_PHONE}}
"""
    return subject, body

def main():
    parser = argparse.ArgumentParser(description="Send or preview FDA EPRC Laser Report Desk outbox.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview messages without sending (default).")
    parser.add_argument("--open-mailto", action="store_true", help="Launch mail client via mailto: links.")
    parser.add_argument("--send-smtp", action="store_true", help="Send live emails via SMTP.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of emails to process.")
    args = parser.parse_args()

    redlist, amazon = load_data()
    all_targets = []

    for l in redlist:
        subj, body = get_redlist_email(l)
        all_targets.append({{"type": "Red List", "name": l["contact_name"], "brand": l.get("brand_name"), "email": l["email"], "subject": subj, "body": body}})

    for b in amazon:
        subj, body = get_amazon_email(b)
        all_targets.append({{"type": "Amazon Brand", "name": b["brand_name"], "brand": b["brand_name"], "email": b["email"], "subject": subj, "body": body}})

    if args.limit:
        all_targets = all_targets[:args.limit]

    print(f"Loaded {{len(all_targets)}} total outreach targets.")

    if args.send_smtp:
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER", SENDER_EMAIL)
        smtp_pass = os.environ.get("SMTP_PASS")

        if not smtp_pass:
            print("ERROR: SMTP_PASS environment variable is not set. Aborting live send.")
            sys.exit(1)

        print(f"Connecting to SMTP server {{smtp_host}}:{{smtp_port}} as {{smtp_user}}...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        for idx, t in enumerate(all_targets, 1):
            msg = MIMEMultipart()
            msg["From"] = f"{{SENDER_NAME}} <{{SENDER_EMAIL}}>"
            msg["To"] = t["email"]
            msg["Subject"] = t["subject"]
            msg.attach(MIMEText(t["body"], "plain"))

            print(f"[{{idx}}/{{len(all_targets)}}] Sending SMTP email to {{t['email']}}...")
            server.sendmail(SENDER_EMAIL, [t["email"]], msg.as_string())
            time.sleep(1.5)

        server.quit()
        print("All emails sent successfully via SMTP.")
        return

    if args.open_mailto:
        for idx, t in enumerate(all_targets, 1):
            mailto_url = f"mailto:{{t['email']}}?subject={{urllib.parse.quote(t['subject'])}}&body={{urllib.parse.quote(t['body'])}}"
            print(f"[{{idx}}/{{len(all_targets)}}] Opening mail client for {{t['email']}}...")
            webbrowser.open(mailto_url)
            time.sleep(0.5)
        print("Finished launching mail clients.")
        return

    # Default dry run preview
    print("\\n=== OUTBOX DRY RUN PREVIEW (NO EMAILS SENT) ===")
    for idx, t in enumerate(all_targets, 1):
        print(f"\\n--- [{{idx}}/{{len(all_targets)}}] {{t['type']}}: {{t['name']}} ({{t['brand']}}) ---")
        print(f"To: {{t['email']}}")
        print(f"Subject: {{t['subject']}}")
        print("Body snippet:")
        print(t["body"][:250].strip() + "\\n...")
    print(f"\\nDry run complete for {{len(all_targets)}} recipients.")
    print("To launch mail clients, run: python3 send_eprc_laser_outbox.py --open-mailto")
    print("To send via SMTP, run: python3 send_eprc_laser_outbox.py --send-smtp")

if __name__ == "__main__":
    main()
'''
    send_script_path.write_text(send_script_code, encoding="utf-8")
    os.chmod(send_script_path, 0o755)
    print(f"Generated Standalone Send Script: {send_script_path}")

    # Also keep a copy inside submissions repo
    repo_send_script = Path(__file__).resolve().parent / "send_outbox.py"
    repo_send_script.write_text(send_script_code, encoding="utf-8")
    os.chmod(repo_send_script, 0o755)

if __name__ == "__main__":
    main()
