from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from twilio.rest import Client
from decouple import config
import random
from pymongo import MongoClient
from bson import ObjectId
from deepface import DeepFace
import os
import cv2
import numpy as np
import logging
from django.conf import settings
from io import BytesIO
from PIL import Image
import base64
import time
import qrcode
import uuid
from django.urls import reverse
from functools import lru_cache
from datetime import datetime
from io import BytesIO
import json
import base64
import logging
import os
import time
from io import BytesIO
from PIL import Image
import numpy as np
from deepface import DeepFace
from django.conf import settings
from django.http import JsonResponse
from bson import ObjectId
from voting_system_backend.web3_config import w3, contract, PRIVATE_KEY





# MongoDB Connection
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["voter_registration_db"]
mongo_collection = mongo_db["user_data"]
features_collection = mongo_db["features"]

# Twilio Credentials
TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = config("TWILIO_PHONE_NUMBER")

# Logging Configuration
logging.basicConfig(level=logging.DEBUG)

# Optimized face embedding function
@lru_cache(maxsize=128)
def get_face_embeddings(image_path):
    return DeepFace.represent(
        img_path=image_path,
        model_name='Facenet',
        enforce_detection=True,
        detector_backend='retinaface',
        align=True
    )

# Home Page
def home_page(request):
    return render(request, "home.html")

# Registration
def register_user(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        unique_id = request.POST.get("unique_id", "").strip()

        if not all([name, phone_number, unique_id]):
            return render(request, "register.html", {"error": "All fields are required."})

        user_data = mongo_collection.find_one({
            "name": name,
            "phone_number": phone_number,
            "unique_id": unique_id
        })

        if user_data:
            if "login_id" in user_data:
                return render(request, "already_registered.html", {
                    "login_id": user_data["login_id"]
                })

            otp = str(random.randint(100000, 999999))
            request.session["otp"] = otp
            request.session["phone_number"] = phone_number

            try:
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"Your OTP for voter registration is {otp}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=f"+91{phone_number}"
                )
                return render(request, "enter_otp.html")
            except Exception as e:
                logging.error(f"Failed to send OTP: {str(e)}")
                return render(request, "register.html", {"error": "Failed to send OTP. Please try again later."})

        return render(request, "register.html", {"error": "User not found in database."})

    return render(request, "register.html")

# OTP Verification
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        saved_otp = request.session.get("otp")
        phone_number = request.session.get("phone_number")

        if not saved_otp or not phone_number:
            return redirect('register_user')

        if str(entered_otp) == str(saved_otp):
            unique_login_id = f"USER{random.randint(10000, 99999)}"
            update_result = mongo_collection.find_one_and_update(
                {"phone_number": phone_number},
                {"$set": {"login_id": unique_login_id, "registration_status": "complete"}}
            )

            if update_result:
                # Send SMS with login ID
                try:
                    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                    message = f"Smart Election Commission: Registration successful! Your Login ID: {unique_login_id}. Please use this ID to login and proceed with voting."
                    client.messages.create(
                        body=message,
                        from_=TWILIO_PHONE_NUMBER,
                        to=f"+91{phone_number}"
                    )
                except Exception as e:
                    logging.error(f"SMS sending failed: {str(e)}")

                request.session.flush()
                # Show success page with login button instead of direct face verification
                return render(request, 'registration_success.html', {
                    'login_id': unique_login_id,
                    'next_step': 'login'  # This will be used to show proper button
                })

        return render(request, "enter_otp.html", {"error": "Invalid OTP. Please try again."})

    return render(request, "enter_otp.html")


# Login
def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id')
        unique_id = request.POST.get('unique_id')
        phone_number = request.POST.get('phone_number')

        # Check if user has already voted
        existing_vote = votes_collection.find_one({
            "unique_id": unique_id,
            "phone_number": phone_number,
            "status": "completed"
        })

        if existing_vote:
            return render(request, 'already_voted.html')

        user = mongo_collection.find_one({
            "login_id": login_id,
            "unique_id": unique_id,
            "phone_number": phone_number
        })

        if user:
            request.session['user_id'] = str(user['_id'])
            return redirect('face_recognition_page')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')




def face_verification(request):
    if request.headers.get('Sec-Fetch-Mode') == 'navigate' or request.method == 'GET':
        request.session['face_verification_attempts'] = 0
        return JsonResponse({
            "status": "ready",
            "message": "Ready for verification",
            "attempts_remaining": 5
        })
   
    attempt_count = request.session.get('face_verification_attempts', 0)
    if attempt_count >= 5:
        request.session['face_verification_attempts'] = 0
        return JsonResponse({
            "status": "locked",
            "message": "Maximum attempts reached. Page will refresh in 5 seconds.",
            "refresh": True
        })

    temp_filepath = None
    try:
        user_id = request.session.get('user_id')
        user = mongo_collection.find_one({"_id": ObjectId(user_id)})
        stored_features = features_collection.find_one({"filename": user.get('feature_filename')})
        
        if not stored_features or 'feature' not in stored_features:
            return JsonResponse({
                "status": "error",
                "message": "Reference face data not found"
            })

        image_data = request.POST.get('image').split(",")[1]
        image_bytes = BytesIO(base64.b64decode(image_data))
        temp_filepath = os.path.join(settings.MEDIA_ROOT, f'temp_face_{time.time()}.jpg')
       
        with Image.open(image_bytes) as img:
            img.convert("RGB").save(temp_filepath)

        realtime_features = DeepFace.represent(
            img_path=temp_filepath,
            model_name='Facenet',
            enforce_detection=True,
            detector_backend='retinaface'
        )

        realtime_vector = np.array(realtime_features[0]['embedding'])
        stored_vector = np.array(stored_features['feature'][0]['embedding'])
        
        similarity = np.dot(realtime_vector, stored_vector) / (
            np.linalg.norm(realtime_vector) * np.linalg.norm(stored_vector)
        )
        match_percentage = round(similarity * 100, 2)

        request.session['face_verification_attempts'] = attempt_count + 1
        attempts_remaining = 5 - (attempt_count + 1)

        if match_percentage >= 15: ########################### Match percentage adjustable
            request.session['face_verification_attempts'] = 0
            request.session['verified'] = True
            return JsonResponse({
                "status": "success",
                "match_found": True,
                "match_percentage": match_percentage,
                "user_verified": True,
                "redirect_url": "/auth/voting-page/",
                "message": f"Match found! {match_percentage}% match"
            })
       
        return JsonResponse({
            "status": "failed",
            "match_found": False,
            "match_percentage": match_percentage,
            "attempts_remaining": attempts_remaining,
            "message": f"Match {match_percentage}% (need 85%). {attempts_remaining} attempts left"
        })

    except Exception as e:
        logging.error(f"Verification error: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Please ensure your face is clearly visible"
        })

    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)




def face_recognition_page(request):
    return render(request, "face_recognition.html")


#Generate QR Code
# def generate_qr_code(request):
#     session_id = str(uuid.uuid4())
#     request.session['mobile_verification_id'] = session_id
    
#     # Make sure this matches your URL configuration exactly
#     base_url = "https://lovely-llamas-roll.loca.lt"
#     verification_url = f"{base_url}/auth/mobile-verify/?session={session_id}"
    
#     print(f"Generated QR URL: {verification_url}")
    
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(verification_url)
#     qr.make(fit=True)
    
#     img = qr.make_image(fill_color="black", back_color="white")
#     response = HttpResponse(content_type="image/png")
#     img.save(response, "PNG")
#     return response



# Process Mobile Verification
import logging
logger = logging.getLogger(__name__)

def process_mobile_verification(request):
    print("=== Mobile Verification Debug ===")
    print(f"Full URL: {request.build_absolute_uri()}")
    print(f"Path: {request.path}")
    print(f"Method: {request.method}")
    print(f"Headers: {request.headers}")
    print("================================")
    
    if request.method == 'GET':
        return render(request, 'mobile_verification.html')
    
    if request.method == 'POST':
        try:
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({'status': 'error', 'message': 'No image provided'})

            # Save temporary image
            temp_filepath = os.path.join(settings.MEDIA_ROOT, f'mobile_temp_{time.time()}.jpg')
            with open(temp_filepath, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            user_id = request.session.get('user_id')
            user = mongo_collection.find_one({"_id": ObjectId(user_id)})
            stored_features = features_collection.find_one({"filename": user.get('feature_filename')})

            if not stored_features or 'feature' not in stored_features:
                return JsonResponse({
                    "status": "error",
                    "message": "Reference face data not found"
                })

            # Get face embeddings
            realtime_features = DeepFace.represent(
                img_path=temp_filepath,
                model_name='Facenet',
                enforce_detection=True,
                detector_backend='retinaface'
            )

            realtime_vector = np.array(realtime_features[0]['embedding'])
            stored_vector = np.array(stored_features['feature'][0]['embedding'])
            
            similarity = np.dot(realtime_vector, stored_vector) / (
                np.linalg.norm(realtime_vector) * np.linalg.norm(stored_vector)
            )
            match_percentage = round(similarity * 100, 2)

            if match_percentage >= 89:
                request.session['verified'] = True
                return JsonResponse({
                    "status": "success",
                    "match_percentage": match_percentage,
                    "redirect_url": "/auth/voting-page/"
                })
            
            return JsonResponse({
                "status": "error",
                "message": f"Face match {match_percentage}% (need 89%)"
            })

        except Exception as e:
            logging.error(f"Mobile verification error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": "Verification failed. Please try again."
            })
        finally:
            if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                os.remove(temp_filepath)


# Voting Page
def voting_page(request):
    if not request.session.get('verified'):
        return redirect('face_recognition_page')
    
    candidates = [
        {
            'id': 1,
            'name': 'Mr. Anubhav',
            'party': 'Progressive Party',
            'image_url': '/static/images/Mr. Anubhav 🤩.jpg'
        },
        {
            'id': 2,
            'name': 'Mr. Brusly Srajan',
            'party': 'Conservative Party',
            'image_url': '/static/images/Mr. Brusly Srajan 🙂.jpg'
        },
        {
            'id': 3,
            'name': 'Mr. Bullet Renu',
            'party': 'Liberal Party',
            'image_url': '/static/images/Mr. Bullet Renu 💪.jpg'
        },
        {
            'id': 4,
            'name': 'Mrs. Nirmala Seetaraman',
            'party': 'Green Party',
            'image_url': '/static/images/Mrs.Nirmala Seetaraman 💰.jpg'
        }
    ]
    return render(request, 'voting_page.html', {'candidates': candidates})
# Cast Vote
# At the top with other MongoDB connections
votes_collection = mongo_db["votes"]

# def cast_vote(request):
#     if request.method == 'POST':
#         user_id = request.session.get('user_id')
#         candidate_id = request.POST.get('candidate_id')
        
#         if not user_id:
#             return JsonResponse({"status": "error", "message": "Not authenticated"})
            
#         # Get user details
#         user = mongo_collection.find_one({"_id": ObjectId(user_id)})
        
#         # Get candidate details based on ID
#         candidates = {
#             "1": {"name": "Mr. Anubhav 🤩", "party": "Progressive Party"},
#             "2": {"name": "Mr. Brusly Srajan 🙂", "party": "Conservative Party"},
#             "3": {"name": "Mr. Bullet Renu 💪", "party": "Liberal Party"},
#             "4": {"name": "Mrs. Nirmala Seetaraman 💰", "party": "Green Party"}
#         }
        
#         candidate = candidates.get(str(candidate_id))
        
#         # Store vote with detailed information
#         vote_data = {
#             "name": user.get('name'),
#             "unique_id": user.get('unique_id'),
#             "phone_number": user.get('phone_number'),
#             "casted_for": candidate['name'],
#             "party": candidate['party'],
#             "timestamp": datetime.now(),
#             "status": "completed"
#         }
#         votes_collection.insert_one(vote_data)
        
#         # Send privacy-focused SMS confirmation
#         try:
#             client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#             message = "Smart Election Commission: Your vote has been securely recorded. Thank you for participating in strengthening our democracy! 🗳️ #YourVoteMatters"
#             client.messages.create(
#                 body=message,
#                 from_=TWILIO_PHONE_NUMBER,
#                 to=f"+91{user.get('phone_number')}"
#             )
#         except Exception as e:
#             logging.error(f"SMS sending failed: {str(e)}")
        
#         request.session.flush()
#         return JsonResponse({
#             "status": "success",
#             "message": "Your vote has been securely recorded",
#             "candidate_name": candidate['name'],
#             "party": candidate['party']
#         })

from web3 import Web3
import json
from decouple import config
import os

# Initialize Web3 and check connection
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
assert w3.is_connected(), "Blockchain connection failed"

# Get contract path and storage path
current_dir = os.path.dirname(os.path.abspath(__file__))
contract_path = os.path.join(current_dir, '..', '..', 'blockchain', 'build', 'contracts', 'VotingSystem.json')
CONTRACT_STORAGE_FILE = os.path.join(current_dir, 'contract_address.json')

# Load contract data
with open(contract_path) as f:
    contract_data = json.load(f)
    CONTRACT_ABI = contract_data['abi']
    CONTRACT_BYTECODE = contract_data['bytecode']

def initialize_contract():
    # Try to load existing contract
    if os.path.exists(CONTRACT_STORAGE_FILE):
        with open(CONTRACT_STORAGE_FILE) as f:
            stored_data = json.load(f)
            if w3.eth.get_code(stored_data['address']):
                print(f"Using existing contract at: {stored_data['address']}")
                return w3.eth.contract(
                    address=stored_data['address'],
                    abi=CONTRACT_ABI
                )

    # Deploy new contract if needed
    deployer_address = w3.eth.accounts[0]
    w3.eth.default_account = deployer_address

    contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
    transaction = contract.constructor().build_transaction({
        'from': deployer_address,
        'nonce': w3.eth.get_transaction_count(deployer_address),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })

    tx_hash = w3.eth.send_transaction(transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Store new contract address
    with open(CONTRACT_STORAGE_FILE, 'w') as f:
        json.dump({'address': tx_receipt.contractAddress}, f)
    
    print(f"New contract deployed at: {tx_receipt.contractAddress}")
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=CONTRACT_ABI
    )

# Initialize contract instance
contract = initialize_contract()




def cast_vote(request):
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            candidate_id = request.POST.get('candidate_id')
            
            if not user_id:
                return JsonResponse({"status": "error", "message": "Not authenticated"})
            
            active_address = w3.eth.accounts[0]
            user = mongo_collection.find_one({"_id": ObjectId(user_id)})
            voter_id = user.get('unique_id')
            
            # Check MongoDB for existing vote
            existing_vote = votes_collection.find_one({
                "unique_id": user.get('unique_id'),
                "status": "completed"
            })
            
            if existing_vote:
                return JsonResponse({
                    "status": "warning",
                    "title": "🔒 Blockchain Security Alert",
                    "message": "Your vote is already securely recorded and immutably stored on the blockchain.",
                    "details": {
                        "timestamp": existing_vote['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                        "transaction": existing_vote['blockchain_tx_hash'][:10] + "...",
                        "security_status": "Maximum Protection Active"
                    }
                })

            candidates = {
                "1": {"name": "Mr. Anubhav 🤩", "party": "Progressive Party"},
                "2": {"name": "Mr. Brusly Srajan 🙂", "party": "Conservative Party"},
                "3": {"name": "Mr. Bullet Renu 💪", "party": "Liberal Party"},
                "4": {"name": "Mrs. Nirmala Seetaraman 💰", "party": "Green Party"}
            }
            
            candidate = candidates.get(str(candidate_id))
            
            try:
                transaction = contract.functions.castVote(
                    voter_id,
                    int(candidate_id)
                ).build_transaction({
                    'from': active_address,
                    'nonce': w3.eth.get_transaction_count(active_address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': w3.eth.chain_id
                })
                
                tx_hash = w3.eth.send_transaction(transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    vote_data = {
                        "name": user.get('name'),
                        "unique_id": user.get('unique_id'),
                        "phone_number": user.get('phone_number'),
                        "casted_for": candidate['name'],
                        "party": candidate['party'],
                        "timestamp": datetime.now(),
                        "status": "completed",
                        "blockchain_tx_hash": w3.to_hex(tx_hash)
                    }
                    
                    votes_collection.insert_one(vote_data)
                    
                    try:
                        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                        message = f"🗳️ Smart Election Commission: Vote successfully recorded! TX: {w3.to_hex(tx_hash)[:10]}... Thank you for strengthening democracy! #YourVoteMatters"
                        client.messages.create(
                            body=message,
                            from_=TWILIO_PHONE_NUMBER,
                            to=f"+91{user.get('phone_number')}"
                        )
                    except Exception as e:
                        logging.error(f"SMS sending failed: {str(e)}")
                    
                    return JsonResponse({
                        "status": "success",
                        "message": "✅ Vote successfully recorded on blockchain",
                        "candidate_name": candidate['name'],
                        "party": candidate['party'],
                        "tx_hash": w3.to_hex(tx_hash)
                    })
                
            except Exception as e:
                if "You have already voted" in str(e):
                    return JsonResponse({
                        "status": "warning",
                        "title": "🛡️ Vote Protection Active",
                        "message": "Blockchain security has detected and prevented a duplicate voting attempt.",
                        "details": {
                            "protection_type": "Smart Contract Security",
                            "status": "Vote Protected",
                            "integrity": "Maintained"
                        }
                    })
                raise e
                
        except Exception as e:
            logging.error(f"Voting error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": "Vote processing encountered a security check. Please try again.",
                "error_details": str(e)
            })

    return JsonResponse({
        "status": "error",
        "message": "Invalid request method detected"
    })







# Logout
def logout_view(request):
    request.session.flush()
    return redirect('home_page')

def send_verification_link(request):
    data = json.loads(request.body)
    target = data.get('target')
    session_id = str(uuid.uuid4())
    
    # Use your server's IP address
    base_url = "http://192.168.56.1"  # Replace X with your actual local IP
    verification_url = f"{base_url}:8000/auth/mobile-verify/?session={session_id}"
    
    if target == 'developer':
        phone_number = "7259344361"
    else:
        user_id = request.session.get('user_id')
        user = mongo_collection.find_one({"_id": ObjectId(user_id)})
        phone_number = user.get('phone_number')
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=f"Click here to complete face verification: {verification_url}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{phone_number}"
        )
        return JsonResponse({
            "status": "success",
            "message": f"Verification link sent to {'developer' if target == 'developer' else 'your number'}"
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })

def contact_developer(request):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body="User requested assistance with face verification",
            from_=TWILIO_PHONE_NUMBER,
            to="+917259344361"
        )
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
def election_results(request):
    # Get all votes from MongoDB
    all_votes = votes_collection.find({})
    
    vote_counts = {
        "Mr. Anubhav": 0,
        "Mr. Brusly Srajan": 0,
        "Mr. Bullet Renu": 0,
        "Mrs. Nirmala Seetaraman": 0
    }
    
    # Count votes
    total_votes = 0
    for vote in all_votes:
        candidate = vote['casted_for']
        if candidate in vote_counts:
            vote_counts[candidate] += 1
            total_votes += 1
    
    # Prepare results data
    candidates_data = []
    for name, votes in vote_counts.items():
        party_map = {
            "Mr. Anubhav": "Progressive Party",
            "Mr. Brusly Srajan": "Conservative Party",
            "Mr. Bullet Renu": "Liberal Party",
            "Mrs. Nirmala Seetaraman": "Green Party"
        }
        
        candidates_data.append({
            "name": name,
            "party": party_map[name],
            "image": f"/static/images/{name}.jpg",
            "votes": votes,
            "percentage": round((votes / total_votes * 100), 2) if total_votes > 0 else 0
        })
    
    candidates_data.sort(key=lambda x: x['votes'], reverse=True)
    winner = candidates_data[0] if candidates_data and candidates_data[0]['votes'] > 0 else None

    return render(request, 'election_results.html', {
        'results': candidates_data,
        'winner': winner,
        'total_votes': total_votes
    })

    
#####3 Result page ###########

def protected_results(request):
    # Initialize vote counts with all candidates
    vote_counts = {
        "Mr. Anubhav 🤩": {
            "name": "Mr. Anubhav 🤩",
            "party": "Progressive Party",
            "image": "/static/images/Mr. Anubhav 🤩.jpg",
            "votes": 0
        },
        "Mr. Brusly Srajan 🙂": {
            "name": "Mr. Brusly Srajan 🙂",
            "party": "Conservative Party",
            "image": "/static/images/Mr. Brusly Srajan 🙂.jpg",
            "votes": 0
        },
        "Mr. Bullet Renu 💪": {
            "name": "Mr. Bullet Renu 💪",
            "party": "Liberal Party",
            "image": "/static/images/Mr. Bullet Renu 💪.jpg",
            "votes": 0
        },
        "Mrs. Nirmala Seetaraman 💰": {
            "name": "Mrs. Nirmala Seetaraman 💰",
            "party": "Green Party",
            "image": "/static/images/Mrs.Nirmala Seetaraman 💰.jpg",
            "votes": 0
        }
    }

    # Fetch all completed votes from MongoDB
    all_votes = list(votes_collection.find({"status": "completed"}))
    total_votes = len(all_votes)

    # Count votes for each candidate
    for vote in all_votes:
        candidate = vote.get('casted_for')
        # Handle emoji variations in candidate names
        candidate_normalized = next(
            (k for k in vote_counts.keys() if k.split()[0:2] == candidate.split()[0:2]), 
            candidate
        )
        if candidate_normalized in vote_counts:
            vote_counts[candidate_normalized]['votes'] += 1

    # Prepare candidates data with percentages
    candidates_data = []
    for data in vote_counts.values():
        candidates_data.append({
            "name": data["name"],
            "party": data["party"],
            "image": data["image"],
            "votes": data["votes"],
            "percentage": round((data["votes"] / total_votes * 100), 2) if total_votes > 0 else 0
        })

    # Sort by votes in descending order
    candidates_data.sort(key=lambda x: x['votes'], reverse=True)

    # Handle tied results
    if len(candidates_data) >= 2 and candidates_data[0]['votes'] == candidates_data[1]['votes']:
        tied_candidates = [c for c in candidates_data if c['votes'] == candidates_data[0]['votes']]
        winner = {
            'name': 'Tie between ' + ' and '.join([c['name'] for c in tied_candidates]),
            'party': 'Multiple Parties',
            'votes': tied_candidates[0]['votes'],
            'percentage': tied_candidates[0]['percentage']
        }
    else:
        winner = candidates_data[0] if candidates_data and candidates_data[0]['votes'] > 0 else None

    return render(request, 'election_results.html', {
        'results': candidates_data,
        'winner': winner,
        'total_votes': total_votes,
        'is_tie': winner and 'Tie between' in winner['name']
    })

