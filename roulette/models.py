from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from jsonfield import JSONField

class Transactions(models.Model):
    class TypeOfTransaction(models.TextChoices):
        DEPOSIT = "DP", ("Deposit")
        WITHDRAW = "WD", ("Withdraw")
        WAGER = "WG", ("Wager")
        WINNINGS = "WN", ("Winnings")
        LOSSES = "LS", ("Losses")
        UNDEFINED = "UD", ("Undefined") #for catching errors with not setting txn type
    
    class TransactionStatus(models.TextChoices):
        INITIATED = "IN", ("Initiated")
        PENDING = "PD", ("Pending")
        COMPLETED = "CP", ("Completed")
        FAILED = "FL", ("Failed")
        ERROR = "ER", ("Error")
        UNDEFINED = "UD", ("Undefined") #for catching errors with not setting txn status
    
    
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    amount = models.IntegerField(default=0)
    type_of_transaction = models.CharField(
        max_length=2,
        choices=TypeOfTransaction.choices,
        default=TypeOfTransaction.UNDEFINED,
    )
    
    status = models.CharField(
        max_length=2,
        choices=TransactionStatus.choices,
        default=TransactionStatus.UNDEFINED,
    )
    
class Achievements(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    won = models.IntegerField(default=0)
    total_bet = models.PositiveIntegerField(default=0)
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    balance = models.PositiveIntegerField(default=0)     # only want user to have a nonzero balance
    join_date = models.DateTimeField()
    joined_game = models.BooleanField(default=False)
    picture = models.FileField(blank=True)
    fname = models.CharField(max_length=100, blank=True)
    ready = models.BooleanField(default=False)
    prevwin = models.IntegerField(default=0)
    prevbet = models.IntegerField(default=0)
    showwin = models.BooleanField(default=False)
    personal_group_name = models.CharField(max_length=100, blank=True)
    win1 = models.CharField(max_length=100, blank=True, default='Not enough wins yet!')
    win2 = models.CharField(max_length=100, blank=True, default='Not enough wins yet!')
    win3 = models.CharField(max_length=100, blank=True, default='Not enough wins yet!')
    # Print profile fields
    def __str__(self):
        return f'{self.user.username} Profile - Balance: {self.balance} Ready: {self.ready} Prevwin: {self.prevwin} Prevbet: {self.prevbet} Showwin: {self.showwin} Personal Group Name: {self.personal_group_name}'
    
    @classmethod
    def make_joined_list(cls):
        joined_list = []
        for profile in cls.objects.all():
            if profile.joined_game:
                profile_dict = {
                    'fname' : profile.fname,
                    'picture' : profile.picture.url[1:].replace('%3A', ':/'),
                    'ready' : profile.ready,
                    'balance' : profile.balance,
                    'prevwin' : profile.prevwin,
                    'prevbet' : profile.prevbet,
                    'showwin' : profile.showwin,
                    'id' : profile.user.id,
                    'personal_group_name' : profile.personal_group_name,
                }
                joined_list.append(profile_dict)
        return joined_list
    
# Make new user when new google login is made
@receiver(user_logged_in)
def create_profile(sender, user, request, **kwargs):
    if not Profile.objects.filter(user=user).exists():
        pic = request.user.social_auth.get(provider='google-oauth2').extra_data['picture']
        Profile.objects.get_or_create(user=user, balance=0, join_date=timezone.now(), picture=pic, fname=user.first_name)
    if 'picture' not in request.session:
        request.session['picture'] = request.user.social_auth.get(provider='google-oauth2').extra_data['picture']
    
    

class Bet(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, blank=True)
    amount = models.IntegerField()
    value = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bet: {self.name} bet {self.amount} on {self.value}"
    
    @classmethod
    def make_bet_list(cls):
        bet_list = []
        for bet in cls.objects.all():
            bet_dict = {
                'user_id' : bet.user.id,
                'name' : bet.name,
                'amount': bet.amount,
                'value': bet.value,
            }
            bet_list.append(bet_dict)
        return bet_list