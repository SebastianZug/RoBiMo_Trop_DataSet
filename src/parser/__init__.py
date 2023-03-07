import json
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

FeatureDescriptions = dict()
with pkg_resources.open_text('parser', 'feature_descriptions.json') as stream:
    FeatureDescriptions = json.load(stream)

GroupDescriptions = dict()
with pkg_resources.open_text('parser', 'group_descriptions.json') as stream:
    GroupDescriptions = json.load(stream)

# Mapping for Beagle Systems F-Series according to Jerry (01/13/2021)
RCMapping = {
    'RCOU_C1': 'AILERON',
    'RCOU_C2': 'VTAIL LEFT',
    'RCOU_C3': 'CAM FOCUS',
    'RCOU_C4': 'VTAIL RIGHT',
    'RCOU_C5': 'MOTOR RIGHT',
    'RCOU_C6': 'MOTOR LEFT',
    'RCOU_C7': 'CAM ZOOM',
    'RCOU_C8': 'MOTOR REAR',
    'RCOU_C9': 'TILT SERVO LEFT',
    'RCOU_C10': 'TILT SERVO RIGHT',
    'RCOU_C11': 'CAM PAN',
    'RCOU_C12': 'CAM TILT',
    'RCOU_C13': 'BEC 5V RAIL',
    'RCOU_C14': 'CAM TRIGGER',
    'RCIN_C1': 'roll control',
    'RCIN_C2': 'pitch control',
    'RCIN_C3': 'Throttle',
    'RCIN_C4': 'Yaw control',
    'RCIN_C5': 'warning buzzer',
    'RCIN_C6': 'NA',
    'RCIN_C7': 'flight mode change',
    'RCIN_C8': 'motor emergency stop',
    'RCIN_C9': 'unknown',
    'RCIN_C10': 'unknown',
    'RCIN_C11': 'unknown',
    'RCIN_C12': 'unknown',
    'RCIN_C13': 'unknown',
    'RCIN_C14': 'unknown'
    }
