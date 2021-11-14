
from django.contrib import admin
from app.models import *

# Register your models here.
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'portfolio', 'currency', 'balance', 'hold', 'available', 'last_balance', 'percent_chng', 'can_trade')

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('balance_usd', 'balance_btc', 'currency3', 'balance3')

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('trade_status', 'potential_trade', 'trade_btc', 'trade_usd')

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'acc_type', 'passphrase', 'api_key', 'api_secret', 'created_at', 'updated_at')

@admin.register(BotConfiguration)
class BotConfiguration(admin.ModelAdmin):
    list_display = ('name', 'portfolio', 'symbol', 'is_active', 'timeframe', 'price_var', 'last_action', 'created_at', 'updated_at')
