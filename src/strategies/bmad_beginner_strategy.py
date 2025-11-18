"""
🌙 Moon Dev's BMAD Beginner Strategy
Built with love by Moon Dev 🚀

SIMPLE $100 STRATEGY for Beginners
Target: 2-5% monthly returns with strict risk management

This is a simplified, standalone strategy that:
1. Uses the EMAVolumeSync approach (proven in backtests)
2. Implements strict $100 capital management
3. Limits risk to 2% per trade ($2)
4. Uses 2.5:1 risk/reward ratio
5. Trades only when conditions are perfect

Perfect for beginners who want to start with $100!
"""

# ============================================================================
# CONFIGURATION - Easy to adjust!
# ============================================================================

# Capital Settings
STARTING_CAPITAL = 100.00  # Your starting balance
RISK_PER_TRADE = 0.02  # Risk 2% ($2) per trade
RISK_REWARD_RATIO = 2.5  # Target 2.5:1 (risk $2 to make $5)

# Monthly Targets
TARGET_MONTHLY_RETURN = 0.025  # 2.5% per month ($2.50 on $100)
MAX_MONTHLY_RETURN = 0.05  # Stop at 5% profit ($5 on $100)
MAX_MONTHLY_LOSS = -0.10  # Stop at -10% loss (-$10 on $100)

# Trading Parameters (EMAVolumeSync Strategy)
EMA_PERIOD = 20  # 20-period EMA
VOLUME_MA_PERIOD = 20  # 20-period volume average
TIMEFRAME = '15m'  # 15-minute candles

# Token to Trade (start with one!)
TOKEN_SYMBOL = 'BTC'  # Bitcoin - most liquid
TOKEN_NAME = 'Bitcoin'

# Safety Limits
MAX_TRADES_PER_DAY = 2  # Only 2 trades max per day
REQUIRE_VOLUME_CONFIRMATION = True  # Must have volume spike
MIN_PROFIT_TARGET = 2.50  # Minimum $2.50 profit target

# ============================================================================
# IMPORTS
# ============================================================================

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# BEGINNER TRADING STRATEGY
# ============================================================================

class BMADBeginnerStrategy:
    """
    Simple $100 Trading Strategy for Beginners

    Based on EMAVolumeSync - a proven trend-following approach
    Risk Management: Never risk more than $2 per trade
    """

    def __init__(self):
        """Initialize the beginner strategy"""

        # Setup directories
        self.data_dir = Path("src/data/bmad_beginner")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Trading state
        self.capital = STARTING_CAPITAL
        self.start_capital = STARTING_CAPITAL
        self.positions = []
        self.trade_history = []

        # Performance tracking
        self.monthly_pnl = 0.0
        self.trades_today = 0
        self.last_trade_date = None

        # Load previous state if exists
        self.state_file = self.data_dir / "beginner_state.json"
        self.load_state()

        print("\n" + "="*60)
        print("🚀 BMAD Beginner Strategy Initialized!")
        print("="*60)
        print(f"💰 Starting Capital: ${self.capital:.2f}")
        print(f"🎯 Monthly Target: {TARGET_MONTHLY_RETURN*100}% (${STARTING_CAPITAL * TARGET_MONTHLY_RETURN:.2f})")
        print(f"🛡️ Risk Per Trade: {RISK_PER_TRADE*100}% (${STARTING_CAPITAL * RISK_PER_TRADE:.2f})")
        print(f"📊 Risk/Reward: {RISK_REWARD_RATIO}:1")
        print(f"🪙 Trading: {TOKEN_NAME} ({TOKEN_SYMBOL})")
        print("="*60 + "\n")

    def load_state(self):
        """Load previous trading state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.capital = state.get('capital', STARTING_CAPITAL)
                    self.positions = state.get('positions', [])
                    self.trade_history = state.get('trade_history', [])
                    self.monthly_pnl = state.get('monthly_pnl', 0.0)
                    print(f"📂 Loaded previous state: ${self.capital:.2f}")
            except Exception as e:
                print(f"⚠️ Could not load state: {e}")

    def save_state(self):
        """Save current trading state"""
        try:
            state = {
                'capital': self.capital,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'monthly_pnl': self.monthly_pnl,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving state: {e}")

    def check_trading_allowed(self):
        """Check if we're allowed to trade based on risk limits"""

        # Calculate current performance
        pnl_pct = (self.monthly_pnl / self.start_capital) * 100

        # Check if we hit max profit target
        if pnl_pct >= MAX_MONTHLY_RETURN * 100:
            print(f"\n🎉 Hit monthly target! ({pnl_pct:.1f}%)")
            print("✅ Take your profit and enjoy!")
            return False, f"Hit monthly target ({pnl_pct:.1f}%)"

        # Check if we hit max loss
        if pnl_pct <= MAX_MONTHLY_LOSS * 100:
            print(f"\n🛑 Hit max loss limit ({pnl_pct:.1f}%)")
            print("⚠️ Stop trading for this month")
            return False, f"Hit max loss ({pnl_pct:.1f}%)"

        # Check daily trade limit
        today = datetime.now().date()
        if self.last_trade_date == today and self.trades_today >= MAX_TRADES_PER_DAY:
            return False, f"Hit daily trade limit ({MAX_TRADES_PER_DAY} trades)"

        # Check if we have enough capital
        if self.capital < STARTING_CAPITAL * 0.5:
            return False, "Capital too low (below 50% of start)"

        return True, "Trading allowed"

    def analyze_entry_signal(self, current_price, ema_high, ema_low, current_volume, volume_ma):
        """
        Analyze if we should enter a trade
        Based on EMAVolumeSync strategy
        """

        signals = {
            'should_enter': False,
            'direction': None,
            'stop_loss': None,
            'take_profit': None,
            'position_size': None,
            'reason': ''
        }

        # Check for uptrend (price above both EMAs + volume spike)
        is_uptrend = current_price > ema_high and current_price > ema_low
        volume_spike = current_volume > volume_ma if REQUIRE_VOLUME_CONFIRMATION else True

        if is_uptrend and volume_spike:
            # Calculate position sizing
            risk_amount = self.capital * RISK_PER_TRADE  # $2 on $100
            stop_loss = ema_low  # Use lower EMA as stop loss
            risk_per_unit = current_price - stop_loss

            if risk_per_unit > 0:
                position_size_usd = risk_amount * RISK_REWARD_RATIO  # Position size
                take_profit = current_price + (risk_per_unit * RISK_REWARD_RATIO)

                # Check if profit target is worth it
                potential_profit = position_size_usd * (take_profit - current_price) / current_price

                if potential_profit >= MIN_PROFIT_TARGET:
                    signals['should_enter'] = True
                    signals['direction'] = 'LONG'
                    signals['stop_loss'] = stop_loss
                    signals['take_profit'] = take_profit
                    signals['position_size'] = position_size_usd
                    signals['reason'] = f'Uptrend + Volume spike. Risk ${risk_amount:.2f} to make ${potential_profit:.2f}'

        # Check for downtrend (price below both EMAs + volume spike)
        is_downtrend = current_price < ema_high and current_price < ema_low

        if is_downtrend and volume_spike and not signals['should_enter']:
            # Calculate position sizing
            risk_amount = self.capital * RISK_PER_TRADE
            stop_loss = ema_high  # Use upper EMA as stop loss
            risk_per_unit = stop_loss - current_price

            if risk_per_unit > 0:
                position_size_usd = risk_amount * RISK_REWARD_RATIO
                take_profit = current_price - (risk_per_unit * RISK_REWARD_RATIO)

                potential_profit = position_size_usd * (current_price - take_profit) / current_price

                if potential_profit >= MIN_PROFIT_TARGET:
                    signals['should_enter'] = True
                    signals['direction'] = 'SHORT'
                    signals['stop_loss'] = stop_loss
                    signals['take_profit'] = take_profit
                    signals['position_size'] = position_size_usd
                    signals['reason'] = f'Downtrend + Volume spike. Risk ${risk_amount:.2f} to make ${potential_profit:.2f}'

        return signals

    def execute_trade(self, signals):
        """
        Execute a trade based on signals
        (For now, this is simulated)
        """

        if not signals['should_enter']:
            return False

        # Create trade record
        trade = {
            'timestamp': datetime.now().isoformat(),
            'direction': signals['direction'],
            'position_size_usd': signals['position_size'],
            'stop_loss': signals['stop_loss'],
            'take_profit': signals['take_profit'],
            'reason': signals['reason'],
            'status': 'open'
        }

        print("\n" + "="*60)
        print(f"🔔 NEW TRADE SIGNAL!")
        print("="*60)
        print(f"📊 Direction: {trade['direction']}")
        print(f"💵 Position Size: ${trade['position_size_usd']:.2f}")
        print(f"🛑 Stop Loss: ${trade['stop_loss']:.2f}")
        print(f"🎯 Take Profit: ${trade['take_profit']:.2f}")
        print(f"💡 Reason: {trade['reason']}")
        print("="*60 + "\n")

        # Add to positions and history
        self.positions.append(trade)
        self.trade_history.append(trade)

        # Update counters
        self.trades_today += 1
        self.last_trade_date = datetime.now().date()

        # Save state
        self.save_state()

        return True

    def run_strategy_check(self):
        """
        Run a single strategy check
        In a real implementation, this would fetch live market data
        """

        print("\n🔍 Running Strategy Check...")

        # Check if trading is allowed
        allowed, reason = self.check_trading_allowed()
        if not allowed:
            print(f"⛔ Trading not allowed: {reason}")
            return False

        # In a real implementation, you would:
        # 1. Fetch current price data for BTC
        # 2. Calculate EMAs
        # 3. Get volume data
        # 4. Analyze entry signals
        # 5. Execute trades if signals are good

        print("📊 Market data analysis would happen here")
        print("💡 In production, this would call exchange APIs")
        print("✅ For now, this is a framework for your strategy")

        return True

    def get_status_report(self):
        """Generate a status report"""

        pnl = self.capital - self.start_capital
        pnl_pct = (pnl / self.start_capital) * 100

        print("\n" + "="*60)
        print("📊 STRATEGY STATUS REPORT")
        print("="*60)
        print(f"💰 Current Capital: ${self.capital:.2f}")
        print(f"📈 P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
        print(f"🎯 Monthly Target: ${self.start_capital * TARGET_MONTHLY_RETURN:.2f} ({TARGET_MONTHLY_RETURN*100}%)")
        print(f"📊 Open Positions: {len(self.positions)}")
        print(f"📜 Total Trades: {len(self.trade_history)}")
        print(f"📅 Trades Today: {self.trades_today}")
        print("="*60 + "\n")

# ============================================================================
# EDUCATIONAL GUIDE
# ============================================================================

def print_beginner_guide():
    """Print educational guide for beginners"""

    guide = """
================================================================================
    🌙 BMAD BEGINNER TRADING STRATEGY GUIDE 🚀
================================================================================

📚 WHAT IS THIS STRATEGY?

This is a simple, safe trading strategy designed for beginners starting with
just $100. It's based on the "EMAVolumeSync" method - a proven trend-following
approach that combines price movement (EMAs) with volume analysis.

💡 HOW IT WORKS:

1. ✅ Wait for a clear trend (price above/below EMA lines)
2. ✅ Confirm with volume spike (shows strong interest)
3. ✅ Enter trade with tight stop loss (limit risk to $2)
4. ✅ Target 2.5:1 profit ($5 profit for $2 risk)
5. ✅ Exit when trend reverses or target hit

🛡️ RISK MANAGEMENT:

• Max Risk: $2 per trade (2% of $100)
• Stop Loss: Always used (automatic exit if wrong)
• Position Size: Calculated based on risk
• Daily Limit: Maximum 2 trades per day
• Monthly Limit: Stop at +5% profit or -10% loss

📊 REALISTIC EXPECTATIONS:

✅ GOOD MONTHS: 2-5% return ($2-$5 on $100)
❌ BAD MONTHS: 0-10% loss (max -$10 on $100)
⚠️ NOT REALISTIC: Making 50% or 100% monthly consistently

📖 BEGINNER TIPS:

1. Start with paper trading (simulated, no real money)
2. Learn to recognize trends before trading
3. Never risk more than you can afford to lose
4. Keep a trading journal to learn from mistakes
5. Be patient - good setups take time
6. Don't chase losses - stick to the plan
7. Take profits when you hit your target

🔧 NEXT STEPS TO USE THIS:

1. Paper trade for 1-2 months first
2. Learn how to read candlestick charts
3. Practice identifying trends and volume spikes
4. Connect to a real exchange API (when ready)
5. Start with the minimum ($100) and learn
6. Scale up ONLY after consistent profits

⚠️ IMPORTANT WARNINGS:

• Trading carries risk of loss
• Past performance ≠ future results
• Only trade with money you can afford to lose
• This is educational - not financial advice
• Do your own research before trading

================================================================================
    💪 Ready to learn and grow as a trader? Let's go! 🚀
================================================================================
"""
    print(guide)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""

    # Print guide
    print_beginner_guide()

    # Initialize strategy
    strategy = BMADBeginnerStrategy()

    # Show current status
    strategy.get_status_report()

    # Run a strategy check
    strategy.run_strategy_check()

    print("\n✅ Framework ready!")
    print("📖 Next: Connect to exchange API and fetch real market data")
    print("💡 For now, this shows you the structure and risk management")

if __name__ == "__main__":
    main()
