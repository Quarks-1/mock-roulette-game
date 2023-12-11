from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from roulette.models import Bet, Profile
import json, random

class MyConsumer(WebsocketConsumer):
    group_name = 'roulette_group'
    channel_name = 'roulette_channel'
    
    user = None

    def connect(self):
        
        personal_group_name = self.scope["user"].username + str(self.scope["user"].id)
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, 
            self.channel_name
        )
        async_to_sync(self.channel_layer.group_add)(
            personal_group_name, 
            self.channel_name
        )
        # print(personal_group_name)
        self.accept()

        if not self.scope["user"].is_authenticated:
            self.send_error(f'You must be logged in')
            self.close()
            return
        # Commented out for internal testing -- Re-enable for production
        # if not self.scope["user"].email.endswith("@andrew.cmu.edu"):
        #     self.send_error(f'You must be logged with Andrew identity')
        #     self.close()
        #     return            

        self.user = self.scope["user"]
        profile = Profile.objects.get(user=self.user)
        profile.joined_game = True
        profile.ready = False
        profile.personal_group_name = personal_group_name
        profile.prevbet = 0
        profile.prevwin = 0
        profile.save()
        # print(profile.personal_group_name, 'h1')
        self.broadcast_user()
        self.broadcast_bets()
        self.broadcast_balance(False)

    def disconnect(self, close_code):
        profile = Profile.objects.get(user=self.user) 
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, 
            self.channel_name
        )
        async_to_sync(self.channel_layer.group_discard)(
            profile.personal_group_name, 
            self.channel_name
        )
        profile.joined_game = False
        profile.ready = False
        profile.personal_group_name = ""
        profile.save()
        self.broadcast_user()
        self.check_ready()
    
    def receive(self, **kwargs):
        data = json.loads(kwargs['text_data'])
        action = data['action']
        if action == 'place_bet':
            self.place_bet(data)
            return
        
    def place_bet(self, data):
        bets = data['bets']
        totalBet = data['totalBet']
        profile = Profile.objects.get(user=self.user)
        if totalBet > profile.balance:
            # self.send_error(f'You do not have enough money to place that bet')
            self.broadcast_error(f'You do not have enough money to place that bet')
            return
        elif profile.ready:
            # self.send_error(f'You have already placed a bet')
            self.broadcast_error(f'You have already placed a bet')
            return
        # Add bets to DB.  Make new if doesn't exist, otherwise update amount
        for number, bet_amount in bets.items():
            bet, created = Bet.objects.get_or_create(
                value=number, 
                user=profile.user, 
                defaults={'amount': bet_amount, 'name': profile.fname}
            )
            if not created:
                bet.amount += bet_amount
                bet.save()
            print("Saving Bet: " + str(number) + " = $" + str(bet.amount))
        profile.balance -= totalBet
        # print(f'totalbet: {totalBet}')
        profile.prevbet = totalBet
        profile.ready = True
        profile.save()
        self.broadcast_bets()
        self.broadcast_user()
        self.broadcast_balance(False)
        self.broadcast_error('Bet placed successfully! Waiting for other players to bet...')
        # Spin wheel if everyone is ready
        self.check_ready()
    
    def check_ready(self):
        for profile in Profile.objects.all():
            # Only start game once all joined users are ready
            if profile.joined_game and not profile.ready:
                return
        # All profiles are ready, so spin the wheel
        spin_value = random.randint(0, 36)
        # Can hardcode spin value for testing here
        print(f'Spin value: {spin_value}')
        self.broadcast_spin(spin_value)
        # Check bets and update balances
        self.check_bets(spin_value)
        
    def check_bets(self, spin_value):
        totalBet = 0
        for profile in Profile.objects.all():
            profile.prevwin = 0
            profile.save()
        for bet in Bet.objects.all():
            profile = Profile.objects.get(user=bet.user)
            won = False
            won_amt = 0
            # Base win
            if bet.value.isdigit() and int(bet.value) == spin_value:
                profile.balance += bet.amount * 35 + bet.amount
                profile.prevwin += bet.amount * 35 + bet.amount
                won = True
                won_amt = bet.amount * 35 + bet.amount
            # 12s win
            elif (bet.value == '1st 12' and spin_value <= 12 and spin_value != 0) or (bet.value == '2nd 12' and spin_value > 12 and spin_value <= 24) or (bet.value == '3rd 12' and spin_value > 24):
                profile.balance += bet.amount * 2 + bet.amount
                profile.prevwin += bet.amount * 2 + bet.amount
                won = True
                won_amt = bet.amount * 2 + bet.amount
            # halves win
            elif (bet.value == '1 to 18' and spin_value <= 18 and spin_value != 0) or (bet.value == '19 to 36' and spin_value > 18):
                profile.balance += bet.amount + bet.amount
                profile.prevwin += bet.amount + bet.amount
                won = True
                won_amt = bet.amount + bet.amount
            # even/odd win
            elif (bet.value == 'Even' and spin_value % 2 == 0 and spin_value != 0) or (bet.value == 'Odd' and spin_value % 2 == 1):
                profile.balance += bet.amount + bet.amount
                profile.prevwin += bet.amount + bet.amount
                won = True
                won_amt = bet.amount + bet.amount
            # color win
            elif (bet.value == 'Black' and spin_value in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]) or (bet.value == 'Red' and spin_value in [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 29, 31, 33, 35]):
                profile.balance += bet.amount + bet.amount
                profile.prevwin += bet.amount + bet.amount
                won = True
                won_amt = bet.amount + bet.amount
            # 2 to 1 wins
            elif (bet.value == '2 to 1 (3)' and spin_value % 3 == 1) or (bet.value == '2 to 1 (2)' and spin_value % 3 == 2) or (bet.value == '2 to 1 (1)' and spin_value % 3 == 0  and spin_value != 0):
                profile.balance += bet.amount * 2 + bet.amount
                profile.prevwin += bet.amount * 2 + bet.amount
                won = True
                won_amt = bet.amount * 2 + bet.amount
            # Clear all bets regardless of win
            # Add to total bet if current user made bet
            totalBet += bet.amount
            profile.prevbet = totalBet
            # Shift all win messages down
            if won:
                profile.win3 = profile.win2
                profile.win2 = profile.win1
                profile.win1 = f'{bet.name} won ${won_amt - bet.amount} on {bet.value}!'
            profile.save()
            bet.delete()
        # Update prevwin and reaady state for all users
        for profile in Profile.objects.all():
            profile.prevwin -= profile.prevbet
            profile.ready = False
            profile.save()
        self.broadcast_bets()   # Update bet list
        self.broadcast_user()   # Update ready status
        self.broadcast_balance(True)  # Update balance
        self.broadcast_win(str(spin_value))  # Update winning number
        
    # Can be used later to show number on wheel
    def broadcast_spin(self, spin):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'spin', 'spin': spin})
            }
        )
    
    # Send balance to display on user's screen
    def broadcast_balance(self,showwin):
        for profile in Profile.objects.all():
            if profile.joined_game == False:
                continue
            # print(f'pgroupname: {profile.personal_group_name}')
            totalBet = profile.prevbet
            winnings = profile.prevwin
            async_to_sync(self.channel_layer.group_send)(
                profile.personal_group_name,
                {
                    'type': 'broadcast_event',
                    'message': json.dumps({'type': 'balance', 'totalBet' : totalBet, 'balance': profile.balance ,'winnings': winnings, 'showWin': showwin})
                }
            )
        
    # Send all current bets to display on board
    def broadcast_bets(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'bet_list', 'bets': Bet.make_bet_list()})
            }
        )
    # Send currently joined users to update list
    def broadcast_user(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'joined_list', 'joined' : Profile.make_joined_list()})
            }
        )
    
    # Broadcast winning number
    def broadcast_win(self, win):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'winning_number', 'winning_number' : win})
            }
        )

    # Broadcast error message
    def broadcast_error(self, error):
        profile = Profile.objects.get(user=self.user)
        async_to_sync(self.channel_layer.group_send)(
            profile.personal_group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'error', 'error' : error})
            }
        )

    def broadcast_event(self, event):
        self.send(text_data=event['message'])
        
    def send_error(self, error_message):
        self.send(text_data=json.dumps({'error': error_message}))

    