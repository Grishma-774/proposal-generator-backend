
import os

# Use the browser installed inside the Playwright package
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from playwright.sync_api import sync_playwright
from decimal import Decimal, InvalidOperation


@api_view(["POST"])
def generate_pdf(request):

    try:
        # Get proposal data from React
        proposal = request.data.get("proposal", {})
        template_name = request.data.get("template", "modern")

        # Allow only these three templates
        allowed_templates = ["modern", "corporate", "creative"]

        if template_name not in allowed_templates:
            return JsonResponse(
                {"error": "Invalid template selected"},
                status=400
            )

        # Format project price
        currency_symbols = {
            "INR": "₹",
            "USD": "$",
            "EUR": "€"
        }

        currency = proposal.get("currency", "INR")

        try:
            amount = Decimal(str(proposal.get("pricing", 0)))
            if not amount.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return JsonResponse(
                {"error": "Invalid pricing value"},
                status=400
            )

        symbol = currency_symbols.get(currency, "₹")
        price = f"{symbol}{amount:,.0f}"

        # Load the selected HTML template
        html = render_to_string(
            f"pdf_generator/{template_name}.html",
            {
                "proposal": proposal,
                "price": price
            }
        )

        # Generate PDF using Playwright and Microsoft Edge
        with sync_playwright() as p:

            browser = p.chromium.launch()

            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True
            )

            browser.close()

        # Return PDF to React
        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf"
        )

        response["Content-Disposition"] = (
            'attachment; filename="business_proposal.pdf"'
        )

        return response

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


# Create your views here.
