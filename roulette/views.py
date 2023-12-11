from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from webapps.settings import ROULETTE_USERS, ROULETTE_TITLE
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from roulette.models import Bet, Profile
import json
import stripe

def home_page(request):
    return render(request, 'roulette/home.html', {})


@login_required
def game_page(request):
    if request.method == 'GET':
        user = Profile.objects.get(user=request.user)
        user.joined_game = True
        user.save()
        context = {
            "balance": user.balance,
            "status": "Place your bets!",
            "profile_picture": request.user.social_auth.get(provider='google-oauth2').extra_data['picture'].rstrip("=s96-c")
        }
        return render(request, 'roulette/game_page.html', context)

@login_required
def place_bet(request):
    response_msg = ""
    reponse_code = -1
    if request.method == 'POST':
        data = json.loads(request.body)
        total_bet_amount = data.get('totalBetAmount')
        user_profile = Profile.objects.get(user=request.user)

        if total_bet_amount > user_profile.balance:
            return JsonResponse({'status': 'error', 'message': 'Insufficient balance'}, status=400)

        bet = data.get('currentBet')
        print(bet)
        for number, bet_amount in bet.items():
            print("Saving Bet: " + str(number) + " = $" + str(bet_amount))
            bet = Bet(value=number, amount=bet_amount, user=request.user, name=request.user.first_name)
            bet.save()

        # Deduct the bet amount from the user's balance
        user_profile.balance -= total_bet_amount
        user_profile.save()
        response_msg = "$" + str(total_bet_amount) + \
            " bet placed successfully."
        reponse_code = 201
    else:
        response_msg = "Invalid Request"
        reponse_code = 405
    return JsonResponse({'status': response_msg}, status=reponse_code)



@login_required
def pre_game_page(request):
    if request.method == 'GET':
        profile = Profile.objects.get(user=request.user)
        profile.joined_game = False
        profile.save()
        context = {
            'profile_picture': request.user.social_auth.get(provider='google-oauth2').extra_data['picture'].rstrip("=s96-c")
        }
        return render(request, 'roulette/pre_game.html', context)


@login_required
def profile(request):
    if request.method == 'GET':
        profile = Profile.objects.get(user=request.user)
        profile.joined_game = False
        profile.save()
        context = {
            'bet1': profile.win1,
            'bet2': profile.win2,
            'bet3': profile.win3,
            'profile_picture': request.user.social_auth.get(provider='google-oauth2').extra_data['picture'].rstrip("=s96-c")
        }
        return render(request, 'roulette/profile.html', context)


def calculate_order_amount(items):
    return 1400


@login_required
def create_payment(request):
    try:
        print(request.POST)
        intent = stripe.PaymentIntent.create(
            amount=calculate_order_amount(request.POST['items']),
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        response_json = '{"clientSecret": "' + intent['client_secret'] + '"}'
        return HttpResponse(response_json, content_type='application/json', status=200)
    except Exception as e:
        response_json = '{"error": "' + e + '"}'


@login_required
def add_balance(request):
    profile = request.user.profile
    if profile == None:
        return HttpResponse('{"error": "no profile"}', content_type='application/json', status=403)
    if profile.joined_game:
        data = json.loads(request.body)
        profile.balance += float(data['deposit-amount'])
        profile.save()
        response_msg = "Successfully added " +  str(data['deposit-amount']) + " to wallet"
        res = {"msg": response_msg}
        return HttpResponse(json.dumps(res), content_type='application/json', status=200)
    else:
        if float(request.POST['deposit-amount']) < 0:
            return redirect('profile')
        profile.balance += float(request.POST['deposit-amount'])
        profile.save()
        return redirect('profile')


@login_required
def subtract_balance(request):
    if request.method == 'POST':
        withdraw_amount = float(request.POST.get('withdraw-amount'))
        if withdraw_amount > request.user.profile.balance or withdraw_amount < 0:
            return redirect('profile')
        request.user.profile.balance -= withdraw_amount
        request.user.profile.save()
        return redirect('profile')
    else:
        return redirect('profile')

