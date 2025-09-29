from flask import session, render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from flask_login import current_user
from models import User, Generation, Payment
from openai_service import generate_social_media_content
import stripe
import os
import json
from datetime import date, datetime, timedelta

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Domain configuration for redirects
YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') != '' else os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page for logged out users, dashboard for logged in users"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """User dashboard with content generation form"""
    user = current_user
    
    # Check subscription status
    check_subscription_status(user)
    
    # Reset daily generation count if it's a new day
    today = date.today()
    if user.last_generation_date != today:
        user.generations_today = 0
        user.last_generation_date = today
        db.session.commit()
    
    # Get user's recent generations
    recent_generations = Generation.query.filter_by(user_id=user.id).order_by(Generation.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', user=user, recent_generations=recent_generations)

def check_subscription_status(user):
    """Check if user's subscription is still valid"""
    if user.subscription_status == 'paid' and user.subscription_end_date:
        if datetime.now() > user.subscription_end_date:
            user.subscription_status = 'free'
            user.subscription_end_date = None
            db.session.commit()
    return user.subscription_status

@app.route('/generate', methods=['POST'])
@require_login
def generate_content():
    """Generate social media content using OpenAI"""
    user = current_user
    
    # Check subscription status
    current_status = check_subscription_status(user)
    
    # Check usage limits
    today = date.today()
    if user.last_generation_date != today:
        user.generations_today = 0
        user.last_generation_date = today
        db.session.commit()
    
    # Check if user can generate content
    if current_status == 'free' and user.generations_today >= 1:
        return jsonify({
            'error': 'Daily generation limit reached. Upgrade to paid plan for unlimited generations.'
        }), 429
    
    try:
        data = request.get_json()
        niche = data.get('niche', '').strip()
        topic = data.get('topic', '').strip()
        tone = data.get('tone', '').strip()
        
        if not all([niche, topic, tone]):
            return jsonify({'error': 'Please fill in all fields'}), 400
        
        # Generate content using OpenAI
        content = generate_social_media_content(niche, topic, tone)
        
        # Save generation to database
        generation = Generation(
            user_id=user.id,
            niche=niche,
            topic=topic,
            tone=tone,
            posts=json.dumps(content['posts']),
            hashtags=json.dumps(content['hashtags']),
            schedule=json.dumps(content['schedule'])
        )
        db.session.add(generation)
        
        # Update usage count
        user.generations_today += 1
        db.session.commit()
        
        return jsonify(content)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate content: {str(e)}'}), 500

@app.route('/create-checkout-session', methods=['POST'])
@require_login
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        # Create customer if doesn't exist
        user = current_user
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': user.id}
            )
            user.stripe_customer_id = customer.id
            db.session.commit()
        
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'AI Post Genie Pro',
                            'description': 'Unlimited social media content generation'
                        },
                        'unit_amount': 900,  # $9.00 in cents
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=f'https://{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'https://{YOUR_DOMAIN}/dashboard',
            automatic_tax={'enabled': False},
        )
        
        if checkout_session.url:
            return redirect(checkout_session.url, code=303)
        else:
            flash('Error creating checkout session', 'error')
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error creating checkout session: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/success')
@require_login
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                user = current_user
                user.subscription_status = 'paid'
                
                # Get subscription details
                if hasattr(session, 'subscription') and session.subscription:
                    try:
                        subscription = stripe.Subscription.retrieve(str(session.subscription))
                        user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
                    except:
                        # Fallback: Set subscription end date to 30 days from now
                        user.subscription_end_date = datetime.now() + timedelta(days=30)
                else:
                    # Set subscription end date to 30 days from now for one-time payments
                    user.subscription_end_date = datetime.now() + timedelta(days=30)
                
                db.session.commit()
                flash('Subscription activated successfully! You now have unlimited generations.', 'success')
            else:
                flash('Payment verification failed. Please contact support.', 'error')
        except Exception as e:
            flash(f'Error verifying payment: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # For now, we'll just handle the event without signature verification
        # In production, you should verify the webhook signature
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
        
        if event['type'] == 'invoice.payment_succeeded':
            # Handle successful subscription payment
            invoice = event['data']['object']
            customer_id = invoice['customer']
            
            # Find user by Stripe customer ID
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.subscription_status = 'paid'
                
                # Get the subscription to set proper end date
                if invoice.get('subscription'):
                    try:
                        subscription = stripe.Subscription.retrieve(invoice['subscription'])
                        user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
                    except Exception as e:
                        # Fallback: Set subscription end date to 30 days from now
                        user.subscription_end_date = datetime.now() + timedelta(days=30)
                        print(f"Error retrieving subscription: {e}")
                else:
                    # For one-time payments, set 30 days from now
                    user.subscription_end_date = datetime.now() + timedelta(days=30)
                
                db.session.commit()
        
        elif event['type'] == 'invoice.payment_failed':
            # Handle failed payment
            subscription = event['data']['object']
            customer_id = subscription['customer']
            
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.subscription_status = 'free'
                user.subscription_end_date = None
                db.session.commit()
        
        elif event['type'] == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription = event['data']['object']
            customer_id = subscription['customer']
            
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.subscription_status = 'free'
                user.subscription_end_date = None
                db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/api/user-status')
@require_login
def user_status():
    """API endpoint to get user status"""
    user = current_user
    today = date.today()
    
    # Reset daily count if new day
    if user.last_generation_date != today:
        user.generations_today = 0
        user.last_generation_date = today
        db.session.commit()
    
    return jsonify({
        'subscription_status': user.subscription_status,
        'generations_today': user.generations_today,
        'can_generate': user.subscription_status == 'paid' or user.generations_today < 1
    })