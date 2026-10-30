#!/usr/bin/env python
"""
SCIENTIFIC FILE FORMAT ANALYSIS SCRIPT
Purpose: Inspect FITS and HDF5 files to extract structural metadata and scientific interpretation
Author: ECAS Research Analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.venv')))

# Try imports with fallback warnings
try:
    import astropy.io.fits as fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
    print("WARNING: astropy not available. Will skip FITS analysis.")

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False
    print("WARNING: h5py not available. Will skip HDF5 analysis.")

# Define file paths relative to ECAS_BETA root
ROOT_DIR = os.path.abspath('.')
FIT_S_FILE = f"{ROOT_DIR}/data/jupiter__9303301451N_evt.fits"
HDF5_FILE = f"{ROOT_DIR}/data/WASP-39b/W39_PRISM_data/FIREFLy_transit_spec.h5"

def analyze_fits_file(filepath):
    """Analyze a FITS file structure and metadata"""
    print(f"\n{'='*80}")
    print(f"FITS FILE ANALYSIS: {filepath}")
    print('='*80)
    
    if not ASTROPY_AVAILABLE or not os.path.exists(filepath):
        return None
    
    try:
        with fits.open(filepath, mode='readonly') as hdul:
            print(f"\n--- FITS File Header ---")
            print(f"Filename: {filepath}")
            print(f"Total HDUs: {len(hdul)}")
            print(f"Primary HDU: {hdul[0].name}")
            
            # Print each HDU's header keywords
            for i, hdul_item in enumerate(hdul):
                print(f"\n{'─'*60}")
                print(f"HDU [{i}]: {hdul_item.name}")
                print(f"{'─'*60}")
                
                header = hdul_item.header
                
                # Print key header keywords (WCS, units, etc.)
                for keyword in ['NAXIS', 'TELESCOP', 'INSTRUME', 'OBSERVE_DATE', 
                               'DATE-OBS', 'MJD-OBS', 'EXPTIME', 'DETECTOR',
                               'OBJECT', 'RADEC', 'DECPOS', 'CTYPE1', 'CTYPE2',
                               'CRPIX1', 'CRPIX2', 'CRVAL1', 'CRVAL2', 'CDELT1', 
                               'CDELT2', 'NAXIS1', 'NAXIS2', 'BUNIT', 'WCSNAME']:
                    if keyword in header:
                        print(f"  {keyword}: {header[keyword]}")
                
                # Check for datasets
                if hasattr(hdul_item, 'data'):
                    data = hdul_item.data
                    print(f"\n--- Dataset Info ---")
                    print(f"Data type: {type(data).__name__}")
                    try:
                        shape = data.shape
                        print(f"Shape (dimensions): {shape}")
                        
                        # Try to get dimensions
                        if len(shape) == 2:
                            print("Possible interpretation: [detector_rows, detector_cols]")
                        elif len(shape) >= 3:
                            print("Multidimensional spectrum - needs axis identification")
                    except:
                        pass
                    
            return True
    except Exception as e:
        print(f"Error reading FITS file: {e}")
        return False

def analyze_hdf5_file(filepath):
    """Analyze an HDF5 file structure and metadata"""
    print(f"\n{'='*80}")
    print(f"HDF5 FILE ANALYSIS: {filepath}")
    print('='*80)
    
    if not HDF5_AVAILABLE or not os.path.exists(filepath):
        return None
    
    try:
        with h5py.File(filepath, 'r') as f:
            # Print entire tree structure
            def print_tree(node, indent=0):
                prefix = "│   " * indent + "├── " if indent > 0 else "    "
                print(f"{prefix}{node.name.split('/')[-1]}")
                if node.attrs:
                    print(f"{' ' * (indent * 4 + 6)}Attributes:")
                    for key, value in node.attrs.items():
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except:
                                value = str(value)
                        print(f"{' ' * (indent * 4 + 10)}  {key}: {value}")
                else:
                    print(f"{' ' * (indent * 4 + 6)}Attributes: <none>")
                children = list(node.keys()) if isinstance(node, h5py.Group) else []
                for child in children:
                    child_item = node[child]
                    if isinstance(child_item, h5py.Dataset):
                        print(f"{' ' * (indent * 4 + 12)}[DATASET shape={child_item.shape}]")
                    elif isinstance(child_item, h5py.Group):
                        print_tree(child_item, indent + 1)
            
            print(f"\n--- HDF5 File Tree Structure ---")
            print("Root:")
            print_tree(f)
            
            return True
    except Exception as e:
        print(f"Error reading HDF5 file: {e}")
        return False

def main():
    """Main analysis runner"""
    print("\n" + "="*80)
    print("ECAS SCIENTIFIC FILE FORMAT ANALYSIS")
    print("="*80)
    print("\nThis script inspects structural metadata and scientific interpretation")
    print("of FITS and HDF5 files used in the ECAS exoplanetary spectroscopy suite.")
    
    results = {}
    
    # Analyze FITS file
    fits_result = analyze_fits_file(FIT_S_FILE)
    results['fits'] = fits_result
    
    # Analyze HDF5 file
    h5_result = analyze_hdf5_file(HDF5_FILE)
    results['hdf5'] = h5_result
    
    # Summary
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print('='*80)
    for fmt, result in results.items():
        status = "✓ ANALYZED" if result else "✗ SKIPPED/FAILED"
        print(f"{fmt.upper()}: {status}")
    
    return results

if __name__ == "__main__":
    main()