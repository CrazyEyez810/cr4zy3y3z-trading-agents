"""
🌙 Moon Dev's BMAD Master Trading Agent
Built with love by Moon Dev 🚀

BMAD = Breakthrough Method for Agile AI Driven Development
Applied to trading: Multi-agent orchestration for intelligent trading decisions

This agent orchestrates multiple specialized agents through 4 BMAD phases:
1. Analysis Phase - Gather market intelligence from all agents
2. Planning Phase - Create trading plan based on agent consensus
3. Solutioning Phase - Determine optimal entry/exit strategy
4. Implementation Phase - Execute trades with proper risk management

For $100 capital, targeting 2-5% monthly returns with strict risk management.
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

# Capital Settings
INITIAL_CAPITAL = 100  # Starting capital in USD
TARGET_MONTHLY_RETURN = 0.025  # 2.5% monthly target (conservative)
MAX_MONTHLY_RETURN = 0.05  # 5% monthly max (take profits)
MAX_MONTHLY_LOSS = -0.10  # -10% max drawdown (stop trading)

# Risk Management
MAX_POSITION_SIZE_PCT = 0.20  # Max 20% of capital per trade
RISK_PER_TRADE_PCT = 0.02  # Risk 2% per trade
MIN_RISK_REWARD_RATIO = 2.5  # Minimum 2.5:1 RR ratio

# Agent Consensus Settings
MIN_AGENTS_FOR_TRADE = 2  # At least 2 agents must agree
MIN_CONFIDENCE_THRESHOLD = 60  # Minimum 60% confidence

# Trading Timeframe
CHECK_INTERVAL_MINUTES = 60  # Check every hour for opportunities

# Agents to Orchestrate
ENABLED_AGENTS = {
    'sentiment': True,   # Twitter sentiment analysis
    'funding': True,     # Funding rate opportunities
    'risk': True,        # Risk management
}

# Model Configuration
MODEL_CONFIG = {
    "type": "claude",
    "name": "claude-3-5-haiku-latest",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Voice Announcements
VOICE_ENABLED = True
VOICE_MODEL = "tts-1"
VOICE_NAME = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1.0

# ============================================================================
# IMPORTS
# ============================================================================

import os
import sys
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from termcolor import cprint, colored
from dotenv import load_dotenv
import openai

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.base_agent import BaseAgent
from src.models import model_factory
from src import config

# ============================================================================
# BMAD MASTER AGENT
# ============================================================================

class BMADMasterAgent(BaseAgent):
    """
    🎯 BMAD Master Trading Agent

    Orchestrates multiple specialized agents through 4 phases:
    - Phase 1: Analysis (gather intelligence)
    - Phase 2: Planning (create strategy)
    - Phase 3: Solutioning (optimize execution)
    - Phase 4: Implementation (execute & monitor)
    """

    def __init__(self):
        """Initialize the BMAD Master Agent"""
        super().__init__('bmad_master')

        load_dotenv()

        # Initialize model for decision making
        self.model = model_factory.get_model(
            MODEL_CONFIG["type"],
            MODEL_CONFIG["name"],
            temperature=MODEL_CONFIG["temperature"],
            max_tokens=MODEL_CONFIG["max_tokens"]
        )

        # Initialize OpenAI for voice
        if VOICE_ENABLED:
            openai_key = os.getenv("OPENAI_KEY")
            if openai_key:
                openai.api_key = openai_key
            else:
                cprint("⚠️ OPENAI_KEY not found - voice disabled", "yellow")

        # Setup directories
        self.data_dir = PROJECT_ROOT / "src" / "data" / "bmad_master"
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        # Trading state
        self.capital = INITIAL_CAPITAL
        self.start_capital = INITIAL_CAPITAL
        self.positions = {}
        self.trade_history = []
        self.current_phase = None

        # Performance tracking
        self.monthly_return = 0.0
        self.total_return = 0.0
        self.trades_today = 0
        self.last_trade_time = None

        # Load or initialize state
        self.state_file = self.data_dir / "bmad_state.json"
        self.load_state()

        cprint("\n" + "="*60, "cyan")
        cprint("🚀 BMAD Master Trading Agent Initialized!", "green", attrs=["bold"])
        cprint("="*60, "cyan")
        cprint(f"💰 Capital: ${self.capital:.2f}", "white")
        cprint(f"🎯 Monthly Target: {TARGET_MONTHLY_RETURN*100}% (${self.capital * TARGET_MONTHLY_RETURN:.2f})", "white")
        cprint(f"🛡️ Max Drawdown: {MAX_MONTHLY_LOSS*100}%", "white")
        cprint(f"📊 Enabled Agents: {', '.join([k for k, v in ENABLED_AGENTS.items() if v])}", "white")
        cprint("="*60 + "\n", "cyan")

    def load_state(self):
        """Load trading state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.capital = state.get('capital', INITIAL_CAPITAL)
                    self.positions = state.get('positions', {})
                    self.trade_history = state.get('trade_history', [])
                    self.monthly_return = state.get('monthly_return', 0.0)
                    cprint(f"📂 Loaded state: ${self.capital:.2f} capital", "cyan")
            except Exception as e:
                cprint(f"⚠️ Error loading state: {e}", "yellow")

    def save_state(self):
        """Save trading state to file"""
        try:
            state = {
                'capital': self.capital,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'monthly_return': self.monthly_return,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            cprint(f"❌ Error saving state: {e}", "red")

    def announce(self, message, is_important=False):
        """Make voice announcement"""
        if not VOICE_ENABLED:
            return

        try:
            print(f"\n🔊 {message}")

            # Generate speech
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )

            # Save and play audio
            audio_file = self.audio_dir / f"bmad_{int(time.time())}.mp3"
            response.stream_to_file(str(audio_file))

            # Play audio (macOS)
            if sys.platform == "darwin":
                os.system(f'afplay "{audio_file}"')

            # Clean up old audio files
            self.cleanup_audio()

        except Exception as e:
            cprint(f"⚠️ Voice error: {e}", "yellow")

    def cleanup_audio(self):
        """Remove old audio files (keep last 10)"""
        try:
            audio_files = sorted(self.audio_dir.glob("bmad_*.mp3"))
            if len(audio_files) > 10:
                for f in audio_files[:-10]:
                    f.unlink()
        except:
            pass

    # ========================================================================
    # PHASE 1: ANALYSIS
    # ========================================================================

    def phase_1_analysis(self):
        """
        Phase 1: Analysis
        Gather intelligence from all enabled agents
        """
        self.current_phase = "Analysis"
        cprint("\n" + "="*60, "blue")
        cprint("📊 PHASE 1: ANALYSIS", "blue", attrs=["bold"])
        cprint("="*60, "blue")

        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'agents': {}
        }

        # Collect data from each enabled agent
        if ENABLED_AGENTS.get('sentiment'):
            analysis_data['agents']['sentiment'] = self.analyze_sentiment()

        if ENABLED_AGENTS.get('funding'):
            analysis_data['agents']['funding'] = self.analyze_funding()

        if ENABLED_AGENTS.get('risk'):
            analysis_data['agents']['risk'] = self.analyze_risk()

        cprint(f"\n✅ Analysis complete: {len(analysis_data['agents'])} agents consulted", "green")
        return analysis_data

    def analyze_sentiment(self):
        """Get sentiment analysis data"""
        cprint("\n🐦 Analyzing Twitter Sentiment...", "cyan")

        # TODO: Actually call sentiment agent
        # For now, return mock data
        result = {
            'score': 0.3,  # Positive sentiment
            'confidence': 65,
            'signal': 'BULLISH',
            'source': 'twitter'
        }

        cprint(f"  └─ Sentiment: {result['signal']} ({result['score']:.2f})", "white")
        return result

    def analyze_funding(self):
        """Get funding rate analysis"""
        cprint("\n💰 Analyzing Funding Rates...", "cyan")

        # TODO: Actually call funding agent
        # For now, return mock data
        result = {
            'rate': -2.5,  # Negative funding = potential long opportunity
            'signal': 'BUY',
            'confidence': 70,
            'reason': 'Negative funding in uptrend suggests short squeeze'
        }

        cprint(f"  └─ Signal: {result['signal']} (Confidence: {result['confidence']}%)", "white")
        return result

    def analyze_risk(self):
        """Get risk management data"""
        cprint("\n🛡️ Checking Risk Parameters...", "cyan")

        # Calculate current risk metrics
        monthly_pnl = self.capital - self.start_capital
        monthly_pnl_pct = (monthly_pnl / self.start_capital) * 100

        result = {
            'capital': self.capital,
            'monthly_pnl': monthly_pnl,
            'monthly_pnl_pct': monthly_pnl_pct,
            'can_trade': True,
            'reason': 'Within risk limits'
        }

        # Check if we hit max gain
        if monthly_pnl_pct >= MAX_MONTHLY_RETURN * 100:
            result['can_trade'] = False
            result['reason'] = f'Hit monthly target ({monthly_pnl_pct:.1f}%)'

        # Check if we hit max loss
        elif monthly_pnl_pct <= MAX_MONTHLY_LOSS * 100:
            result['can_trade'] = False
            result['reason'] = f'Hit max drawdown ({monthly_pnl_pct:.1f}%)'

        cprint(f"  └─ P&L: ${monthly_pnl:.2f} ({monthly_pnl_pct:.1f}%)", "white")
        cprint(f"  └─ Can Trade: {result['can_trade']}", "green" if result['can_trade'] else "red")

        return result

    # ========================================================================
    # PHASE 2: PLANNING
    # ========================================================================

    def phase_2_planning(self, analysis_data):
        """
        Phase 2: Planning
        Create trading plan based on agent consensus
        """
        self.current_phase = "Planning"
        cprint("\n" + "="*60, "blue")
        cprint("🎯 PHASE 2: PLANNING", "blue", attrs=["bold"])
        cprint("="*60, "blue")

        # Check if we can trade
        risk_data = analysis_data['agents'].get('risk', {})
        if not risk_data.get('can_trade', True):
            cprint(f"\n⛔ Cannot trade: {risk_data.get('reason')}", "red")
            return None

        # Count agent signals
        signals = []
        confidences = []

        for agent_name, agent_data in analysis_data['agents'].items():
            if agent_name == 'risk':
                continue

            signal = agent_data.get('signal', '').upper()
            confidence = agent_data.get('confidence', 0)

            if signal in ['BUY', 'BULLISH']:
                signals.append('BUY')
                confidences.append(confidence)
            elif signal in ['SELL', 'BEARISH']:
                signals.append('SELL')
                confidences.append(confidence)

        cprint(f"\n📊 Agent Signals: {signals}", "white")
        cprint(f"📊 Confidences: {confidences}", "white")

        # Check consensus
        if len(signals) < MIN_AGENTS_FOR_TRADE:
            cprint(f"\n⚠️ Not enough agents agree (need {MIN_AGENTS_FOR_TRADE})", "yellow")
            return None

        # Determine consensus signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')

        if buy_count > sell_count:
            consensus_signal = 'BUY'
            avg_confidence = sum(c for s, c in zip(signals, confidences) if s == 'BUY') / buy_count
        elif sell_count > buy_count:
            consensus_signal = 'SELL'
            avg_confidence = sum(c for s, c in zip(signals, confidences) if s == 'SELL') / sell_count
        else:
            cprint("\n⚠️ No consensus - agents split", "yellow")
            return None

        # Check confidence threshold
        if avg_confidence < MIN_CONFIDENCE_THRESHOLD:
            cprint(f"\n⚠️ Confidence too low ({avg_confidence:.0f}% < {MIN_CONFIDENCE_THRESHOLD}%)", "yellow")
            return None

        # Create trading plan
        plan = {
            'signal': consensus_signal,
            'confidence': avg_confidence,
            'agents_agree': len([s for s in signals if s == consensus_signal]),
            'total_agents': len(signals),
            'analysis_data': analysis_data
        }

        cprint(f"\n✅ Trading Plan Created:", "green")
        cprint(f"  └─ Signal: {plan['signal']}", "white")
        cprint(f"  └─ Confidence: {plan['confidence']:.0f}%", "white")
        cprint(f"  └─ Consensus: {plan['agents_agree']}/{plan['total_agents']} agents", "white")

        return plan

    # ========================================================================
    # PHASE 3: SOLUTIONING
    # ========================================================================

    def phase_3_solutioning(self, plan):
        """
        Phase 3: Solutioning
        Determine optimal entry, exit, and position sizing
        """
        self.current_phase = "Solutioning"
        cprint("\n" + "="*60, "blue")
        cprint("🔧 PHASE 3: SOLUTIONING", "blue", attrs=["bold"])
        cprint("="*60, "blue")

        if not plan:
            return None

        # Calculate position size
        risk_amount = self.capital * RISK_PER_TRADE_PCT
        max_position_size = self.capital * MAX_POSITION_SIZE_PCT

        # For now, use simple position sizing
        # TODO: Calculate based on actual price and stop loss
        position_size = min(risk_amount * MIN_RISK_REWARD_RATIO, max_position_size)

        solution = {
            'signal': plan['signal'],
            'position_size_usd': position_size,
            'risk_amount': risk_amount,
            'risk_reward_ratio': MIN_RISK_REWARD_RATIO,
            'confidence': plan['confidence']
        }

        cprint(f"\n✅ Solution Created:", "green")
        cprint(f"  └─ Position Size: ${solution['position_size_usd']:.2f}", "white")
        cprint(f"  └─ Risk Amount: ${solution['risk_amount']:.2f}", "white")
        cprint(f"  └─ Risk/Reward: {solution['risk_reward_ratio']}:1", "white")

        return solution

    # ========================================================================
    # PHASE 4: IMPLEMENTATION
    # ========================================================================

    def phase_4_implementation(self, solution):
        """
        Phase 4: Implementation
        Execute the trade and monitor
        """
        self.current_phase = "Implementation"
        cprint("\n" + "="*60, "blue")
        cprint("⚡ PHASE 4: IMPLEMENTATION", "blue", attrs=["bold"])
        cprint("="*60, "blue")

        if not solution:
            cprint("\n⚠️ No solution to implement", "yellow")
            return False

        # For now, just log the trade (not executing real trades yet)
        cprint(f"\n📝 SIMULATED TRADE:", "yellow")
        cprint(f"  └─ Signal: {solution['signal']}", "white")
        cprint(f"  └─ Size: ${solution['position_size_usd']:.2f}", "white")
        cprint(f"  └─ Risk: ${solution['risk_amount']:.2f}", "white")

        # Record trade
        trade = {
            'timestamp': datetime.now().isoformat(),
            'signal': solution['signal'],
            'position_size': solution['position_size_usd'],
            'risk_amount': solution['risk_amount'],
            'confidence': solution['confidence'],
            'status': 'simulated'
        }

        self.trade_history.append(trade)
        self.save_state()

        # Announce
        message = f"BMAD Master: {solution['signal']} signal with {solution['confidence']:.0f}% confidence. Position size: ${solution['position_size_usd']:.2f}"
        self.announce(message, is_important=True)

        cprint("\n✅ Trade recorded!", "green")
        return True

    # ========================================================================
    # MAIN RUN METHOD
    # ========================================================================

    def run(self):
        """
        Main run loop - executes all 4 BMAD phases
        """
        cprint("\n" + "="*60, "green")
        cprint("🚀 BMAD MASTER AGENT - STARTING RUN CYCLE", "green", attrs=["bold"])
        cprint("="*60, "green")

        try:
            # Phase 1: Analysis
            analysis_data = self.phase_1_analysis()

            # Phase 2: Planning
            plan = self.phase_2_planning(analysis_data)

            # Phase 3: Solutioning
            solution = self.phase_3_solutioning(plan)

            # Phase 4: Implementation
            result = self.phase_4_implementation(solution)

            cprint("\n" + "="*60, "green")
            cprint("✅ BMAD CYCLE COMPLETE", "green", attrs=["bold"])
            cprint("="*60, "green")

            return result

        except Exception as e:
            cprint(f"\n❌ Error in BMAD cycle: {e}", "red")
            import traceback
            traceback.print_exc()
            return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    cprint("\n" + "="*80, "cyan", attrs=["bold"])
    cprint(" "*20 + "🌙 BMAD MASTER TRADING AGENT 🚀", "cyan", attrs=["bold"])
    cprint("="*80 + "\n", "cyan", attrs=["bold"])

    try:
        # Initialize agent
        agent = BMADMasterAgent()

        # Run one cycle
        cprint("\n🎯 Running single BMAD cycle...\n", "yellow")
        agent.run()

        # TODO: Add continuous loop with CHECK_INTERVAL_MINUTES
        # while True:
        #     agent.run()
        #     time.sleep(CHECK_INTERVAL_MINUTES * 60)

    except KeyboardInterrupt:
        cprint("\n\n👋 BMAD Master Agent stopped by user", "yellow")
    except Exception as e:
        cprint(f"\n\n❌ Fatal error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
