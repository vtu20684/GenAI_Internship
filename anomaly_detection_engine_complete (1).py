"""
Anomaly Detection Engine - Complete Implementation
Detects salary manipulation and fake overtime using unsupervised learning
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from scipy import stats
from scipy.spatial.distance import jensenshannon
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import logging
from datetime import datetime, timedelta
from collections import deque
import json
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from queue import Queue

# ============================================================================
# DATA PREPROCESSING
# ============================================================================

class HRPayrollPreprocessor:
    """Preprocesses HR and payroll data for anomaly detection"""
    
    def __init__(self):
        self.scaler = RobustScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.feature_columns = []
        self.is_fitted = False
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean raw HR & payroll data"""
        df = df.drop_duplicates()
        
        # Remove negative values for salary/hours
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'salary' in col.lower() or 'pay' in col.lower() or 'hours' in col.lower():
                df = df[df[col] >= 0]
        
        # Remove extreme outliers
        for col in numeric_cols:
            if col not in ['employee_id', 'department_id']:
                mean_val = df[col].mean()
                std_val = df[col].std()
                df = df[np.abs(df[col] - mean_val) <= 5 * std_val]
        
        return df
    
    def create_salary_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create salary-related features"""
        # Salary change ratios
        if 'current_salary' in df.columns and 'previous_salary' in df.columns:
            df['salary_change_ratio'] = df['current_salary'] / df['previous_salary'].replace(0, 1)
            df['salary_change_amount'] = df['current_salary'] - df['previous_salary']
        
        # Salary vs department average
        if 'department_id' in df.columns and 'salary' in df.columns:
            dept_avg_salary = df.groupby('department_id')['salary'].transform('mean')
            df['salary_vs_dept_avg'] = df['salary'] / dept_avg_salary
        
        # Salary vs role average
        if 'job_title' in df.columns and 'salary' in df.columns:
            role_avg_salary = df.groupby('job_title')['salary'].transform('mean')
            df['salary_vs_role_avg'] = df['salary'] / role_avg_salary
        
        return df
    
    def create_overtime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create overtime-related features"""
        # Overtime ratios
        if 'overtime_hours' in df.columns and 'regular_hours' in df.columns:
            df['overtime_ratio'] = df['overtime_hours'] / df['regular_hours'].replace(0, 1)
            df['total_hours'] = df['regular_hours'] + df['overtime_hours']
        
        # Overtime frequency patterns
        if 'overtime_hours' in df.columns and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['is_weekend'] = df['date'].dt.dayofweek >= 5
            df['weekend_overtime'] = df['overtime_hours'] * df['is_weekend']
            
            # Rolling overtime patterns
            df = df.sort_values(['employee_id', 'date'])
            df['overtime_7day_avg'] = df.groupby('employee_id')['overtime_hours'].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
        
        # Suspicious overtime patterns
        if 'overtime_hours' in df.columns:
            df['consistent_high_overtime'] = (
                df.groupby('employee_id')['overtime_hours'].transform(
                    lambda x: (x > x.quantile(0.8)).rolling(window=4).sum()
                ) >= 3
            )
            df['is_round_overtime'] = (df['overtime_hours'] % 1 == 0) & (df['overtime_hours'] > 0)
        
        return df
    
    def normalize_features(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """Normalize and scale features"""
        numeric_features = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
        
        if not self.is_fitted:
            X_imputed = self.imputer.fit_transform(df[numeric_features])
            X_scaled = self.scaler.fit_transform(X_imputed)
            self.feature_columns = numeric_features
            self.is_fitted = True
        else:
            X_imputed = self.imputer.transform(df[numeric_features])
            X_scaled = self.scaler.transform(X_imputed)
        
        return X_scaled
    
    def preprocess(self, df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """Complete preprocessing pipeline"""
        df_clean = self.clean_data(df)
        df_features = self.create_salary_features(df_clean)
        df_features = self.create_overtime_features(df_features)
        
        feature_cols = [
            col for col in df_features.columns 
            if col not in ['employee_id', 'department_id', 'date', 'hire_date', 'job_title']
            and df_features[col].dtype in ['int64', 'float64']
        ]
        
        X_processed = self.normalize_features(df_features, feature_cols)
        return X_processed, df_features

# ============================================================================
# ANOMALY DETECTION MODELS
# ============================================================================

class IsolationForestAnomalyDetector:
    """Isolation Forest model for real-time anomaly detection"""
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = None
        self.feature_names = []
        self.threshold = None
        self.is_fitted = False
        
    def fit(self, X: np.ndarray, feature_names: Optional[list] = None) -> Dict:
        """Train the Isolation Forest model"""
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.model.fit(X)
        scores = self.model.decision_function(X)
        self.threshold = np.percentile(scores, self.contamination * 100)
        
        if feature_names:
            self.feature_names = feature_names
        
        self.is_fitted = True
        
        predictions = self.model.predict(X)
        anomaly_rate = np.mean(predictions == -1)
        
        normal_mask = predictions == 1
        if np.sum(normal_mask) > 1:
            silhouette_avg = silhouette_score(X[normal_mask], predictions[normal_mask])
        else:
            silhouette_avg = 0
        
        return {
            'anomaly_rate': anomaly_rate,
            'threshold': self.threshold,
            'silhouette_score': silhouette_avg,
            'n_samples': X.shape[0],
            'n_features': X.shape[1]
        }
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies and return scores"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        predictions = self.model.predict(X)
        scores = self.model.decision_function(X)
        binary_predictions = (predictions == -1).astype(int)
        
        return binary_predictions, scores
    
    def predict_single(self, x: np.ndarray) -> Tuple[int, float]:
        """Predict for a single sample"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        x_reshaped = x.reshape(1, -1)
        prediction = self.model.predict(x_reshaped)[0]
        score = self.model.decision_function(x_reshaped)[0]
        is_anomaly = 1 if prediction == -1 else 0
        
        return is_anomaly, score

class AnomalyAutoencoder(nn.Module):
    """Neural network autoencoder for anomaly detection"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int] = [64, 32, 16], dropout_rate: float = 0.2):
        super(AnomalyAutoencoder, self).__init__()
        
        # Encoder
        encoder_layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        self.encoder = nn.Sequential(*encoder_layers)
        
        # Decoder
        decoder_layers = []
        reversed_dims = hidden_dims[::-1][1:] + [input_dim]
        prev_dim = hidden_dims[-1]
        
        for hidden_dim in reversed_dims:
            decoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        decoder_layers[-1] = nn.Linear(prev_dim, input_dim)
        self.decoder = nn.Sequential(*decoder_layers)
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class AutoencoderAnomalyDetector:
    """Autoencoder-based anomaly detector for batch processing"""
    
    def __init__(self, hidden_dims: List[int] = [64, 32, 16], learning_rate: float = 0.001, 
                 batch_size: int = 32, epochs: int = 100, device: str = 'cpu'):
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        self.feature_names = []
        self.is_fitted = False
        
        self.training_losses = []
        self.validation_losses = []
    
    def fit(self, X: np.ndarray, feature_names: Optional[List[str]] = None, 
            validation_split: float = 0.2) -> Dict:
        """Train the autoencoder"""
        X_scaled = self.scaler.fit_transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        # Split data
        n_samples = X_tensor.shape[0]
        n_val = int(n_samples * validation_split)
        n_train = n_samples - n_val
        
        X_train = X_tensor[:n_train]
        X_val = X_tensor[n_train:]
        
        # Initialize model
        input_dim = X.shape[1]
        self.model = AnomalyAutoencoder(input_dim, self.hidden_dims).to(self.device)
        
        # Setup training
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        for epoch in range(self.epochs):
            self.model.train()
            train_loss = 0.0
            
            # Simple batch training
            for i in range(0, len(X_train), self.batch_size):
                batch_x = X_train[i:i+self.batch_size]
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_x)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            avg_train_loss = train_loss / (len(X_train) / self.batch_size)
            self.training_losses.append(avg_train_loss)
        
        # Calculate reconstruction errors
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1)
            self.threshold = np.percentile(reconstruction_errors.cpu().numpy(), 95)
        
        self.is_fitted = True
        
        if feature_names:
            self.feature_names = feature_names
        
        return {
            'final_train_loss': self.training_losses[-1],
            'threshold': self.threshold,
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'epochs_trained': self.epochs
        }
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies and return reconstruction errors"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1)
        
        errors = reconstruction_errors.cpu().numpy()
        predictions = (errors > self.threshold).astype(int)
        
        return predictions, errors

# ============================================================================
# CONCEPT DRIFT DETECTION
# ============================================================================

class ConceptDriftDetector:
    """Detects and handles concept drift in anomaly detection models"""
    
    def __init__(self, window_size: int = 1000, drift_threshold: float = 0.05):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.reference_window = deque(maxlen=window_size)
        self.current_window = deque(maxlen=window_size)
        self.drift_history = []
        self.feature_names = []
        self.is_initialized = False
    
    def initialize_reference(self, X: np.ndarray, feature_names: Optional[List[str]] = None):
        """Initialize reference window with initial data"""
        self.feature_names = feature_names or [f'feature_{i}' for i in range(X.shape[1])]
        
        for sample in X:
            self.reference_window.append(sample)
        
        self.is_initialized = True
    
    def update(self, X: np.ndarray) -> Dict:
        """Update detector with new data and check for drift"""
        if not self.is_initialized:
            raise ValueError("Detector must be initialized with reference data")
        
        for sample in X:
            self.current_window.append(sample)
        
        if len(self.current_window) >= self.window_size // 2:
            drift_results = self._detect_drift()
            return drift_results
        
        return {'status': 'insufficient_data'}
    
    def _detect_drift(self) -> Dict:
        """Detect concept drift using statistical tests"""
        ref_data = np.array(self.reference_window)
        curr_data = np.array(self.current_window)
        
        drift_results = {
            'drift_detected': False,
            'test_results': {},
            'drift_magnitude': 0.0
        }
        
        total_drift_score = 0
        test_count = 0
        
        # Kolmogorov-Smirnov test
        ks_scores = []
        for i in range(min(ref_data.shape[1], curr_data.shape[1])):
            try:
                statistic, p_value = stats.ks_2samp(ref_data[:, i], curr_data[:, i])
                ks_scores.append(statistic)
            except:
                continue
        
        if ks_scores:
            drift_results['test_results']['ks'] = np.mean(ks_scores)
            total_drift_score += np.mean(ks_scores)
            test_count += 1
        
        # Calculate average drift magnitude
        if test_count > 0:
            drift_results['drift_magnitude'] = total_drift_score / test_count
        
        # Determine drift status
        if drift_results['drift_magnitude'] > self.drift_threshold:
            drift_results['drift_detected'] = True
            self.drift_history.append({
                'timestamp': datetime.now(),
                'magnitude': drift_results['drift_magnitude']
            })
        
        return drift_results

# ============================================================================
# MAIN APPLICATION
# ============================================================================

@dataclass
class AnomalyAlert:
    """Data structure for anomaly alerts"""
    employee_id: str
    timestamp: datetime
    anomaly_type: str
    anomaly_score: float
    confidence: float
    features: Dict[str, float]
    explanation: str
    severity: str

class AnomalyDetectionEngine:
    """Main anomaly detection engine"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.preprocessor = HRPayrollPreprocessor()
        self.isolation_forest = IsolationForestAnomalyDetector(
            contamination=self.config.get('contamination', 0.05),
            n_estimators=self.config.get('n_estimators', 100)
        )
        self.autoencoder = AutoencoderAnomalyDetector(
            hidden_dims=self.config.get('hidden_dims', [64, 32, 16]),
            epochs=self.config.get('epochs', 50)
        )
        self.drift_detector = ConceptDriftDetector(
            window_size=self.config.get('window_size', 1000),
            drift_threshold=self.config.get('drift_threshold', 0.05)
        )
        
        self.is_trained = False
        self.alerts = []
    
    def train(self, data: pd.DataFrame) -> Dict:
        """Train the anomaly detection models"""
        print("Training anomaly detection models...")
        
        # Preprocess data
        X_processed, df_features = self.preprocessor.preprocess(data)
        
        # Train Isolation Forest
        iso_results = self.isolation_forest.fit(X_processed, df_features.columns.tolist())
        
        # Train Autoencoder
        ae_results = self.autoencoder.fit(X_processed, df_features.columns.tolist())
        
        # Initialize drift detector
        self.drift_detector.initialize_reference(X_processed, df_features.columns.tolist())
        
        self.is_trained = True
        
        return {
            'isolation_forest': iso_results,
            'autoencoder': ae_results,
            'total_samples': len(data),
            'features': df_features.columns.tolist()
        }
    
    def detect_anomalies(self, data: pd.DataFrame) -> Dict:
        """Detect anomalies in new data"""
        if not self.is_trained:
            raise ValueError("Models must be trained before detection")
        
        # Preprocess data
        X_processed, df_features = self.preprocessor.preprocess(data)
        
        # Detect with both models
        iso_predictions, iso_scores = self.isolation_forest.predict(X_processed)
        ae_predictions, ae_scores = self.autoencoder.predict(X_processed)
        
        # Ensemble prediction (majority voting)
        ensemble_predictions = ((iso_predictions + ae_predictions) >= 1).astype(int)
        
        # Check for concept drift
        drift_results = self.drift_detector.update(X_processed)
        
        # Create alerts for anomalies
        alerts = []
        for i, (is_anomaly, score) in enumerate(zip(ensemble_predictions, iso_scores)):
            if is_anomaly:
                alert = self._create_alert(df_features.iloc[i], score)
                alerts.append(alert)
        
        self.alerts.extend(alerts)
        
        return {
            'predictions': ensemble_predictions,
            'scores': iso_scores,
            'anomalies_detected': len(alerts),
            'anomaly_rate': np.mean(ensemble_predictions),
            'drift_detected': drift_results.get('drift_detected', False),
            'alerts': [alert.__dict__ for alert in alerts]
        }
    
    def _create_alert(self, record: pd.Series, score: float) -> AnomalyAlert:
        """Create an anomaly alert"""
        # Determine anomaly type
        anomaly_type = self._classify_anomaly_type(record)
        
        # Calculate confidence
        confidence = min(abs(score) * 2, 1.0)
        
        # Determine severity
        if abs(score) > 0.4:
            severity = 'critical'
        elif abs(score) > 0.2:
            severity = 'high'
        elif abs(score) > 0.1:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Generate explanation
        explanation = self._generate_explanation(record, anomaly_type)
        
        # Extract features
        features = {
            col: record[col] 
            for col in record.index 
            if col not in ['employee_id', 'date', 'hire_date']
            and pd.notna(record[col])
        }
        
        return AnomalyAlert(
            employee_id=record.get('employee_id', 'unknown'),
            timestamp=datetime.now(),
            anomaly_type=anomaly_type,
            anomaly_score=score,
            confidence=confidence,
            features=features,
            explanation=explanation,
            severity=severity
        )
    
    def _classify_anomaly_type(self, record: pd.Series) -> str:
        """Classify the type of anomaly"""
        salary_indicators = ['salary_change_ratio', 'salary_vs_dept_avg', 'salary_vs_role_avg']
        overtime_indicators = ['overtime_ratio', 'weekend_overtime', 'consistent_high_overtime', 'is_round_overtime']
        
        salary_score = 0
        overtime_score = 0
        
        for indicator in salary_indicators:
            if indicator in record and pd.notna(record[indicator]):
                if 'ratio' in indicator:
                    salary_score += abs(record[indicator] - 1.0)
                else:
                    salary_score += abs(record[indicator])
        
        for indicator in overtime_indicators:
            if indicator in record and pd.notna(record[indicator]):
                if indicator == 'is_round_overtime':
                    overtime_score += record[indicator] * 2
                elif indicator == 'consistent_high_overtime':
                    overtime_score += record[indicator] * 1.5
                else:
                    overtime_score += abs(record[indicator])
        
        if salary_score > overtime_score:
            return 'salary_manipulation'
        elif overtime_score > 0:
            return 'fake_overtime'
        else:
            return 'general_anomaly'
    
    def _generate_explanation(self, record: pd.Series, anomaly_type: str) -> str:
        """Generate explanation for the anomaly"""
        explanations = []
        
        if anomaly_type == 'salary_manipulation':
            if 'salary_change_ratio' in record and pd.notna(record['salary_change_ratio']):
                ratio = record['salary_change_ratio']
                if abs(ratio - 1.0) > 0.2:
                    explanations.append(f"Unusual salary change ratio: {ratio:.2f}")
            
            if 'salary_vs_dept_avg' in record and pd.notna(record['salary_vs_dept_avg']):
                dept_ratio = record['salary_vs_dept_avg']
                if abs(dept_ratio - 1.0) > 0.5:
                    explanations.append(f"Salary deviates from department average: {dept_ratio:.2f}x")
        
        elif anomaly_type == 'fake_overtime':
            if 'overtime_ratio' in record and pd.notna(record['overtime_ratio']):
                ot_ratio = record['overtime_ratio']
                if ot_ratio > 0.5:
                    explanations.append(f"High overtime ratio: {ot_ratio:.2f}")
            
            if 'is_round_overtime' in record and pd.notna(record['is_round_overtime']):
                if record['is_round_overtime']:
                    explanations.append("Overtime hours are round numbers (potential fake entries)")
            
            if 'consistent_high_overtime' in record and pd.notna(record['consistent_high_overtime']):
                if record['consistent_high_overtime']:
                    explanations.append("Consistently high overtime over multiple periods")
        
        if not explanations:
            explanations.append("Unusual pattern detected in employee data")
        
        return "; ".join(explanations)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def create_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """Create sample HR & Payroll data for testing"""
    np.random.seed(42)
    
    data = {
        'employee_id': [f'EMP_{i:05d}' for i in range(n_samples)],
        'date': pd.date_range('2023-01-01', periods=n_samples, freq='H'),
        'salary': np.random.normal(50000, 15000, n_samples),
        'previous_salary': np.random.normal(48000, 14000, n_samples),
        'regular_hours': np.random.normal(40, 5, n_samples),
        'overtime_hours': np.random.exponential(5, n_samples),
        'department_id': np.random.randint(1, 11, n_samples),
        'job_title': np.random.choice(['Analyst', 'Manager', 'Developer', 'Admin'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Add some anomalies
    # Salary manipulation
    anomaly_indices = np.random.choice(n_samples, size=50, replace=False)
    df.loc[anomaly_indices[:25], 'salary'] *= np.random.uniform(1.3, 2.0, 25)  # 30-100% increase
    
    # Fake overtime
    df.loc[anomaly_indices[25:], 'overtime_hours'] = np.random.choice([8, 10, 12], 25)  # Round hours
    
    return df

def main():
    """Main function to demonstrate the anomaly detection engine"""
    print("=== Anomaly Detection Engine Demo ===")
    
    # Create sample data
    print("Creating sample data...")
    data = create_sample_data(1000)
    print(f"Created {len(data)} records")
    
    # Initialize engine
    engine = AnomalyDetectionEngine()
    
    # Train models
    print("\nTraining models...")
    training_results = engine.train(data)
    print(f"Training complete. Anomaly rate: {training_results['isolation_forest']['anomaly_rate']:.3f}")
    
    # Detect anomalies
    print("\nDetecting anomalies...")
    detection_results = engine.detect_anomalies(data)
    
    print(f"Anomalies detected: {detection_results['anomalies_detected']}")
    print(f"Anomaly rate: {detection_results['anomaly_rate']:.3f}")
    print(f"Concept drift detected: {detection_results['drift_detected']}")
    
    # Show sample alerts
    if detection_results['alerts']:
        print("\nSample Alerts:")
        for i, alert in enumerate(detection_results['alerts'][:3]):
            print(f"\nAlert {i+1}:")
            print(f"  Employee: {alert['employee_id']}")
            print(f"  Type: {alert['anomaly_type']}")
            print(f"  Severity: {alert['severity']}")
            print(f"  Explanation: {alert['explanation']}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
