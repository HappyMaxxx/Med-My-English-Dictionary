from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def subscriptions(request):
    """
    Renders the subscriptions page displaying Free, Standard, and Pro plans.
    """
    user_subscription = None
    if request.user.is_authenticated:
        # Assuming a UserProfile or Subscription model exists
        user_subscription = getattr(request.user, 'subscription_plan', None)  # Example: 'free', 'standard', 'pro'

    context = {
        'user_subscription': user_subscription,
    }
    return render(request, 'premium/subscriptions.html', context)

@login_required
def subscribe(request, plan):
    """
    Handles subscription selection for Standard or Pro plans.
    """
    valid_plans = ['standard', 'pro']
    if plan.lower() not in valid_plans:
        messages.error(request, "Invalid subscription plan selected.")
        return redirect('subscriptions')

    # Placeholder: Logic to process subscription (e.g., integrate with payment gateway)
    messages.success(request, f"You have selected the {plan.capitalize()} plan! (Processing not implemented.)")
    return redirect('subscriptions')

def faq(request):
    """
    Renders the FAQ page with common questions about Med.
    """
    return render(request, 'premium/faq.html', {})