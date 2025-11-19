# Trained Model Location

## Model Storage

Trained models are saved in the **`models/`** directory within the project folder.

**Location**: `/Users/nk/Documents/Student Data/DoD SAFE-tWObA2Vtnk8vL9AT/models/`

## Saved Files

For each trained sensor model, three files are saved:

1. **`{sensor}_{column}_model.pkl`** - The trained machine learning model
2. **`{sensor}_{column}_scaler.pkl`** - Feature scaler (StandardScaler)
3. **`{sensor}_{column}_bounds.pkl`** - Prediction bounds and statistics

### Current Models

- `cmd_vel_linear_x_*` - Velocity command predictions
- `odometry_twist_twist_linear_x_*` - Odometry velocity predictions
- `imu_linear_acceleration_x_*` - IMU acceleration predictions
- `joint_states_velocity_0_*` - Joint state velocity predictions
- `metadata.pkl` - Model metadata (window size, confidence level, etc.)

## File Sizes

- **Model files**: ~240KB - 4.3MB each (depending on model complexity)
- **Scaler files**: ~1KB each
- **Bounds files**: ~250 bytes each
- **Metadata**: ~1KB

**Total size**: ~7-10MB for all models

## How It Works

### First Run
1. Models are trained on historical data
2. Models are automatically saved to `models/` directory
3. You'll see: "Saving models to models/..."

### Subsequent Runs
1. System checks for existing models in `models/` directory
2. If found, loads them automatically
3. You'll see: "✓ Loaded X models from models/"
4. **No retraining needed** - saves time!

### Retraining

To retrain models (e.g., with new data):
1. Delete the `models/` directory: `rm -rf models/`
2. Run the program again - it will train new models

Or modify the code to force retraining:
```python
predictive = PredictiveDetector(model_dir='models')
# Delete old models first, or use a different directory
predictive.train_model(data)  # Forces retraining
```

## Model Persistence Benefits

✅ **Faster startup**: No need to retrain every time  
✅ **Consistent predictions**: Same models used across runs  
✅ **Easy sharing**: Models can be copied to other systems  
✅ **Version control**: Can track model versions  
✅ **Backup**: Models can be backed up separately  

## Loading Models Manually

```python
from predictive_model import PredictiveDetector
import joblib

# Load a specific model
model = joblib.load('models/cmd_vel_linear_x_model.pkl')
scaler = joblib.load('models/cmd_vel_linear_x_scaler.pkl')
bounds = joblib.load('models/cmd_vel_linear_x_bounds.pkl')

# Or use the class method
predictive = PredictiveDetector(model_dir='models')
if predictive.load_models():
    print("Models loaded successfully!")
```

## Model Directory Structure

```
models/
├── cmd_vel_linear_x_model.pkl
├── cmd_vel_linear_x_scaler.pkl
├── cmd_vel_linear_x_bounds.pkl
├── odometry_twist_twist_linear_x_model.pkl
├── odometry_twist_twist_linear_x_scaler.pkl
├── odometry_twist_twist_linear_x_bounds.pkl
├── imu_linear_acceleration_x_model.pkl
├── imu_linear_acceleration_x_scaler.pkl
├── imu_linear_acceleration_x_bounds.pkl
├── joint_states_velocity_0_model.pkl
├── joint_states_velocity_0_scaler.pkl
├── joint_states_velocity_0_bounds.pkl
└── metadata.pkl
```

## Notes

- Models are saved using `joblib` (standard for scikit-learn)
- Models are compatible across Python versions (with same scikit-learn version)
- Models can be loaded on different machines
- File format: Pickle (`.pkl`)

## Troubleshooting

**Models not loading?**
- Check that `models/` directory exists
- Verify `metadata.pkl` exists
- Check file permissions

**Want to use different models?**
- Change `model_dir` parameter: `PredictiveDetector(model_dir='my_models')`
- Or delete `models/` directory to retrain

**Models too large?**
- Consider using smaller models (fewer trees in Random Forest)
- Or use Gradient Boosting (smaller but slower)

