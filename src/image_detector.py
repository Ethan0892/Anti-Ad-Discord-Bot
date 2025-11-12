import cv2
import numpy as np
from PIL import Image
import io
import os
from pathlib import Path
from typing import List, Tuple, Dict
import logging
import hashlib
import pickle
from functools import lru_cache
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger('image_detector')


class ImageDetector:
    """Detects similar images using multiple computer vision techniques with caching."""
    
    def __init__(self, training_data_path: str, similarity_threshold: float = 0.65):
        self.training_data_path = Path(training_data_path)
        self.similarity_threshold = similarity_threshold
        self.training_images = []
        self.training_features = []
        
        # Initialize feature detectors with enhanced settings
        self.orb = cv2.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=12)  # Enhanced ORB
        self.sift = cv2.SIFT_create()  # SIFT for better accuracy
        self.akaze = cv2.AKAZE_create()  # Add AKAZE for additional robustness
        
        # Matchers with different strategies
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.bf_matcher_sift = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        self.bf_matcher_akaze = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        # FLANN matcher for faster matching on large datasets
        FLANN_INDEX_KDTREE = 1
        self.flann = cv2.FlannBasedMatcher({'algorithm': FLANN_INDEX_KDTREE, 'trees': 5}, {})
        
        # Cache for recent detections
        self.detection_cache: Dict[str, Tuple[bool, float, str, float]] = {}
        self.cache_timeout = 3600  # 1 hour
        
        # Performance tracking
        self.detection_times = []
        self.algorithm_performance = {'sift': [], 'orb': [], 'akaze': [], 'structural': []}
        
        self.load_training_data()
    
    def load_training_data(self):
        """Load and process all training images."""
        logger.info(f"Loading training data from {self.training_data_path}")
        
        if not self.training_data_path.exists():
            logger.error(f"Training data path does not exist: {self.training_data_path}")
            return
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        loaded_count = 0
        
        for img_path in sorted(self.training_data_path.iterdir()):
            if img_path.suffix.lower() in image_extensions:
                try:
                    # Load image
                    img = cv2.imread(str(img_path))
                    if img is None:
                        logger.warning(f"Could not load image: {img_path}")
                        continue
                    
                    # Normalize size (max 1024x1024 to save memory)
                    height, width = img.shape[:2]
                    if max(height, width) > 1024:
                        scale = 1024 / max(height, width)
                        img = cv2.resize(img, (int(width * scale), int(height * scale)))
                    
                    # Convert to grayscale for feature detection
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Extract ORB features
                    orb_keypoints, orb_descriptors = self.orb.detectAndCompute(gray, None)
                    
                    # Extract SIFT features
                    sift_keypoints, sift_descriptors = self.sift.detectAndCompute(gray, None)
                    
                    # Extract AKAZE features for robustness
                    akaze_keypoints, akaze_descriptors = self.akaze.detectAndCompute(gray, None)
                    
                    if orb_descriptors is not None or sift_descriptors is not None:
                        self.training_images.append({
                            'path': str(img_path),
                            'img': img,
                            'image': img,
                            'gray': gray,
                            'orb_keypoints': orb_keypoints,
                            'orb_descriptors': orb_descriptors,
                            'sift_keypoints': sift_keypoints,
                            'sift_descriptors': sift_descriptors,
                            'akaze_keypoints': akaze_keypoints,
                            'akaze_descriptors': akaze_descriptors,
                            'hist': self._compute_histogram(img),
                            'phash': self._compute_perceptual_hash(gray)
                        })
                        loaded_count += 1
                        logger.info(f"Loaded training image: {img_path.name}")
                    else:
                        logger.warning(f"No features detected in: {img_path.name}")
                        
                except Exception as e:
                    logger.error(f"Error loading {img_path}: {e}")
        
        logger.info(f"Successfully loaded {loaded_count} training images")
    
    def _compute_histogram(self, image: np.ndarray) -> np.ndarray:
        """Compute color histogram for image comparison."""
        # Convert to HSV for better color representation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate histogram
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist
    
    def _compute_perceptual_hash(self, image: np.ndarray) -> str:
        """Compute perceptual hash of image for quick similarity checks."""
        try:
            # Resize to 8x8
            small = cv2.resize(image, (8, 8))
            
            # Convert to grayscale if needed
            if len(small.shape) == 3:
                small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            
            # Compute average
            avg = small.mean()
            
            # Create hash
            hash_bits = (small > avg).flatten()
            hash_str = ''.join(['1' if x else '0' for x in hash_bits])
            
            return hash_str
        except Exception as e:
            logger.error(f"Error computing perceptual hash: {e}")
            return ""
    
    def _compute_template_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute template matching similarity."""
        try:
            # Normalize image sizes
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            # Make img1 the smaller one for template matching
            if h1 * w1 > h2 * w2:
                img1, img2 = img2, img1
            
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            if h1 < 10 or w1 < 10 or h2 < 10 or w2 < 10:
                return 0.0
            
            # Try template matching at different scales
            best_match = 0.0
            
            for scale in [0.8, 0.9, 1.0, 1.1, 1.2]:
                scaled_h = max(10, int(h1 * scale))
                scaled_w = max(10, int(w1 * scale))
                
                if scaled_h <= h2 and scaled_w <= w2:
                    try:
                        img1_scaled = cv2.resize(img1, (scaled_w, scaled_h))
                        result = cv2.matchTemplate(img2, img1_scaled, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        
                        # max_val is the best correlation
                        if max_val > best_match:
                            best_match = max_val
                    except:
                        continue
            
            return max(0.0, min(1.0, best_match))
            
        except Exception as e:
            logger.debug(f"Template matching error (non-critical): {e}")
            return 0.0
    
    def _compare_histograms(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """Compare two histograms using correlation."""
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    def _compare_features(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        """Compare two sets of feature descriptors."""
        if desc1 is None or desc2 is None:
            return 0.0
        
        try:
            # Ensure at least some descriptors
            if len(desc1) == 0 or len(desc2) == 0:
                return 0.0
            
            # Match features
            matches = self.bf_matcher.match(desc1, desc2)
            
            if len(matches) == 0:
                return 0.0
            
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Calculate similarity based on good matches
            # Lower distance = better match
            good_matches = [m for m in matches if m.distance < 50]
            
            # If no good matches, use ratio of best matches
            if len(good_matches) == 0:
                # Check if best match is good enough
                if matches[0].distance < 70:
                    good_matches = matches[:max(1, len(matches)//4)]
                else:
                    return 0.0
            
            # Similarity based on number of good matches
            similarity = len(good_matches) / max(len(desc1), len(desc2))
            
            # Also consider average distance of good matches
            if good_matches:
                avg_distance = np.mean([m.distance for m in good_matches])
                distance_factor = max(0, 1.0 - (avg_distance / 100.0))
                similarity = (similarity * 0.6) + (distance_factor * 0.4)
            
            return min(1.0, similarity)
            
        except Exception as e:
            logger.error(f"Error comparing ORB features: {e}")
            return 0.0
    
    def _compare_sift_features(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        """Compare two sets of SIFT feature descriptors."""
        if desc1 is None or desc2 is None:
            return 0.0
        
        try:
            # Ensure descriptors are correct type
            if not isinstance(desc1, np.ndarray) or not isinstance(desc2, np.ndarray):
                return 0.0
            
            # Need at least 2 features for knnMatch
            if len(desc1) < 2 or len(desc2) < 2:
                return 0.0
            
            # Ensure descriptors are float32
            desc1 = desc1.astype(np.float32)
            desc2 = desc2.astype(np.float32)
            
            # Match features with ratio test
            try:
                matches = self.bf_matcher_sift.knnMatch(desc1, desc2, k=2)
            except cv2.error as e:
                # Fallback to single match if knnMatch fails
                logger.debug(f"knnMatch failed, trying match: {e}")
                matches = self.bf_matcher_sift.match(desc1, desc2)
                if len(matches) == 0:
                    return 0.0
                # Use match results directly
                good_matches = sorted(matches, key=lambda x: x.distance)[:len(desc1)//2]
                similarity = len(good_matches) / max(len(desc1), len(desc2))
                return min(1.0, similarity)
            
            if len(matches) == 0:
                return 0.0
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
                elif len(match_pair) == 1:
                    # Single match, accept it
                    good_matches.append(match_pair[0])
            
            if len(good_matches) == 0:
                return 0.0
            
            similarity = len(good_matches) / max(len(desc1), len(desc2))
            return min(1.0, similarity)
            
        except Exception as e:
            logger.error(f"Error comparing SIFT features: {e}")
            return 0.0
    
    def _compare_akaze_features(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        """Compare two sets of AKAZE feature descriptors (binary features like ORB)."""
        if desc1 is None or desc2 is None:
            return 0.0
        
        try:
            if len(desc1) < 1 or len(desc2) < 1:
                return 0.0
            
            # Use Hamming distance for binary features
            matches = self.bf_matcher_akaze.knnMatch(desc1, desc2, k=2)
            
            if len(matches) == 0:
                return 0.0
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 70:  # Hamming distance threshold
                        good_matches.append(m)
                elif len(match_pair) == 1 and match_pair[0].distance < 50:
                    good_matches.append(match_pair[0])
            
            if len(good_matches) == 0:
                return 0.0
            
            similarity = len(good_matches) / max(len(desc1), len(desc2))
            return min(1.0, similarity)
            
        except Exception as e:
            logger.debug(f"Error comparing AKAZE features: {e}")
            return 0.0
    
    def _compute_structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute structural similarity between two images."""
        try:
            # Resize images to same size for comparison
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])
            
            # Ensure reasonable size
            if height < 10 or width < 10:
                logger.debug("Images too small for structural comparison")
                return 0.0
            
            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))
            
            # Compute using multiple methods
            
            # 1. Direct pixel comparison with histogram normalization
            img1_hist = cv2.calcHist([img1_resized], [0], None, [256], [0, 256])
            img2_hist = cv2.calcHist([img2_resized], [0], None, [256], [0, 256])
            img1_hist = cv2.normalize(img1_hist, img1_hist).flatten()
            img2_hist = cv2.normalize(img2_hist, img2_hist).flatten()
            hist_match = cv2.compareHist(img1_hist, img2_hist, cv2.HISTCMP_CORREL)
            
            # 2. Direct pixel difference
            diff = cv2.absdiff(img1_resized, img2_resized)
            mse = np.mean(diff.astype(float) ** 2)
            
            if mse == 0:
                pixel_similarity = 1.0
            else:
                max_mse = 255.0 ** 2
                pixel_similarity = max(0, 1.0 - (mse / max_mse))
            
            # 3. SSIM-like approach with Laplacian
            lap1 = cv2.Laplacian(img1_resized, cv2.CV_64F)
            lap2 = cv2.Laplacian(img2_resized, cv2.CV_64F)
            lap_diff = np.mean(np.abs(lap1 - lap2))
            edge_similarity = max(0, 1.0 - (lap_diff / 255.0))
            
            # Combine all methods
            structural_similarity = (
                hist_match * 0.3 +
                pixel_similarity * 0.4 +
                edge_similarity * 0.3
            )
            
            return min(1.0, max(0.0, structural_similarity))
            
        except Exception as e:
            logger.error(f"Error computing structural similarity: {e}")
            return 0.0
    
    async def detect_similar_image(self, image_bytes: bytes) -> Tuple[bool, float, str]:
        """
        Detect if an image is similar to any training images.
        
        Returns:
            Tuple of (is_similar, confidence, matched_image_name)
        """
        if not self.training_images:
            logger.warning("No training images loaded")
            return False, 0.0, ""
        
        start_time = datetime.now()
        
        # Check cache
        image_hash = hashlib.md5(image_bytes).hexdigest()
        if image_hash in self.detection_cache:
            cached_result, cache_time = self.detection_cache[image_hash], datetime.now()
            if (cache_time - cache_time).total_seconds() < self.cache_timeout:
                logger.debug(f"Cache hit for image hash {image_hash}")
                return cached_result[0], cached_result[1], cached_result[2]
        
        try:
            # Load the image from bytes
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.warning("Could not decode image")
                return False, 0.0, ""
            
            # Normalize size
            height, width = img.shape[:2]
            if max(height, width) > 1024:
                scale = 1024 / max(height, width)
                img = cv2.resize(img, (int(width * scale), int(height * scale)))
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Extract features
            orb_keypoints, orb_descriptors = self.orb.detectAndCompute(gray, None)
            sift_keypoints, sift_descriptors = self.sift.detectAndCompute(gray, None)
            akaze_keypoints, akaze_descriptors = self.akaze.detectAndCompute(gray, None)
            
            # Compute histogram and perceptual hash
            hist = self._compute_histogram(img)
            phash = self._compute_perceptual_hash(gray)
            
            max_similarity = 0.0
            matched_image = ""
            
            # Compare with each training image
            for train_img in self.training_images:
                # 1. Perceptual hash comparison (very fast)
                phash_similarity = self._hamming_distance(phash, train_img['phash'])
                
                # Quick rejection if phash is too different
                if phash_similarity < 0.6:
                    continue
                
                # 2. Compare histograms (color/tone similarity)
                hist_similarity = self._compare_histograms(hist, train_img['hist'])
                
                # 3. Compare ORB features (structural similarity)
                orb_similarity = 0.0
                if orb_descriptors is not None and train_img['orb_descriptors'] is not None:
                    orb_similarity = self._compare_features(orb_descriptors, train_img['orb_descriptors'])
                
                # 4. Compare SIFT features (more robust)
                sift_similarity = 0.0
                if sift_descriptors is not None and train_img['sift_descriptors'] is not None:
                    sift_similarity = self._compare_sift_features(sift_descriptors, train_img['sift_descriptors'])
                
                # 4b. Compare AKAZE features (additional robustness)
                akaze_similarity = 0.0
                if akaze_descriptors is not None and train_img.get('akaze_descriptors') is not None:
                    akaze_similarity = self._compare_akaze_features(akaze_descriptors, train_img['akaze_descriptors'])
                
                # 5. Compute pixel-level similarity
                structural_similarity = self._compute_structural_similarity(gray, train_img['gray'])
                
                # 6. Template matching (rotation/scale invariant)
                template_similarity = self._compute_template_similarity(img, train_img['img'])
                
                # First, check if worth comparing (quick filters)
                # If structural and histogram both low, skip this training image
                quick_score = (hist_similarity + structural_similarity) / 2
                if quick_score < 0.4:
                    logger.debug(
                        f"Quick reject {Path(train_img['path']).name}: "
                        f"hist={hist_similarity:.3f}, struct={structural_similarity:.3f}"
                    )
                    continue
                
                # Weighted average of all similarity measures
                # Enhanced weighting emphasizes feature matching
                combined_similarity = (
                    phash_similarity * 0.08 +      # Quick hash check (fast pre-filter)
                    hist_similarity * 0.15 +        # Color/tone similarity
                    max(orb_similarity, sift_similarity, akaze_similarity) * 0.40 +  # Best feature match
                    structural_similarity * 0.25 +  # Pixel-level structural
                    template_similarity * 0.12      # Template matching (multi-scale)
                )
                
                # Boost score if multiple algorithms agree strongly
                algorithms_strong = sum([
                    orb_similarity > 0.7,
                    sift_similarity > 0.7,
                    akaze_similarity > 0.7
                ])
                if algorithms_strong >= 2:
                    combined_similarity = min(1.0, combined_similarity * 1.2)
                
                if hist_similarity > 0.8 and structural_similarity > 0.8:
                    combined_similarity = min(1.0, combined_similarity * 1.1)
                
                logger.debug(
                    f"Comparison with {Path(train_img['path']).name}: "
                    f"phash={phash_similarity:.3f}, hist={hist_similarity:.3f}, "
                    f"orb={orb_similarity:.3f}, sift={sift_similarity:.3f}, akaze={akaze_similarity:.3f}, "
                    f"struct={structural_similarity:.3f}, template={template_similarity:.3f}, "
                    f"combined={combined_similarity:.3f}"
                )
                
                if combined_similarity > max_similarity:
                    max_similarity = combined_similarity
                    matched_image = Path(train_img['path']).name
            
            is_similar = max_similarity >= self.similarity_threshold
            
            # Track detection time
            detection_time = (datetime.now() - start_time).total_seconds()
            self.detection_times.append(detection_time)
            if len(self.detection_times) > 100:
                self.detection_times.pop(0)
            
            logger.info(
                f"Detection result: is_similar={is_similar}, "
                f"confidence={max_similarity:.3f}, matched={matched_image}, "
                f"time={detection_time:.2f}s"
            )
            
            # Cache result
            result = (is_similar, max_similarity, matched_image)
            self.detection_cache[image_hash] = result
            
            return is_similar, max_similarity, matched_image
            
        except Exception as e:
            logger.error(f"Error detecting similar image: {e}")
            return False, 0.0, ""
    
    def get_stats(self) -> Dict:
        """Get detector statistics."""
        avg_time = sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
        return {
            'training_images': len(self.training_images),
            'cache_size': len(self.detection_cache),
            'avg_detection_time': avg_time,
            'threshold': self.similarity_threshold
        }
    
    def _hamming_distance(self, hash1: str, hash2: str) -> float:
        """Calculate Hamming distance between two hashes (as percentage)."""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 0.0
        
        distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        return 1.0 - (distance / len(hash1))
    
    def _compute_template_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute template matching similarity."""
        try:
            # Normalize image sizes
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            # Make img1 the smaller one for template matching
            if h1 * w1 > h2 * w2:
                img1, img2 = img2, img1
            
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            if h1 < 10 or w1 < 10 or h2 < 10 or w2 < 10:
                return 0.0
            
            # Try template matching at different scales
            best_match = 0.0
            
            for scale in [0.8, 0.9, 1.0, 1.1, 1.2]:
                scaled_h = max(10, int(h1 * scale))
                scaled_w = max(10, int(w1 * scale))
                
                if scaled_h <= h2 and scaled_w <= w2:
                    try:
                        img1_scaled = cv2.resize(img1, (scaled_w, scaled_h))
                        result = cv2.matchTemplate(img2, img1_scaled, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        
                        # max_val is the best correlation
                        if max_val > best_match:
                            best_match = max_val
                    except:
                        continue
            
            return max(0.0, min(1.0, best_match))
            
        except Exception as e:
            logger.debug(f"Template matching error (non-critical): {e}")
            return 0.0

