#!/usr/bin/env python3
"""
Test script to validate image detection against training data.
Tests the core detection algorithm without needing Discord or a bot.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_detector import ImageDetector

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_detection():
    """Test detection against training data."""
    
    # Training data is in root/Training-Data folder
    training_data_path = Path(__file__).parent.parent / "Training-Data"
    
    if not training_data_path.exists():
        logger.error(f"Training data path not found: {training_data_path}")
        return
    
    # Get list of training images
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    training_files = sorted([
        f for f in training_data_path.iterdir() 
        if f.suffix.lower() in image_extensions
    ])
    
    if not training_files:
        logger.error(f"No training images found in {training_data_path}")
        return
    
    logger.info(f"Found {len(training_files)} training images:")
    for f in training_files:
        logger.info(f"  - {f.name}")
    
    # Initialize detector
    logger.info("\nInitializing ImageDetector...")
    detector = ImageDetector(training_data_path=training_data_path)
    
    logger.info(f"Detector loaded {len(detector.training_images)} training images")
    logger.info(f"Detection threshold: {detector.similarity_threshold}")
    
    # Test detection on each training image
    logger.info("\n" + "="*70)
    logger.info("TESTING: Each training image should match itself (confidence > 0.75)")
    logger.info("="*70)
    
    all_passed = True
    
    for test_file in training_files:
        logger.info(f"\nTesting: {test_file.name}")
        
        # Read image bytes
        with open(test_file, 'rb') as f:
            image_bytes = f.read()
        
        # Run detection
        is_similar, confidence, matched_image = await detector.detect_similar_image(image_bytes)
        
        # Check result
        expected_match = test_file.name
        status = "✓ PASS" if is_similar and matched_image == expected_match else "✗ FAIL"
        
        logger.info(f"  Result: {status}")
        logger.info(f"    is_similar: {is_similar}")
        logger.info(f"    confidence: {confidence:.4f}")
        logger.info(f"    matched: {matched_image}")
        logger.info(f"    expected: {expected_match}")
        
        if not (is_similar and matched_image == expected_match):
            all_passed = False
    
    # Print statistics
    logger.info("\n" + "="*70)
    logger.info("DETECTION STATISTICS")
    logger.info("="*70)
    stats = detector.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Final result
    logger.info("\n" + "="*70)
    if all_passed:
        logger.info("✓ ALL TESTS PASSED - Detection is working correctly!")
    else:
        logger.info("✗ SOME TESTS FAILED - Detection needs adjustment")
        logger.info("Recommendations:")
        logger.info("  1. Check bot.log for detailed comparison scores")
        logger.info("  2. Consider lowering SIMILARITY_THRESHOLD in .env")
        logger.info("  3. Verify training images exist and are valid")
    logger.info("="*70)
    
    return all_passed

if __name__ == '__main__':
    success = asyncio.run(test_detection())
    sys.exit(0 if success else 1)
