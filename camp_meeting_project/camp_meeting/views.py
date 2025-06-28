from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json, requests, os, base64, re
from .models import Contribution
from .forms import ContributionForm
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth.decorators import login_required
from django.conf import settings

# loading environment variables
load_dotenv()

# retrieving M-Pesa variables from Django settings
CONSUMER_KEY = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET
MPESA_PASSKEY = settings.MPESA_PASSKEY
MPESA_BASE_URL = settings.MPESA_BASE_URL
MPESA_SHORTCODE = settings.MPESA_SHORTCODE
CALLBACK_URL = settings.CALLBACK_URL

def camp_meeting_landing(request):
    """Main landing page view for Camp Meeting 2025"""
    # Event details
    event_date = timezone.make_aware(datetime(2025, 8, 17))
    event_end_date = timezone.make_aware(datetime(2025, 8, 24))
    current_date = timezone.now()

    # Calculate days left
    days_left = (event_date - current_date).days

    # Contribution statistics
    total_contributions = Contribution.objects.aggregate(total=Sum('amount'))['total'] or 0
    target_amount = 2300000
    percentage_raised = (total_contributions / target_amount) * 100

    # Latest contributions
    latest_contributions = Contribution.objects.filter(is_verified=True).order_by('-created_at')[:3]
    latest_contribution = latest_contributions.first()

    context = {
        'event_date': event_date,
        'event_end_date': event_end_date,
        'days_left': max(0, days_left),
        'total_contributions': total_contributions,
        'target_amount': target_amount,
        'percentage_raised': min(100, percentage_raised),
        'latest_contributions': latest_contributions,
        'latest_contribution': latest_contribution,
        'contribution_form': ContributionForm(),
    }

    return render(request, 'camp_meeting/landing.html', context)

def generate_access_token():
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"

    try:
        # encodeing credentials
        encoded_credentials = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode()

        headers = {'Authorization': f"Basic {encoded_credentials}", 'Content-Type': 'application/json'}

        # sending requests
        response = requests.get(url, headers=headers).json()

        # checking if there are errors
        if "access_token" in response:
            return response['access_token']
        else:
            raise Exception("Access token not found in response")
    except Exception as e:
        raise Exception(f"Error generating access token: {str(e)}")
    
def initiate_stk_push(phone_number, amount, contribution_id):
    try:
        token = generate_access_token()
        url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        stk_password = base64.b64encode((MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()).decode()

        payload = {
            "BusinessShortCode": "174379",
            "Password": stk_password,
            "Timestamp":timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA":phone_number,
            "PartyB":"174379",
            "PhoneNumber":phone_number,
            "CallBackURL": CALLBACK_URL,
            "AccountReference":"EdenSprings",
            "TransactionDesc":"Camp2025"
        }

        # sending the requests
        response = requests.post(url, headers=headers, json=payload).json()

        return response
    
    except Exception as e:
        raise Exception(f"Error sending STK push: {str(e)}")

def initiate_mpesa_payment(request):
    """Handle M-Pesa STK Push initiation and create a pending contribution record"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        email = data.get('email')
        amount = data.get('amount')
        full_name = data.get('full_name')

        # Validate input
        if not all([phone_number, email, amount, full_name]):
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)

        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+254'):
            phone_number = phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number

        # Create a pending contribution
        contribution = Contribution.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            amount=amount,
            status='pending',
            is_verified=False, 
        )

        # Initiate M-Pesa STK Push
        response = initiate_stk_push(phone_number, amount, contribution.id)
        print(response)

        if response.get('ResponseCode') == '0':
            checkout_request_id = response.get('CheckoutRequestID')
            contribution.checkout_request_id = checkout_request_id
            contribution.save()

            return JsonResponse({
                'success': True,
                'message': 'Payment request sent to your phone',
                'contribution_id': contribution.id,
                'checkout_request_id': checkout_request_id
            })
        else:
            contribution.status = 'failed'
            contribution.save()
            return JsonResponse({'success': False, 'message': 'Failed to initiate payment'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handles M-Pesa callback for payment verification and updates the contribution record"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only use POST method'}, status=405)

    try:
        callback_data = json.loads(request.body)
        stk_callback = callback_data['Body']['stkCallback']
        checkout_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']
        items = stk_callback.get('CallbackMetadata', {}).get('Item', [])

        amount = next((item['value'] for item in items if item['Name'] == 'Amount'), None)
        mpesa_code = next((item['value'] for item in items if item['Name'] == 'MpesaReceiptNumber'), None)
        phone = next((item['value'] for item in items if item['Name'] == 'PhoneNumber'), None)

        contribution = Contribution.objects.filter(checkout_request_id=checkout_id).first()
        if not contribution:
            return JsonResponse({'success': False, 'message': 'Original contribution not found'}, status=404)

        # Idempotency: Don't process if already completed
        if contribution.is_verified:
            return JsonResponse({'success': True, 'message': 'Already processed'}, status=200)

        if result_code != 0:
            error_message = stk_callback['ResultDesc']
            if str(result_code) == '1032':
                contribution.status = 'Cancelled'
            else:
                contribution.status = 'Failed'
            contribution.save()
            return JsonResponse({'success': False, 'message': f'Payment failed: {error_message}'}, status=400)

        # Update contribution
        contribution.status = 'Completed'
        contribution.is_verified = True
        contribution.mpesa_transaction_id = mpesa_code
        contribution.amount = amount
        contribution.phone_number = phone
        contribution.save()

        # Optionally: Send confirmation email here

        return JsonResponse({'success': True, 'message': 'Payment verified'}, status=200)

    except Exception as e:
        # Log the error for debugging
        import logging
        logging.exception("Error in mpesa_callback")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def query_stk_push(checkout_request_id):
    try:
        url = f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query"
        access_token = generate_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        stk_password = base64.b64encode((MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()).decode()

        request_body = {
        "BusinessShortCode": "174379",
        "Password": stk_password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(url, json=request_body, headers=headers)
        print("Query Response:", response.json())
        return response.json()
    
    except requests.RequestException as e:
        print(f"Error quering STK Push status: {str(e)}")
        return {"error": str(e)}

@csrf_exempt
@require_http_methods(["POST"])
def stk_status_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        checkout_request_id = data.get('checkout_request_id')
        print("Received Checkout Request ID:", checkout_request_id)
        if not checkout_request_id:
            return JsonResponse({'success': False, 'message': 'Missing CheckoutRequestID'}, status=400)

        contribution = Contribution.objects.filter(checkout_request_id=checkout_request_id).first()
        if not contribution:
            return JsonResponse({'success': False, 'message': 'Contribution not found'}, status=404)

        # quering stk push status
        status = query_stk_push(checkout_request_id)
        print(f"STK Push Status: {status}")

        # Handle pending status (user hasn't interacted yet)
        if status.get("errorCode") == "500.001.1001":
            return JsonResponse({
                'success': True,
                'status': {
                    'ResultCode': -1,
                    'ResultDesc': 'Pending: Awaiting user interaction',
                    'Status': 'Pending'
                }
            })

        # Only handle if ResultCode exists (user has responded)
        if "ResultCode" in status:
            result_code = int(status.get("ResultCode", -1))
            result_desc = status.get("ResultDesc", "Unknown result")

            # Extract MpesaReceiptNumber if present
            mpesa_code = status.get("MpesaReceiptNumber")

            if result_code == 0:
                contribution.status = "Completed"
                contribution.is_verified = True
                if mpesa_code:
                    contribution.mpesa_transaction_id = mpesa_code
            elif result_code == 1032:
                contribution.status = "Cancelled"
            else:
                contribution.status = "Failed"

            contribution.save()

            return JsonResponse({
                'success': True,
                'status': {
                    'ResultCode': result_code,
                    'ResultDesc': result_desc,
                    'Status': contribution.status,
                    'MpesaReceiptNumber': mpesa_code
                }
            })

        # 3. Handle unexpected response structure
        return JsonResponse({
            'success': False,
            'message': 'Unknown response structure from Safaricom',
            'raw_response': status
        }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import logging
        logging.exception("Error in stk_status_view")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def stk_status(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed'}, status=405)
    try:
        data = json.loads(request.body)
        checkout_id = data.get('checkout_request_id')
        contribution = Contribution.objects.filter(checkout_request_id=checkout_id).first()
        if not contribution:
            return JsonResponse({'success': False, 'message': 'Contribution not found'}, status=404)
        # You can also query the M-Pesa STK Push Query API here if you want real-time status from Safaricom
        return JsonResponse({
            'success': True,
            'status': {
                'ResultCode': 0 if contribution.is_verified else 1,
                'ResultDesc': 'Payment successful' if contribution.is_verified else (
                    'Payment failed' if contribution.status == 'Failed' else 'Pending or cancelled'
                )
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def get_contribution_stats(request):
    """API endpoint to get real-time contribution statistics"""
    total_contributions = Contribution.objects.filter(
        is_verified=True
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    target_amount = 2300000
    percentage_raised = (total_contributions / target_amount) * 100
    
    # Event countdown
    event_date = timezone.make_aware(datetime(2025, 8, 17))
    current_date = timezone.now()
    time_left = event_date - current_date
    
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    seconds = time_left.seconds % 60
    
    return JsonResponse({
        'total_contributions': total_contributions,
        'target_amount': target_amount,
        'percentage_raised': min(100, percentage_raised),
        'countdown': {
            'days': max(0, days),
            'hours': max(0, hours),
            'minutes': max(0, minutes),
            'seconds': max(0, seconds)
        }
    })

@login_required
def finance_report(request):
    # Filter only successful transactions
    transactions = Contribution.objects.filter(is_verified=True, status="Completed").order_by('-created_at')
    print("Finance report count:", transactions.count())

    # Check if PDF export is requested
    if request.GET.get('format') == 'pdf':
        # Render the HTML template to a string
        html_string = render_to_string('camp_meeting/finance_report.html', {
            'transactions': transactions,
            'is_export': True  # useful for hiding buttons or styles when exporting
        })

        # Create PDF from HTML
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        # Return as downloadable file
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="finance_report.pdf"'
        return response

    # Normal web view
    return render(request, 'camp_meeting/finance_report.html', {
        'transactions': transactions,
        'is_export': False
    })

# user login
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('camp_meeting:finance_report')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'camp_meeting/login.html')

# user logout
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('camp_meeting:login')
