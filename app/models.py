
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Account(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    portfolio = models.ForeignKey("Portfolio", null=True, blank=True, on_delete=models.CASCADE)
    currency = models.CharField(max_length=100, null=True)
    balance = models.CharField(max_length=100, null=True)
    hold = models.CharField(max_length=100, null=True)
    available = models.CharField(max_length=100, null=True)
    last_balance = models.CharField(max_length=100, null=True)
    percent_chng = models.CharField(max_length=100, null=True)
    can_trade = models.BooleanField(default=False, null=True)

    def __id__(self):
        return self.id


class Balance(models.Model):
    balance_usd = models.CharField(max_length=100, null=True)
    balance_btc = models.CharField(max_length=100, null=True)
    currency3 = models.CharField(max_length=100, null=True)
    balance3 = models.CharField(max_length=100, null=True)


class Setting(models.Model):
    trade_status = models.BooleanField(default=True, null=True)
    potential_trade = models.BooleanField(default=False, null=True)
    trade_btc = models.BooleanField(default=False, null=True)
    trade_usd = models.BooleanField(default=False, null=True)


class Portfolio(models.Model):
    ACC_TYPES = (
        ('LIVE', 'LIVE'),
        ('DEMO', 'DEMO')
    )
    name = models.CharField(max_length=512, null=True, blank=True, verbose_name='Name')
    acc_type = models.CharField(max_length=512, default="LIVE", verbose_name='acc_type', choices=ACC_TYPES)
    passphrase = models.CharField(max_length=512, null=True, blank=True, verbose_name='PassPhrase')
    api_key = models.CharField(max_length=512, null=True, blank=True, verbose_name='API_KEY')
    api_secret = models.CharField(max_length=512, null=True, blank=True, verbose_name='API_SECRET')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Updated At')


class BotConfiguration(models.Model):
    name = models.CharField(max_length=512, null=True, blank=True, verbose_name='Name')
    portfolio = models.ForeignKey(Portfolio, null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False, verbose_name='Active')
    symbol = models.CharField(max_length=512, null=True, blank=True, verbose_name='Symbol')
    timeframe = models.CharField(max_length=512, null=True, blank=True, verbose_name='Timeframe')
    price_var = models.FloatField(null=True, blank=True, verbose_name="PriceVar")
    last_action = models.CharField(max_length=512, default="NAN", verbose_name='LastAction')
    last_price = models.FloatField(default=-1, verbose_name="PriceVar")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Updated At')
