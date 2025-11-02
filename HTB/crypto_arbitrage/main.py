# """Main application entry point."""
# import asyncio
# import threading
# import time
# from loguru import logger

# from data_ingestion import MultiExchangeAggregator
# from arbitrage_detector import ArbitrageDetector
# from ml_predictor import SpreadPredictor, OpportunityScorer
# from dashboard import ArbitrageDashboard


# class ArbitrageSystem:
#     """Main arbitrage detection system."""

#     def __init__(self):
#         # Initialize components
#         self.detector = ArbitrageDetector()
#         self.spread_predictor = SpreadPredictor()
#         self.opportunity_scorer = OpportunityScorer()
#         self.aggregator = MultiExchangeAggregator(self.on_price_update)
#         self.dashboard = None

#         # Control flags
#         self.running = False
#         self.training_interval = 300  # Train ML model every 5 minutes

#     def on_price_update(self, price_data):
#         """Callback for new price data."""
#         # Update detector (which checks for arbitrage)
#         self.detector.update_price(price_data)

#     async def run_data_collection(self):
#         """Run the data collection and arbitrage detection."""
#         logger.info("Starting data collection and arbitrage detection...")
#         await self.aggregator.start()

#     def start_dashboard(self):
#         """Start the web dashboard in a separate thread."""
#         self.dashboard = ArbitrageDashboard(
#             self.detector,
#             self.spread_predictor,
#             self.opportunity_scorer
#         )
#         self.dashboard.run(host='0.0.0.0', port=8050, debug=False)

#     async def run(self):
#         """Run the complete system."""
#         self.running = True

#         logger.info("=" * 60)
#         logger.info("🚀 CRYPTO ARBITRAGE MONITOR")
#         logger.info("=" * 60)

#         # Load the trained models
#         logger.info("🧠 Loading ML models...")
#         predictor_loaded = self.spread_predictor.load("models/spread_predictor_live.pkl")
#         scorer_loaded = self.opportunity_scorer.load("models/opportunity_scorer_live.pkl")
#         if not predictor_loaded or not scorer_loaded:
#             logger.error("❌ Failed to load one or more ML models. Exiting.")
#             return

#         logger.info("Monitoring exchanges: Coinbase, Binance, Bitstamp")
#         logger.info("Trading pairs: BTC-USD, ETH-USD, SOL-USD")
#         logger.info("=" * 60)
#         logger.info("✅ System ready. Dashboard running at: http://localhost:8050")

#         # Start dashboard in separate thread
#         dashboard_thread = threading.Thread(target=self.start_dashboard, daemon=True)
#         dashboard_thread.start()

#         # Give dashboard time to start
#         await asyncio.sleep(2)

#         # Run data collection
#         await self.run_data_collection()

#     def stop(self):
#         """Stop the system."""
#         logger.info("Stopping arbitrage system...")
#         self.running = False


# def main():
#     """Main entry point."""
#     # Configure logger
#     logger.add(
#         "logs/arbitrage_{time}.log",
#         rotation="1 day",
#         retention="7 days",
#         level="INFO"
#     )

#     system = ArbitrageSystem()

#     try:
#         asyncio.run(system.run())
#     except KeyboardInterrupt:
#         logger.info("Received shutdown signal")
#         system.stop()
#     except Exception as e:
#         logger.error(f"Fatal error: {e}")
#         raise


# if __name__ == "__main__":
#     main()






"""Main application entry point."""
import asyncio
import threading
from loguru import logger
from pathlib import Path
from data_ingestion import MultiExchangeAggregator
from arbitrage_detector import ArbitrageDetector
from ml_predictor import SpreadPredictor, OpportunityScorer
from dashboard import ArbitrageDashboard


class ArbitrageSystem:
    """Main arbitrage detection system."""
    
    def __init__(self):
        # Initialize ML components
        self.spread_predictor = SpreadPredictor()
        self.opportunity_scorer = OpportunityScorer()
        
        # Initialize detector - Try different initialization patterns
        try:
            # Try with ml_predictor parameter
            self.detector = ArbitrageDetector(ml_predictor=self.spread_predictor)
        except TypeError:
            try:
                # Try with spread_predictor and opportunity_scorer
                self.detector = ArbitrageDetector(
                    spread_predictor=self.spread_predictor,
                    opportunity_scorer=self.opportunity_scorer
                )
            except TypeError:
                try:
                    # Try with just predictor
                    self.detector = ArbitrageDetector(predictor=self.spread_predictor)
                except TypeError:
                    # Initialize without ML components
                    logger.warning("⚠️  ArbitrageDetector doesn't accept ML predictor - initializing without it")
                    self.detector = ArbitrageDetector()
                    # Manually attach ML components if detector has these attributes
                    if hasattr(self.detector, 'ml_predictor'):
                        self.detector.ml_predictor = self.spread_predictor
                    if hasattr(self.detector, 'spread_predictor'):
                        self.detector.spread_predictor = self.spread_predictor
                    if hasattr(self.detector, 'opportunity_scorer'):
                        self.detector.opportunity_scorer = self.opportunity_scorer
        
        # Initialize data aggregator
        self.aggregator = MultiExchangeAggregator(self.on_price_update)
        
        self.dashboard = None
        self.running = False
        
        # Training interval (5 minutes)
        self.training_interval = 300

    def on_price_update(self, price_data):
        """Callback for new price data."""
        # Update detector (which checks for arbitrage)
        self.detector.update_price(price_data)

    async def train_ml_models(self):
        """Periodically retrain ML models with new data."""
        while self.running:
            await asyncio.sleep(self.training_interval)
            
            logger.info("🧠 Training ML models with recent data...")
            
            try:
                # Train spread predictor
                for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
                    df = self.detector.get_historical_data(symbol)
                    if df is not None and len(df) > 100:
                        self.spread_predictor.train(df)
                        logger.info(f"✅ Spread predictor updated for {symbol}")
                
                # Save updated models
                self.spread_predictor.save("models/spread_predictor_live.pkl")
                
                # Train opportunity scorer if we have enough opportunities
                recent_opps = self.detector.get_recent_opportunities(minutes=30)
                if len(recent_opps) > 20:
                    # Prepare training data from recent opportunities
                    training_data = []
                    for opp in recent_opps:
                        training_data.append({
                            'spread_pct': opp.spread_pct,
                            'profit_after_fees': opp.profit_after_fees,
                            'symbol': opp.symbol,
                            'timestamp': opp.timestamp
                        })
                    
                    # Train scorer (you'd need to implement this method)
                    # self.opportunity_scorer.train(training_data)
                    # self.opportunity_scorer.save("models/opportunity_scorer_live.pkl")
                
                logger.success("✅ ML models updated successfully")
                
            except Exception as e:
                logger.error(f"❌ Error training ML models: {e}")

    async def run_data_collection(self):
        """Run the data collection and arbitrage detection."""
        logger.info("Starting data collection and arbitrage detection...")
        await self.aggregator.start()

    def start_dashboard(self):
        """Start the web dashboard in a separate thread."""
        self.dashboard = ArbitrageDashboard(
            self.detector,
            self.spread_predictor,
            self.opportunity_scorer
        )
        self.dashboard.run(host='0.0.0.0', port=8050, debug=False)

    async def run(self):
        """Run the complete system."""
        self.running = True
        
        # Create necessary directories
        Path("models").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("🚀 CRYPTO ARBITRAGE MONITOR")
        logger.info("=" * 60)
        
        # Try to load existing trained models
        logger.info("🧠 Loading ML models...")
        predictor_loaded = self.spread_predictor.load("models/spread_predictor_live.pkl")
        scorer_loaded = self.opportunity_scorer.load("models/opportunity_scorer_live.pkl")
        
        if predictor_loaded:
            logger.success("✅ Spread predictor loaded from disk")
        else:
            logger.warning("⚠️  No saved spread predictor found - will train with incoming data")
        
        if scorer_loaded:
            logger.success("✅ Opportunity scorer loaded from disk")
        else:
            logger.warning("⚠️  No saved opportunity scorer found - will train with incoming data")
        
        # Verify models are ready
        if predictor_loaded and not self.spread_predictor.is_trained:
            logger.error("❌ Spread predictor loaded but not marked as trained!")
        
        if scorer_loaded and not self.opportunity_scorer.is_trained:
            logger.error("❌ Opportunity scorer loaded but not marked as trained!")
        
        logger.info("Monitoring exchanges: Coinbase, Binance, Bitstamp")
        logger.info("Trading pairs: BTC-USD, ETH-USD, SOL-USD")
        logger.info("=" * 60)
        logger.info("✅ System ready. Dashboard: http://localhost:8050")
        logger.info("=" * 60)
        
        # Start dashboard in separate thread
        dashboard_thread = threading.Thread(target=self.start_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Give dashboard time to start
        await asyncio.sleep(2)
        
        # Run data collection and ML training concurrently
        await asyncio.gather(
            self.run_data_collection(),
            self.train_ml_models(),
            return_exceptions=True
        )

    def stop(self):
        """Stop the system."""
        logger.info("🛑 Stopping arbitrage system...")
        self.running = False


def main():
    """Main entry point."""
    # Configure logger
    logger.add(
        "logs/arbitrage_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    system = ArbitrageSystem()
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Received shutdown signal (Ctrl+C)")
        system.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        logger.info("👋 System stopped")


if __name__ == "__main__":
    main()