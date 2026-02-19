"""
Synthetic Dataset Generator for LSTM Training
Follows the Dataset Creation Guide exactly

Generates ~6,000 realistic freelancer profiles with:
- Synthetic BERT embeddings (768 dimensions)
- 6 project-based indicators
- Experience level
- Clean trust labels (1=Trustworthy, 0=Risky)

Author: Freelancer Trust Evaluation System
Version: 1.0
"""

import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PersonaConfig:
    """Configuration for a freelancer persona type"""
    name: str
    percentage: float
    projects_range: Tuple[int, int]
    years_range: Tuple[float, float]
    duration_range: Tuple[float, float]  # months


class SyntheticDatasetGenerator:
    """
    Generates synthetic freelancer dataset for LSTM training
    Following the Dataset Creation Guide specifications
    """
    
    def __init__(self, total_samples: int = 6000, seed: int = 42):
        """
        Initialize dataset generator
        
        Args:
            total_samples: Total number of samples to generate (default: 6000)
            seed: Random seed for reproducibility
        """
        self.total_samples = total_samples
        self.seed = seed
        np.random.seed(seed)
        
        # Define persona types (Step 2 of guide)
        self.personas = {
            'Entry': PersonaConfig('Entry', 0.20, (1, 6), (0.5, 2.0), (1.0, 3.0)),
            'Mid': PersonaConfig('Mid', 0.30, (4, 15), (2.0, 5.0), (2.0, 6.0)),
            'Senior': PersonaConfig('Senior', 0.25, (10, 30), (5.0, 10.0), (3.0, 9.0)),
            'Expert': PersonaConfig('Expert', 0.15, (20, 50), (8.0, 15.0), (6.0, 18.0)),
            'Edge': PersonaConfig('Edge', 0.10, (1, 50), (0.5, 15.0), (1.0, 18.0))
        }
        
        # Feature ranges (Step 3 of guide)
        self.overlap_rules = {
            'trustworthy': (0, 1),
            'borderline': (1, 3),
            'risky': (3, 10)
        }
        
        self.tech_consistency_ranges = {
            'strong': (0.75, 1.0),
            'moderate': (0.45, 0.75),
            'weak': (0.15, 0.45)
        }
        
        self.link_ratio_ranges = {
            'well_verified': (0.7, 1.0),
            'partial': (0.4, 0.7),
            'poor': (0.05, 0.4)
        }
        
        # Label distribution
        self.trustworthy_count = total_samples // 2
        self.risky_count = total_samples // 2
        
        logger.info(f"Dataset Generator initialized")
        logger.info(f"Total samples: {total_samples} (Trustworthy: {self.trustworthy_count}, Risky: {self.risky_count})")
    
    def generate_dataset(self) -> pd.DataFrame:
        """
        Generate complete synthetic dataset
        
        Returns:
            DataFrame with all samples
        """
        logger.info("="*70)
        logger.info("Starting Dataset Generation")
        logger.info("="*70)
        
        all_samples = []
        
        # Generate trustworthy samples
        logger.info(f"\n📊 Generating {self.trustworthy_count} TRUSTWORTHY profiles...")
        trustworthy_samples = self._generate_trustworthy_samples(self.trustworthy_count)
        all_samples.extend(trustworthy_samples)
        
        # Generate risky samples
        logger.info(f"\n📊 Generating {self.risky_count} RISKY profiles...")
        risky_samples = self._generate_risky_samples(self.risky_count)
        all_samples.extend(risky_samples)
        
        # Create DataFrame
        df = pd.DataFrame(all_samples)
        
        # Shuffle the dataset
        df = df.sample(frac=1, random_state=self.seed).reset_index(drop=True)
        
        logger.info(f"\n✅ Generated {len(df)} total samples")
        
        # Validate dataset
        self._validate_dataset(df)
        
        return df
    
    def _generate_trustworthy_samples(self, count: int) -> List[Dict]:
        """Generate trustworthy profiles following Step 4.1 rules"""
        samples = []
        
        # Calculate distribution across personas
        persona_counts = self._calculate_persona_distribution(count)
        
        for persona_name, persona_count in persona_counts.items():
            if persona_name == 'Edge':
                continue  # Handle edge cases separately
            
            persona = self.personas[persona_name]
            
            for _ in range(persona_count):
                # Generate base features
                num_projects = np.random.randint(persona.projects_range[0], persona.projects_range[1] + 1)
                total_years = np.random.uniform(persona.years_range[0], persona.years_range[1])
                
                # Ensure consistency: avg_duration * num_projects ≈ total_years * 12
                target_total_months = total_years * 12
                avg_duration = target_total_months / num_projects if num_projects > 0 else persona.duration_range[0]
                
                # Clip to realistic range
                avg_duration = np.clip(avg_duration, persona.duration_range[0], persona.duration_range[1])
                
                # Global cap at 24 months maximum
                avg_duration = min(avg_duration, 24.0)
                
                # Add small variation
                avg_duration += np.random.normal(0, 0.5)
                avg_duration = max(1.0, avg_duration)
                
                # Trustworthy conditions (Step 4.1)
                overlap_count = np.random.randint(0, 2)  # 0-1 for trustworthy
                tech_consistency = np.random.uniform(0.6, 1.0)  # >= 0.6
                project_link_ratio = np.random.uniform(0.6, 1.0)  # >= 0.6
                
                # Generate synthetic BERT embedding
                embedding = self._generate_trustworthy_embedding()
                
                sample = {
                    'embedding': embedding,
                    'num_projects': num_projects,
                    'total_years': round(total_years, 2),
                    'avg_project_duration': round(avg_duration, 2),
                    'overlap_count': overlap_count,
                    'tech_consistency': round(tech_consistency, 3),
                    'project_link_ratio': round(project_link_ratio, 3),
                    'experience_level': persona_name,
                    'label': 1
                }
                
                samples.append(sample)
        
        return samples
    
    def _generate_risky_samples(self, count: int) -> List[Dict]:
        """Generate risky profiles following Step 4.2 rules"""
        samples = []
        
        # Add edge cases (Step 7) - 10% of total
        edge_cases_count = int(count * 0.10)
        
        # Calculate distribution across personas (excluding edge cases)
        remaining_count = count - edge_cases_count
        persona_counts = self._calculate_persona_distribution(remaining_count)
        
        for persona_name, persona_count in persona_counts.items():
            if persona_name == 'Edge':
                continue
            
            persona = self.personas[persona_name]
            
            for _ in range(persona_count):
                # Choose which risky pattern to apply
                risky_pattern = np.random.choice([
                    'too_many_projects',
                    'high_overlap',
                    'low_consistency',
                    'low_verification'
                ])
                
                if risky_pattern == 'too_many_projects':
                    # Too many projects for experience (capped at 50 max)
                    total_years = np.random.uniform(persona.years_range[0], persona.years_range[0] + 1)
                    num_projects = np.random.randint(
                        persona.projects_range[1] - 5,
                        min(persona.projects_range[1] + 10, 50)
                    )
                    avg_duration = np.random.uniform(0.5, 2.0)  # Very short
                    overlap_count = np.random.randint(3, 8)
                    tech_consistency = np.random.uniform(0.3, 0.6)
                    project_link_ratio = np.random.uniform(0.1, 0.4)
                
                elif risky_pattern == 'high_overlap':
                    # Normal projects but high overlap
                    num_projects = np.random.randint(persona.projects_range[0], persona.projects_range[1])
                    total_years = np.random.uniform(persona.years_range[0], persona.years_range[1])
                    avg_duration = np.random.uniform(persona.duration_range[0], persona.duration_range[1])
                    overlap_count = np.random.randint(3, 10)  # >= 3 for risky
                    tech_consistency = np.random.uniform(0.3, 0.7)
                    project_link_ratio = np.random.uniform(0.2, 0.5)
                
                elif risky_pattern == 'low_consistency':
                    # Scattered technologies
                    num_projects = np.random.randint(persona.projects_range[0], persona.projects_range[1])
                    total_years = np.random.uniform(persona.years_range[0], persona.years_range[1])
                    avg_duration = np.random.uniform(persona.duration_range[0], persona.duration_range[1])
                    overlap_count = np.random.randint(0, 4)
                    tech_consistency = np.random.uniform(0.1, 0.45)  # < 0.45 for risky
                    project_link_ratio = np.random.uniform(0.2, 0.6)
                
                else:  # low_verification
                    # Poor verification
                    num_projects = np.random.randint(persona.projects_range[0], persona.projects_range[1])
                    total_years = np.random.uniform(persona.years_range[0], persona.years_range[1])
                    avg_duration = np.random.uniform(persona.duration_range[0], persona.duration_range[1])
                    overlap_count = np.random.randint(1, 5)
                    tech_consistency = np.random.uniform(0.4, 0.7)
                    project_link_ratio = np.random.uniform(0.0, 0.4)  # < 0.4 for risky
                
                # Generate synthetic BERT embedding (with more noise)
                embedding = self._generate_risky_embedding()
                
                sample = {
                    'embedding': embedding,
                    'num_projects': num_projects,
                    'total_years': round(total_years, 2),
                    'avg_project_duration': round(avg_duration, 2),
                    'overlap_count': overlap_count,
                    'tech_consistency': round(tech_consistency, 3),
                    'project_link_ratio': round(project_link_ratio, 3),
                    'experience_level': persona_name,
                    'label': 0
                }
                
                samples.append(sample)
        
        # Add explicit edge cases (Step 7)
        edge_samples = self._generate_edge_cases(edge_cases_count)
        samples.extend(edge_samples)
        
        return samples
    
    def _generate_edge_cases(self, count: int) -> List[Dict]:
        """Generate explicit edge cases for robustness"""
        edge_samples = []
        
        edge_types = ['high_projects_low_years', 'perfect_language_fake_claims', 
                     'low_projects_high_experience', 'conflicting_indicators']
        
        samples_per_type = count // len(edge_types)
        
        for edge_type in edge_types:
            for _ in range(samples_per_type):
                if edge_type == 'high_projects_low_years':
                    # Very high projects + low years (RISKY) - capped at 50 max
                    num_projects = np.random.randint(40, 51)  # Up to 50
                    total_years = np.random.uniform(0.5, 2.0)
                    avg_duration = np.random.uniform(0.3, 1.5)
                    overlap_count = np.random.randint(10, 20)
                    tech_consistency = np.random.uniform(0.2, 0.5)
                    project_link_ratio = np.random.uniform(0.0, 0.2)
                    label = 0
                
                elif edge_type == 'perfect_language_fake_claims':
                    # Good consistency but unrealistic numbers (RISKY)
                    num_projects = np.random.randint(30, 50)
                    total_years = np.random.uniform(1.0, 3.0)
                    avg_duration = np.random.uniform(0.5, 2.0)
                    overlap_count = np.random.randint(5, 15)
                    tech_consistency = np.random.uniform(0.8, 1.0)  # HIGH but fake
                    project_link_ratio = np.random.uniform(0.0, 0.3)
                    label = 0
                
                elif edge_type == 'low_projects_high_experience':
                    # Few projects but long experience (could be trustworthy)
                    num_projects = np.random.randint(2, 5)
                    total_years = np.random.uniform(8.0, 15.0)
                    avg_duration = np.random.uniform(20.0, 24.0)  # Capped at 24 months
                    overlap_count = np.random.randint(0, 1)
                    tech_consistency = np.random.uniform(0.7, 1.0)
                    project_link_ratio = np.random.uniform(0.6, 1.0)
                    label = 1
                
                else:  # conflicting_indicators
                    # Mixed signals (RISKY)
                    num_projects = np.random.randint(10, 25)
                    total_years = np.random.uniform(3.0, 7.0)
                    avg_duration = np.random.uniform(2.0, 8.0)
                    overlap_count = np.random.randint(2, 6)
                    tech_consistency = np.random.uniform(0.3, 0.7)
                    project_link_ratio = np.random.uniform(0.2, 0.6)
                    label = 0
                
                experience_level = np.random.choice(['Entry', 'Mid', 'Senior', 'Expert'])
                embedding = self._generate_risky_embedding() if label == 0 else self._generate_trustworthy_embedding()
                
                sample = {
                    'embedding': embedding,
                    'num_projects': num_projects,
                    'total_years': round(total_years, 2),
                    'avg_project_duration': round(avg_duration, 2),
                    'overlap_count': overlap_count,
                    'tech_consistency': round(tech_consistency, 3),
                    'project_link_ratio': round(project_link_ratio, 3),
                    'experience_level': experience_level,
                    'label': label
                }
                
                edge_samples.append(sample)
        
        return edge_samples
    
    def _generate_trustworthy_embedding(self) -> np.ndarray:
        """
        Generate synthetic BERT embedding for trustworthy profile
        Step 5: Lower noise, higher coherence
        """
        # Base embedding from normal distribution
        embedding = np.random.randn(768).astype(np.float32)
        
        # Normalize to unit length (common in BERT embeddings)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        # Add structured pattern (simulates semantic coherence)
        pattern = np.sin(np.linspace(0, 4 * np.pi, 768)).astype(np.float32) * 0.1
        embedding = embedding * 0.9 + pattern * 0.1
        
        # Normalize again
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding
    
    def _generate_risky_embedding(self) -> np.ndarray:
        """
        Generate synthetic BERT embedding for risky profile
        Step 5: Higher noise, lower coherence
        """
        # Base embedding with more noise
        embedding = np.random.randn(768).astype(np.float32)
        
        # Add random noise
        noise = np.random.uniform(-0.3, 0.3, 768).astype(np.float32)
        embedding = embedding + noise
        
        # Normalize
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding
    
    def _calculate_persona_distribution(self, total: int) -> Dict[str, int]:
        """Calculate how many samples per persona"""
        distribution = {}
        
        for name, persona in self.personas.items():
            if name == 'Edge':
                continue
            count = int(total * persona.percentage)
            distribution[name] = count
        
        # Adjust for rounding
        current_total = sum(distribution.values())
        if current_total < total:
            distribution['Mid'] += (total - current_total)
        
        return distribution
    
    def _validate_dataset(self, df: pd.DataFrame):
        """
        Validate dataset (Step 8)
        """
        logger.info("\n" + "="*70)
        logger.info("🔍 VALIDATING DATASET")
        logger.info("="*70)
        
        # 8.1 Consistency checks
        logger.info("\n1️⃣ Consistency Checks:")
        
        # No negative values
        numeric_cols = ['num_projects', 'total_years', 'avg_project_duration', 
                       'overlap_count', 'tech_consistency', 'project_link_ratio']
        
        for col in numeric_cols:
            if (df[col] < 0).any():
                logger.error(f"❌ Found negative values in {col}")
            else:
                logger.info(f"   ✅ {col}: No negative values")
        
        # Check impossible combinations
        impossible = df[df['num_projects'] == 0]
        if len(impossible) > 0:
            logger.warning(f"⚠️  Found {len(impossible)} samples with 0 projects")
        else:
            logger.info("   ✅ No impossible combinations")
        
        # 8.2 Distribution checks
        logger.info("\n2️⃣ Distribution Checks:")
        
        logger.info(f"\n   Label Distribution:")
        logger.info(f"   - Trustworthy (1): {(df['label'] == 1).sum()}")
        logger.info(f"   - Risky (0): {(df['label'] == 0).sum()}")
        
        logger.info(f"\n   Experience Level Distribution:")
        for level in df['experience_level'].unique():
            count = (df['experience_level'] == level).sum()
            pct = count / len(df) * 100
            logger.info(f"   - {level}: {count} ({pct:.1f}%)")
        
        # Feature statistics
        logger.info(f"\n   Feature Statistics:")
        for col in numeric_cols:
            logger.info(f"   - {col}:")
            logger.info(f"     Min: {df[col].min():.3f}, Max: {df[col].max():.3f}, Mean: {df[col].mean():.3f}")
        
        # Check embedding dimensions
        first_embedding = df['embedding'].iloc[0]
        logger.info(f"\n   Embedding Dimension: {len(first_embedding)}")
        
        if len(first_embedding) != 768:
            logger.error(f"❌ Embedding dimension should be 768, got {len(first_embedding)}")
        else:
            logger.info("   ✅ Embeddings have correct dimension (768)")
        
        logger.info("\n" + "="*70)
        logger.info("✅ VALIDATION COMPLETE")
        logger.info("="*70)
    
    def save_dataset(self, df: pd.DataFrame, output_dir: Path):
        """
        Save dataset in multiple formats (Step 9)
        
        Args:
            df: Dataset DataFrame
            output_dir: Directory to save files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info("\n" + "="*70)
        logger.info("💾 SAVING DATASET")
        logger.info("="*70)
        
        # 1. Save embeddings separately as NumPy array
        embeddings = np.stack(df['embedding'].values)
        embeddings_path = output_dir / f"lstm_embeddings_{timestamp}.npy"
        np.save(embeddings_path, embeddings)
        logger.info(f"\n✅ Saved embeddings: {embeddings_path}")
        logger.info(f"   Shape: {embeddings.shape}")
        
        # 2. Save features as NumPy array
        feature_cols = ['num_projects', 'total_years', 'avg_project_duration',
                       'overlap_count', 'tech_consistency', 'project_link_ratio']
        features = df[feature_cols].values.astype(np.float32)
        features_path = output_dir / f"lstm_features_{timestamp}.npy"
        np.save(features_path, features)
        logger.info(f"\n✅ Saved features: {features_path}")
        logger.info(f"   Shape: {features.shape}")
        
        # 3. Save labels
        labels = df['label'].values.astype(np.int32)
        labels_path = output_dir / f"lstm_labels_{timestamp}.npy"
        np.save(labels_path, labels)
        logger.info(f"\n✅ Saved labels: {labels_path}")
        logger.info(f"   Shape: {labels.shape}")
        
        # 4. Save metadata (experience levels)
        metadata_df = df[['experience_level', 'label']].copy()
        metadata_path = output_dir / f"lstm_metadata_{timestamp}.csv"
        metadata_df.to_csv(metadata_path, index=False)
        logger.info(f"\n✅ Saved metadata: {metadata_path}")
        
        # 5. Save full dataset as CSV (for inspection)
        # Convert embeddings to string for CSV
        df_csv = df.copy()
        df_csv['embedding_shape'] = df_csv['embedding'].apply(lambda x: f"[{len(x)}]")
        df_csv = df_csv.drop('embedding', axis=1)
        csv_path = output_dir / f"lstm_dataset_{timestamp}.csv"
        df_csv.to_csv(csv_path, index=False)
        logger.info(f"\n✅ Saved CSV (for inspection): {csv_path}")
        
        # 6. Save dataset info
        info = {
            'timestamp': timestamp,
            'total_samples': len(df),
            'trustworthy_samples': (df['label'] == 1).sum(),
            'risky_samples': (df['label'] == 0).sum(),
            'embedding_dim': 768,
            'feature_dim': 6,
            'experience_levels': df['experience_level'].unique().tolist(),
            'files': {
                'embeddings': str(embeddings_path.name),
                'features': str(features_path.name),
                'labels': str(labels_path.name),
                'metadata': str(metadata_path.name),
                'csv': str(csv_path.name)
            }
        }
        
        info_path = output_dir / f"lstm_dataset_info_{timestamp}.txt"
        with open(info_path, 'w') as f:
            for key, value in info.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"\n✅ Saved dataset info: {info_path}")
        
        logger.info("\n" + "="*70)
        logger.info("✨ DATASET SAVED SUCCESSFULLY")
        logger.info("="*70)
        
        return {
            'embeddings': embeddings_path,
            'features': features_path,
            'labels': labels_path,
            'metadata': metadata_path,
            'csv': csv_path,
            'info': info_path
        }


def generate_lstm_training_dataset(
    total_samples: int = 6000,
    output_dir: str = "./data/processed",
    seed: int = 42
) -> Dict:
    """
    Main function to generate complete LSTM training dataset
    
    Args:
        total_samples: Number of samples to generate (default: 6000)
        output_dir: Output directory path
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with paths to saved files
    """
    logger.info("\n" + "="*70)
    logger.info("🚀 LSTM TRAINING DATASET GENERATION")
    logger.info("="*70)
    logger.info(f"\nConfiguration:")
    logger.info(f"  Total Samples: {total_samples}")
    logger.info(f"  Output Directory: {output_dir}")
    logger.info(f"  Random Seed: {seed}")
    
    # Initialize generator
    generator = SyntheticDatasetGenerator(total_samples=total_samples, seed=seed)
    
    # Generate dataset
    df = generator.generate_dataset()
    
    # Save dataset
    output_path = Path(output_dir)
    file_paths = generator.save_dataset(df, output_path)
    
    logger.info("\n" + "="*70)
    logger.info("🎉 DATASET GENERATION COMPLETE!")
    logger.info("="*70)
    logger.info(f"\nDataset ready for LSTM training:")
    logger.info(f"  Location: {output_path}")
    logger.info(f"  Total samples: {len(df)}")
    logger.info(f"  Files created: {len(file_paths)}")
    
    return file_paths


if __name__ == "__main__":
    # Generate dataset
    file_paths = generate_lstm_training_dataset(
        total_samples=6000,
        output_dir="./data/processed",
        seed=42
    )
    
    print("\n" + "="*70)
    print("✅ Dataset generation completed successfully!")
    print("="*70)
